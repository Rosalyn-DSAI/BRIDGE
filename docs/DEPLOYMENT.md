# Deployment

BRIDGE runs locally today and is being prepared for hosted deployment.

> **Fly.io-specific deployment instructions will be added after the deployment configuration is created and tested.**

Do not copy local settings directly into a public deployment.

## What a hosted deployment needs

A small hosted BRIDGE demonstration needs:

1. A Python runtime with the project dependencies installed.
2. `APP_ENV=production`.
3. A strong `SECRET_KEY` stored in the host's secret manager.
4. Live AI credentials if `AI_MODE=gemini` or `AI_MODE=openai`.
5. Gmail credentials if `MAIL_MODE=gmail`.
6. A public HTTPS `BASE_URL` that exactly matches the deployed site.
7. `HOST=0.0.0.0` and the port supplied by the hosting platform.
8. Persistent database storage shared by the web process and reminder worker.
9. Both `run.py` and `worker.py` kept running and restarted after failures.
10. Outbound access to the configured AI provider and Gmail SMTP if those live services are enabled.

## SQLite warning

The current prototype uses SQLite. A hosted copy therefore needs persistent storage that is available to both the web process and reminder worker.

Do not place the SQLite database only on an ephemeral filesystem, and do not run the web process and worker against two unrelated database copies.

For higher traffic, multiple replicas, or production use, move to a shared production database and a proper background-job queue.

## Production configuration example

Use environment variables/secrets on the hosting platform rather than uploading a real `.env` file.

Typical production values include:

```dotenv
APP_ENV=production
AI_MODE=gemini
MAIL_MODE=gmail
BASE_URL=https://YOUR_PUBLIC_DOMAIN
HOST=0.0.0.0
SECRET_KEY=YOUR_PRODUCTION_SECRET
DATABASE_PATH=YOUR_PERSISTENT_DATABASE_PATH
```

Add provider/email secrets through the hosting platform's secret manager.

## Before making the deployment public

Test all of the following with accounts you control:

- HTTPS and public sign-in links
- AI processing
- task ownership between users
- reminder scheduling
- real email delivery
- mark-as-done cancellation
- restart persistence
- health endpoint
- database backups

Also add appropriate monitoring, retention/account-deletion policies, abuse controls, cost limits, and provider-specific privacy review before use beyond a controlled demonstration.

For the current local setup, start with [../QUICKSTART.md](../QUICKSTART.md).
