# BRIDGE quick start

This page is the shortest path to running BRIDGE locally.

## 1. Choose your setup guide

- **Windows:** [WINDOWS_SETUP.md](WINDOWS_SETUP.md)
- **macOS / Linux:** [MAC_LINUX_SETUP.md](MAC_LINUX_SETUP.md)

Those guides create the virtual environment, install dependencies, and create `.env` from `.env.example`.

## 2. Choose how BRIDGE should run

For a completely local review with no external AI request and no real email:

```dotenv
AI_MODE=demo
MAIL_MODE=local
```

For the live hackathon setup using Gemini and Gmail:

```dotenv
AI_MODE=gemini
MAIL_MODE=gmail
```

Then complete:

- [GEMINI_SETUP.md](GEMINI_SETUP.md)
- [GMAIL_SETUP.md](GMAIL_SETUP.md)

## 3. Start the application

Open **two terminals** in the BRIDGE folder.

**Terminal 1**

```bash
python run.py
```

**Terminal 2**

```bash
python worker.py
```

Then open:

```text
http://127.0.0.1:5000
```

Keep both terminals running if you want scheduled reminders to be processed.

## 4. Try the workflow

1. Paste a message or load a prepared example.
2. Choose the input and output languages.
3. Select **Explain this message**.
4. Review the meaning, steps, dates, location, missing details, and source evidence.
5. Select **Track this task**.
6. Sign in through email or the local development inbox, depending on `MAIL_MODE`.
7. Confirm the deadline, reminder time, and time zone.
8. Save the task.
9. Mark it done after completion, or delete it when it is no longer needed.

## Important

Never upload your real `.env`, `.venv`, `instance/`, API keys, Gmail app password, or local database to GitHub.
