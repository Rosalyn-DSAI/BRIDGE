# Run BRIDGE on macOS or Linux

These instructions use Terminal and work from the main `BRIDGE` folder.

## Requirements

- Python 3.11 or newer
- Internet access for live AI/email modes

Check Python:

```bash
python3 --version
```

## 1. Open the project folder

In Terminal, move into the folder that contains `run.py`.

Example:

```bash
cd /path/to/BRIDGE
```

## 2. Create the virtual environment

```bash
python3 -m venv .venv
```

## 3. Install dependencies

```bash
.venv/bin/python -m pip install -r requirements-lock.txt
```

## 4. Create `.env`

```bash
cp .env.example .env
```

If `.env` already exists, do not overwrite it.

Generate a secret key:

```bash
.venv/bin/python -c "import secrets; print(secrets.token_hex(32))"
```

Paste that value into `SECRET_KEY` in `.env`.

For service configuration, follow:

- [GEMINI_SETUP.md](GEMINI_SETUP.md)
- [GMAIL_SETUP.md](GMAIL_SETUP.md)

For offline/local review, use:

```dotenv
APP_ENV=local
AI_MODE=demo
MAIL_MODE=local
BASE_URL=http://127.0.0.1:5000
HOST=127.0.0.1
PORT=5000
```

## 5. Start BRIDGE

Open two Terminal windows/tabs in the BRIDGE folder.

**Terminal 1 — web app**

```bash
.venv/bin/python run.py
```

**Terminal 2 — reminder worker**

```bash
.venv/bin/python worker.py
```

Open:

```text
http://127.0.0.1:5000
```

## 6. Optional checks

Translation check:

```bash
.venv/bin/python scripts/check_translation.py
```

AI connection check:

```bash
.venv/bin/python scripts/check_ai.py
```

Email login check:

```bash
.venv/bin/python scripts/check_email.py
```

## Common problems

| Problem | What to check |
|---|---|
| `python3` not found | Install a supported Python version first. |
| Virtual environment cannot be created | On some Linux systems, install the OS package that provides Python `venv`. |
| Port 5000 is already in use | Stop the older process using that port. |
| `.env` changes do not appear | Restart both the web app and worker. |
| Reminder does not arrive | Confirm the worker is running and check the saved reminder time/time zone. |

Stop either process with **Ctrl+C**.
