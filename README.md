# BRIDGE

**Clarity that leads to action.**

BRIDGE turns complex or multilingual messages into clear, actionable tasks with dates, locations, missing-information warnings, source evidence, task tracking, and email reminders.

> **Message → Meaning → Action → Connection**

BRIDGE was created around a simple idea: a message has not truly connected two people just because it was delivered. Connection happens when the receiver understands the meaning and knows what to do next.

## What BRIDGE can do

- Explain pasted text in plain language.
- Translate between **English, Simplified Chinese, Japanese, and Spanish**.
- Extract instructions into clear, trackable steps.
- Identify stated dates, times, locations, conditions, and deadlines.
- Flag important information that is missing instead of inventing it.
- Show the exact source passage behind an extracted instruction.
- Let a signed-in user save and track tasks.
- Schedule one email reminder for a saved task.
- Mark tasks complete or delete them.
- Run with prepared examples offline, or use live Gemini/OpenAI processing.

## Who can use it?

BRIDGE is designed for anyone who receives instructions that may be long, unfamiliar, multilingual, or easy to misunderstand. Example users include international students, employees, parents, travelers, older adults, schools, universities, workplaces, and service organizations.

BRIDGE is an assistive communication tool, not a replacement for authoritative medical, legal, financial, or institutional advice.

## How it works

1. Choose the input language or let BRIDGE detect it automatically.
2. Choose the language you want the explanation in.
3. Paste a message and select **Explain this message**.
4. Review the plain-language meaning, instructions, dates, location, and missing details.
5. Use **Show source** to compare an instruction with the original text.
6. Select **Track this task** if you want to save it.
7. Sign in with the one-time email link.
8. Confirm the deadline, reminder time, and time zone yourself.
9. BRIDGE saves the task and the background worker sends the reminder when due.
10. Mark the task as done when you complete it, or delete it if you no longer need it.

BRIDGE deliberately does **not** assume that an event date is automatically a submission deadline. When the source is unclear, the user is asked to confirm the date instead.

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask, Waitress |
| AI | Gemini API or OpenAI API |
| Structured output | JSON, JSON Schema, `jsonschema` |
| Data | SQLite |
| Authentication | Passwordless email sign-in, Flask sessions |
| Email | Gmail SMTP or local development inbox |
| Background processing | Python reminder worker |
| Configuration | `.env`, `python-dotenv` |

### Architecture in one line

**Browser → Flask API → AI analysis → validation → SQLite → reminder worker → email**

Gemini or OpenAI is one service inside BRIDGE. The application also provides structured extraction, validation, source evidence, task persistence, authentication, reminder scheduling, and email delivery.

## Quick start

Choose your operating system:

- **Windows:** [WINDOWS_SETUP.md](WINDOWS_SETUP.md)
- **macOS / Linux:** [MAC_LINUX_SETUP.md](MAC_LINUX_SETUP.md)
- **Short overview:** [QUICKSTART.md](QUICKSTART.md)

Then configure the services you want:

- **Gemini AI:** [GEMINI_SETUP.md](GEMINI_SETUP.md)
- **Gmail email delivery:** [GMAIL_SETUP.md](GMAIL_SETUP.md)
- **Other live-service options:** [docs/LIVE_SERVICES.md](docs/LIVE_SERVICES.md)

> Never commit your real `.env` file, API keys, Gmail app password, local database, or virtual environment to a public repository. Use `.env.example` as the public template.

## Run BRIDGE

BRIDGE uses two processes:

**Terminal 1 — web application**

```bash
python run.py
```

**Terminal 2 — reminder worker**

```bash
python worker.py
```

Then open:

```text
http://127.0.0.1:5000
```

If your virtual environment is not activated, use the OS-specific commands in the setup guides instead.

## AI and email modes

AI and email are independent settings.

| Setting | Local/review mode | Live mode |
|---|---|---|
| `AI_MODE` | `demo` | `gemini` or `openai` |
| `MAIL_MODE` | `local` | `gmail` |

This means you can test live AI with the local inbox, or real Gmail delivery with prepared examples.

## Project structure

```text
BRIDGE/
├── run.py                  # Web-server entry point
├── worker.py               # Reminder worker
├── requirements.txt
├── requirements-lock.txt
├── .env.example            # Safe configuration template
├── README.md
├── QUICKSTART.md
├── WINDOWS_SETUP.md
├── MAC_LINUX_SETUP.md
├── GEMINI_SETUP.md
├── GMAIL_SETUP.md
├── bridge/
│   ├── analysis.py         # AI analysis, translation and validation
│   ├── routes.py           # Web/API routes
│   ├── db.py               # SQLite access
│   ├── mail.py             # Email delivery
│   ├── reminders.py        # Reminder processing
│   ├── security.py         # Security controls
│   ├── templates/
│   └── static/
├── scripts/
├── tests/
└── docs/
```

The `instance/` folder is created locally and contains runtime data such as the SQLite database. Do not commit it publicly.

## Testing

Install the development requirements and run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

For the multilingual live check:

```bash
python scripts/check_translation.py
```

See [docs/TESTING.md](docs/TESTING.md) for the detailed test scope and limitations.

## Important limitations

- Input is pasted text only; PDF/image/OCR upload is not implemented yet.
- AI output can still be wrong, incomplete, or mistranslated and should be reviewed against the source.
- Exact source matching proves that the quoted passage exists, not that the AI interpreted it perfectly.
- Users confirm deadlines and reminder times themselves; BRIDGE does not invent missing dates.
- One reminder is supported per saved task.
- SQLite and the current worker design are appropriate for this prototype, not high-volume production use.
- Real email delivery depends on Gmail SMTP availability, sending limits, and spam filtering.

Read [docs/PRIVACY_AND_LIMITATIONS.md](docs/PRIVACY_AND_LIMITATIONS.md) before using BRIDGE with real information.

## Future direction

Planned directions include PDF/document upload, OCR, voice input and output, more languages, calendar integration, Gmail/Outlook import, Slack/Teams/Notion integrations, confidence and ambiguity scoring, stronger enterprise privacy controls, and production-scale databases and job queues.

## More documentation

- [Quick start](QUICKSTART.md)
- [Windows setup](WINDOWS_SETUP.md)
- [macOS / Linux setup](MAC_LINUX_SETUP.md)
- [Gemini setup](GEMINI_SETUP.md)
- [Gmail setup](GMAIL_SETUP.md)
- [Architecture and API](docs/ARCHITECTURE.md)
- [Live services](docs/LIVE_SERVICES.md)
- [Testing](docs/TESTING.md)
- [Privacy and limitations](docs/PRIVACY_AND_LIMITATIONS.md)
- [Deployment notes](docs/DEPLOYMENT.md)

## Team

Built by:

- Chukwunonyelum Rosalyn Ezeako
- Ruyi Gai
- Odunayo Juliana Owokade

**UCM MuleHacks Hackathon 2026**