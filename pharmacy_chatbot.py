import os
import sys
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise SystemExit("No API key found. Add GEMINI_API_KEY=your-key to your .env file.")

client = genai.Client(api_key=api_key)

# If the first model is busy, the script tries the next one.
MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite"]

# Keep the last 20 messages (10 turns). The number must stay even.
MAX_MESSAGES = 20

# Sample details: replace them with the pharmacy's real ones.
SYSTEM_PROMPT = """You are the assistant for Kisumu Pharmacy in Kisumu, Kenya. Staff use you to give callers consistent answers.
Be brief, polite and clear. Reply in the language the person uses (English or Swahili).
Use the earlier messages in the conversation to understand what the person is referring to.

Opening hours:
- Monday to Saturday: 8am to 8pm
- Sunday: 10am to 4pm
- Public holiday hours are not known. Ask the person to call the pharmacy.
- You do not know the current day or time. If asked whether the pharmacy is open now, give the hours and ask the person to compare them with the current day and time.

Services:
1. Dispensing of prescription medicines
2. Repeat prescription refills
3. Over-the-counter medicines
4. Blood pressure checks
5. Blood sugar testing
6. First aid supplies and wound care items

Prescriptions:
- A new prescription usually takes about 15 to 20 minutes to prepare. It can take longer if a medicine must be ordered.
- A repeat prescription usually takes about 10 minutes.
- For a repeat prescription, bring the previous prescription or the empty medicine pack, and a valid ID.
- Prescription-only medicines are given only with a valid prescription.

Stock:
- Stock changes every day, so you cannot confirm that a specific medicine is in stock. Say that staff will check, and ask the person to call the pharmacy or visit.
- Medicines usually stocked: paracetamol, ibuprofen, oral rehydration salts, antacids and antihistamines.

Rules:
- Never give a diagnosis, a dose, or advice on whether a medicine is safe. Say that the pharmacist must answer that.
- In an emergency, tell the person to go to the nearest hospital or call 999 or 112.
- If something is not covered here, say you do not know and ask the person to call the pharmacy."""

TEST_TURNS = [
    "I have a prescription for my daughter's antibiotics.",
    "How long will it take?",
    "And what documents do I need if it is a repeat prescription?",
]

messages = []


def ask(history):
    # Tries each model up to 3 times when it is busy (error 503).
    for model in MODELS:
        for attempt in range(3):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=history,
                    config={"system_instruction": SYSTEM_PROMPT, "max_output_tokens": 1024},
                )
            except errors.APIError as error:
                if error.code != 503:
                    raise
                wait = 2 ** (attempt + 1)
                print(f"{model} is busy. Retrying in {wait} seconds...")
                time.sleep(wait)
    return None


def explain(error):
    if error.code == 429:
        return "Too many requests or daily limit reached. Wait a minute and try again."
    if error.code in (400, 401, 403):
        return "The request was rejected. Check your API key in the .env file."
    return f"The API returned an error: {error.code}"


def chat_turn(user_text):
    # Adds the question to the history, gets the reply, and remembers it.
    messages.append({"role": "user", "parts": [{"text": user_text}]})

    try:
        response = ask(messages)
    except httpx.RequestError:
        print("No internet connection. Check your connection and try again.\n")
        messages.pop()
        return None
    except errors.APIError as error:
        print(explain(error) + "\n")
        messages.pop()
        return None

    if response is None:
        print("The models are busy right now. Please try again in a few minutes.\n")
        messages.pop()
        return None

    reply = response.text or "Sorry, I could not answer that. Please try again."
    messages.append({"role": "model", "parts": [{"text": reply}]})
    del messages[:-MAX_MESSAGES]
    return reply


def run_test():
    print("Kisumu Pharmacy Assistant: three-turn test\n")
    for text in TEST_TURNS:
        print(f"You: {text}")
        reply = chat_turn(text)
        if reply is None:
            break
        print(f"\nAssistant: {reply}\n")


def run_chat():
    print("Kisumu Pharmacy Assistant. Type 'exit' to quit.\n")
    try:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                break
            if not user_input:
                continue
            reply = chat_turn(user_input)
            if reply is not None:
                print(f"\nAssistant: {reply}\n")
    except (KeyboardInterrupt, EOFError):
        print()


if "--test" in sys.argv:
    run_test()
else:
    run_chat()