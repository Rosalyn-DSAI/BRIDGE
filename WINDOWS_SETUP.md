# Run BRIDGE on Windows

These instructions use PowerShell and work from the main `BRIDGE` folder.

## Requirements

- Python 3.11 or newer
- Internet access for live AI/email modes
- A code editor such as VS Code (recommended)

## 1. Open the project

Open the `BRIDGE` folder in VS Code and choose **Terminal → New Terminal**.

Make sure the terminal is in the folder containing `run.py`.

## 2. Create the virtual environment

```powershell
py -3 -m venv .venv
```

If `py` is unavailable, use:

```powershell
python -m venv .venv
```

## 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

## 4. Create `.env`

```powershell
Copy-Item .env.example .env
```

If `.env` already exists, do not overwrite it.

Generate a secret key:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
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

**Terminal 1 — web app**

```powershell
.\.venv\Scripts\python.exe run.py
```

**Terminal 2 — reminder worker**

```powershell
.\.venv\Scripts\python.exe worker.py
```

Open:

```text
http://127.0.0.1:5000
```

## 6. Optional checks

Translation check:

```powershell
.\.venv\Scripts\python.exe scripts\check_translation.py
```

AI connection check:

```powershell
.\.venv\Scripts\python.exe scripts\check_ai.py
```

Email login check:

```powershell
.\.venv\Scripts\python.exe scripts\check_email.py
```

## Common problems

| Problem | What to check |
|---|---|
| Python command not found | Install Python and reopen the terminal. |
| `.venv` command not found | Confirm the virtual environment was created in the BRIDGE folder. |
| Port 5000 is already in use | Stop the older BRIDGE process before starting another. |
| Changes to `.env` do not appear | Stop and restart both `run.py` and `worker.py`. |
| Reminder does not arrive | Make sure `worker.py` is still running and check the saved reminder time/time zone. |

Stop either process with **Ctrl+C**.
