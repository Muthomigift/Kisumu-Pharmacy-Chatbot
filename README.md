# Kisumu Pharmacy Chatbot

A command-line chatbot that helps Kisumu Pharmacy staff answer the same caller questions in the same way, using the Google Gemini API.

## The problem

A small pharmacy in Kisumu gets calls all day asking about:

- opening hours
- whether a specific drug is in stock
- how long a prescription takes to process
- which documents are needed for a repeat prescription

Staff type the caller's question, and the chatbot gives a clear, consistent answer.

## What it does

- Answers from a fixed system prompt that holds the pharmacy's name, opening hours, services, prescription rules and stock policy.
- **Remembers the conversation.** If someone says "I have a prescription" and later asks "How long will it take?", the chatbot knows "it" means the prescription.
- Replies in English or Swahili, matching the person's language.
- Never gives a diagnosis, a dose, or advice on whether a medicine is safe. It refers those questions to the pharmacist.
- Tells the person to go to the nearest hospital or call 999 or 112 in an emergency.
- Does not save any conversation to disk.

## What is in the system prompt

| Part | Content |
|---|---|
| Name | Kisumu Pharmacy, Kisumu, Kenya |
| Opening hours | Monday to Saturday 8am to 8pm, Sunday 10am to 4pm |
| Services | Dispensing prescription medicines, repeat prescription refills, over-the-counter medicines, blood pressure checks, blood sugar testing, first aid supplies and wound care items |
| Prescriptions | Processing times and the documents needed for a repeat prescription |
| Stock | Staff must check specific medicines, and a short list of items usually stocked |
| Rules | No medical advice, emergency guidance, and "I do not know" when something is not covered |

The processing times, documents, services and stock list are sample details. Replace them in `SYSTEM_PROMPT` with the pharmacy's real ones before staff use the tool.

## How the memory works

The script keeps a list called `messages`. Each turn it:

1. Adds the user's question to the list.
2. Sends the whole list to the model, so the model sees everything said so far.
3. Adds the model's reply to the list.
4. Keeps only the last 20 messages (10 turns), which controls cost and length.

If a request fails, the user's last message is removed, so the list stays in order.

## Setup

1. Install Python 3.9 or newer.
2. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
3. Get a free API key from [Google AI Studio](https://aistudio.google.com).
4. Copy `.env.example` to `.env` and put your key in it:
   ```
   GEMINI_API_KEY=your-key-here
   ```
   Do not use quotes or spaces around `=`.

## Run it

Chat:
```
python pharmacy_chatbot.py
```
Type a question and press Enter. Type `exit` to quit.

Run the three-turn test:
```
python pharmacy_chatbot.py --test
```

## The three-turn test

The second and third questions only make sense because of the earlier turns.

| Turn | The user says | What a correct reply shows |
|---|---|---|
| 1 | I have a prescription for my daughter's antibiotics. | Acknowledges the prescription and offers help, for example with processing time or what to bring |
| 2 | How long will it take? | Understands "it" is the prescription and gives the processing time, about 15 to 20 minutes |
| 3 | And what documents do I need if it is a repeat prescription? | Gives the repeat prescription documents: the previous prescription or the empty medicine pack, and a valid ID |

Check that turn 2 does not ask "how long will what take?". That proves the chatbot remembers the conversation. The model's exact wording can differ between runs.

## Error handling

| Problem | What the script does |
|---|---|
| Model busy (503) | Retries 3 times (waits 2, 4, then 8 seconds), then tries the next model |
| Too many requests (429) | Tells you to wait and try again |
| Wrong or missing key (400, 401, 403) | Tells you to check your `.env` file |
| No internet | Tells you to check your connection |

## Changing the model

The `MODELS` list near the top of `pharmacy_chatbot.py` sets which models are used, in order. Model names change over time. If you see a "model not found" error, copy a current model name from Google AI Studio and update the list.

## Notes

- This tool answers common questions only. It is not medical advice, and the pharmacist decides anything about medicines, doses and safety.
- It cannot see real stock. It always asks staff to confirm whether a medicine is available.
- The free tier of the Gemini API has rate limits, and content sent on the free tier can be used to improve Google's products. Do not type patient names or other personal details.
- Never share your API key or upload your `.env` file.

## Files

- `pharmacy_chatbot.py`: the chatbot.
- `requirements.txt`: the libraries to install.
- `.env.example`: a template for your `.env` file.
- `.gitignore`: keeps `.env` out of Git.
- `README.md`: this file.