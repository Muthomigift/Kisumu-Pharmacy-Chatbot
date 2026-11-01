import json
import os
import time
from datetime import datetime

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

system_prompt = """You are an assistant for Otieno Wholesale in Kisumu.
Answer questions about stock, pricing, and delivery.
All prices in KES. Be helpful and brief.
Only use facts given here. If you do not know something, say so and ask the customer to contact the shop."""

messages = [] 
full_log = []  


def ask(history):
    # Tries each model up to 3 times when it is busy (error 503).
    for model in MODELS:
        for attempt in range(3):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=history,
                    config={"system_instruction": system_prompt, "max_output_tokens": 1024},
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


def save_log():
    if not full_log:
        print("No messages to save.")
        return
    log = {"date": datetime.now().isoformat(), "messages": full_log}
    with open("chat_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print("Conversation saved to chat_log.json")


print("Otieno Wholesale Assistanth.\n")

try:
    while True:
        user_input = input("Question: ").strip()
        if user_input.lower() == "exit":
            break
        if not user_input:
            continue

        messages.append({"role": "user", "parts": [{"text": user_input}]})

        try:
            response = ask(messages)
        except httpx.RequestError:
            print("No internet connection. Check your connection and try again.\n")
            messages.pop()
            continue
        except errors.APIError as error:
            print(explain(error) + "\n")
            messages.pop()
            continue

        if response is None:
            print("The models are busy right now. Please try again in a few minutes.\n")
            messages.pop()
            continue

        reply = response.text or "Sorry, I could not answer that. Please try again."

        # Add the reply to the history before the next turn
        messages.append({"role": "model", "parts": [{"text": reply}]})
        full_log.append({"role": "user", "text": user_input})
        full_log.append({"role": "model", "text": reply})

        # Keep only the last 10 messages (5 user + 5 model turns)
        if len(messages) > 10:
            messages = messages[-10:]

        print(f"\nAssistant: {reply}\n")
except (KeyboardInterrupt, EOFError):
    print()

save_log()