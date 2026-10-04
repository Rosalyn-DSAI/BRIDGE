# Configure Gemini for BRIDGE

Use this guide after completing the Windows or macOS/Linux setup.

BRIDGE supports `demo`, `gemini`, and `openai` AI modes. Only the selected provider is called.

## 1. Add your Gemini settings

Open `.env` and set:

```dotenv
AI_MODE=gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=YOUR_WORKING_GEMINI_MODEL
```

Use the exact model name available to your Gemini account.

Do not put your API key in JavaScript, screenshots, documentation, GitHub, or messages you share publicly.

## 2. Test the connection

From the BRIDGE folder, run:

```bash
python scripts/check_ai.py
```

If you are not using an activated virtual environment, use the command from your OS setup guide.

A successful check should identify Gemini as the selected mode and complete a short fictional request without printing your private key.

## 3. Start or restart BRIDGE

Restart both processes after changing `.env`:

```bash
python run.py
```

and, in a second terminal:

```bash
python worker.py
```

The interface should indicate that live AI processing is using Gemini.

## Common Gemini errors

| Error | What to check |
|---|---|
| 400 / invalid key | API key and key restrictions |
| 403 | Project permissions, restrictions, or regional availability |
| 404 | Model name and model access |
| 429 | Account/model quota; repeated retries do not fix a zero quota |
| Timeout | Internet connection or message length |
| Still using another provider | Duplicate `AI_MODE` settings or an old process that needs restarting |

## Privacy note

Live mode sends the pasted document to the selected AI provider after the user gives consent. Provider data-handling policies apply. Use fictional or non-confidential information unless you are authorized to send the content to that provider.

For OpenAI configuration, see [docs/LIVE_SERVICES.md](docs/LIVE_SERVICES.md).
