# How BRIDGE works

## The pieces

| Piece | Responsibility |
|---|---|
| Browser | Message input, language choice, explanations, source highlighting, task review |
| Flask | Validates requests, sessions, AI results, and task ownership |
| SQLite | Stores users, hashed sign-in tokens, tasks, reminders, and local-mode emails |
| AI adapter | Prepared results offline, structured Gemini or OpenAI API response online |
| Email adapter | Local inbox or Gmail SMTP |
| Worker | Polls due reminders, rechecks task completion, and delivers eligible emails |

## From message to task

1. Browser posts text and output language to `/api/analyze`.
2. Backend returns a structured explanation. It does not save the source document.
3. Browser displays source quotes using text nodes, not injected HTML.
4. User selects an action and explicitly enters the deadline and reminder time.
5. Backend validates the time zone, converts to UTC, and requires `now < reminder < deadline`.
6. Task and reminder are inserted in one database transaction.

The model is deliberately not asked to guess a UTC timestamp. This trades a little convenience for visible human confirmation of ambiguous dates.

## Sign-in

`secrets.token_urlsafe(32)` creates a random link token. SQLite stores only its SHA-256 digest, email, expiry, and used flag. The email contains the token. A confirmation POST consumes it once inside a transaction, creates/finds the user, and sets a signed Flask session cookie.

GET requests show a confirmation page but do not consume a token, which avoids sign-in by email link scanners. Local mode has an AJAX equivalent so the browser draft survives. Local mode is not proof of actual email ownership and must not be exposed publicly.

POST/PATCH/DELETE requests need a session-bound CSRF token. Session cookies are HttpOnly and SameSite=Lax; production requires Secure cookies and HTTPS. Do not place documents or API keys in cookies.

## Reminder state

`pending → sent`, `pending → canceled`, or `pending → failed`.

Before sending, the worker obtains a SQLite write transaction and rechecks that the task is pending. Marking a task done cancels a pending reminder. A provider call already in progress cannot be recalled; completion may briefly wait for the send transaction to finish.

Gmail SMTP uses a stable Message-ID for tracing, not deduplication. Known transient failures retry up to five attempts within 23 hours. Authentication errors, permanent rejections, and uncertain sends stop automatic retries. A crash after SMTP acceptance but before database commit may cause duplicate delivery. Exactly-once delivery is not guaranteed.

Holding a SQLite write lock during the provider call prevents a common completion/send race but can block other writes for the network timeout. This is an intentional small-project tradeoff. For higher volume, use a database-backed job queue with explicit leases and reconciliation.

Reminders missed while the worker is offline are processed after restart, even if the deadline has passed. Their wording says the task is still marked not done, rather than promising it is due tomorrow.

## API summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/config` | Modes, signed-in user, server time, CSRF token |
| GET | `/api/samples` | Original fictional sample texts |
| POST | `/api/analyze` | Explain text in a chosen language |
| POST | `/api/auth/request` | Request email sign-in link |
| GET/POST | `/auth/confirm` | Show and consume sign-in link |
| POST | `/api/auth/local-confirm` | Local-only sign-in for the review inbox |
| POST | `/api/auth/logout` | Sign out |
| GET/POST | `/api/tasks` | List own tasks / create a task |
| POST | `/api/tasks/<id>/complete` | Confirm completion |
| DELETE | `/api/tasks/<id>` | Delete own task and pending reminder |
| GET | `/api/inbox` | Local-only browser/account-scoped email inbox |
| POST | `/api/local/run-reminders` | Local-only due check for signed-in user's tasks |
| GET | `/health` | Basic health check |

Task payload fields: `title`, `language` (`en`, `zh`, `ja`, `es`), `due_local`, `remind_local` (both `YYYY-MM-DDTHH:MM`), `timezone` (IANA name), `source_title`, optional `details` (`steps`, `location`, `deadline_text`, `conditions`), and `confirmed: true`.

## Data minimization

Task title, checklist, stated time/location, conditions, source title, language, confirmed dates, and status are saved. Task details are also included in reminder emails. The full document and AI explanation stay in browser memory unless included in saved task fields. Local inbox messages are stored in SQLite for review. Secrets and personal runtime data are excluded from the ZIP.

## Grouped instructions

The AI returns one action per independent outcome, with related steps in a checklist.
Each grouped action must have an exact source passage. Time and location are optional;
event times are shown as context and do not automatically set the confirmed deadline.
Empty condition placeholders are removed. A script check rejects untranslated CJK
time/condition wording for English or Spanish output; it is not full language validation.
Existing databases receive a nullable-free JSON details column with an empty-object
default. Old tasks remain readable. No existing reminders are rescheduled.
