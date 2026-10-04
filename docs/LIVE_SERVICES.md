# Live services (advanced)

For the simplest setup, use [Gemini setup](../GEMINI_SETUP.md) and [Gmail setup](../GMAIL_SETUP.md). This page contains additional provider details and advanced notes.


These are separate switches. Start with local mode and configure one service at a time. Do not commit `.env` or expose service keys in browser JavaScript.

## Gemini alternative

To use your Gemini key, follow [GEMINI_SETUP.md](../GEMINI_SETUP.md). Set AI_MODE=gemini, GEMINI_API_KEY, and GEMINI_MODEL. Email settings remain independent.

## 1. Live AI with OpenAI

Create an API key with your provider account and configure `.env`:

```dotenv
AI_MODE=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

The model name is configurable. Choose a model available to your account that supports the Responses API and strict JSON-schema structured outputs. Verify current availability and pricing rather than relying on this example name.

Restart the web server. The interface will say **Live AI processing**. Paste text, select the output language, and check the consent box before explaining it.

The server sends the document and output-language request to the OpenAI Responses API, requests structured JSON, sets `store=false`, validates the shape, and checks that every action quote appears verbatim in the document. No tools or external actions are exposed to the model.

`store=false` does not establish zero provider retention. Review the provider's current data handling and your organization's policies before using private information.

The adapter and request shape were checked against official documentation and mocked in automated tests. No paid/live calls were made during package validation. Your real credentials, selected model, output quality, and account access still need an end-to-end check.

## 2. Gmail email setup

Follow [GMAIL_SETUP.md](../GMAIL_SETUP.md) for sender credentials, both terminals,
sign-in testing, recipient testing, and scheduled reminders. Use MAIL_MODE=gmail.
No purchased domain is required. Gmail limits and recipient filtering apply.
Email is sent only when users request sign-in or the worker processes due tasks.
A stable Message-ID is used for tracing, not guaranteed duplicate prevention.

## Official references

- https://support.google.com/accounts/answer/185833
- https://developers.google.com/workspace/gmail/imap/imap-smtp
- https://developers.openai.com/api/docs/guides/structured-outputs

Provider calls are mocked in automated tests. Real delivery must be verified
using your credentials. Language support does not guarantee country availability.