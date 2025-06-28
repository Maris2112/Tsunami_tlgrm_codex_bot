# Tsunami WhatsApp Codex Bot

Flask webhook for WhatsApp that forwards messages to the OpenRouter API. The
assistant behavior is configured via `system_prompt.txt`.

## Setup

Install requirements:

```bash
pip install -r requirements.txt
```

Create a `.env` file or export these variables before starting the app:

```
GREENAPI_INSTANCE_ID
GREENAPI_TOKEN
GREENAPI_API_URL
GREENAPI_MEDIA_URL
OPENROUTER_API_KEY
SYSTEM_PROMPT_PATH  # optional path to custom prompt
```

## Running

Launch the server:

```bash
python main.py
```

It listens on port `5000` and provides `/webhook` for Green API callbacks.
