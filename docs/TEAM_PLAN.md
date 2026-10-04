# Three-person review and build plan

The files are implemented so your team can spend its time understanding, checking, and improving the project rather than starting from an empty folder.

| Person | Owns | Main files |
|---|---|---|
| 1 | Interface and user journey | templates/, static/app.js, static/style.css |
| 2 | AI output quality and multilingual evaluation | analysis.py, data/samples.json, tests/ |
| 3 | Authentication, task storage, and email reminders | routes.py, mail.py, reminders.py, schema.sql |

## Suggested 12-hour schedule

| Time | Outcome |
|---|---|
| Hour 1 | Every teammate runs the app; one controlled real email successfully sends |
| Hours 2–3 | Understand the code, connect live AI, and review each output field |
| Hours 4–5 | Verify English, Chinese, Japanese, and Spanish with fluent readers where possible |
| Hours 6–7 | Exercise sign-in, dates, reminders, completion, and error states |
| Hours 8–9 | Polish the interface and choose a reliable hosted or local presentation setup |
| Hour 10 | Run tests and use unseen messages, exceptions, and missing deadlines |
| Hour 11 | Rehearse the live reminder demonstration and prepare an offline fallback |
| Hour 12 | Freeze changes, rehearse the pitch, and check service credentials and worker uptime |

## Definition of ready

- Each teammate can explain the flow from pasted message to completed task.
- You can distinguish prepared outputs from live AI results.
- One real email flow works with your own sender credentials.
- The team has reviewed language quality and recorded any limitations.
- The worker is running during the presentation.
- No real student, patient, customer, or employee documents are exposed.

Avoid adding OCR, calendar sync, voice input, or organizational integrations until the core journey is stable.
