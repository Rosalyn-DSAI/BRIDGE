# Validation and review

## Automated backend tests

Run from the BRIDGE folder:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Package validation: **68 tests passed** using Python 3.12. Tests cover:

- Four sample documents × four output languages and exact source-quote matching.
- Refusal to pretend that arbitrary text has been processed in offline mode.
- CSRF enforcement and authentication requirements.
- Expiring, single-use sign-in links; GET does not consume a link.
- Task ownership and local inbox separation.
- Due-time checks, localized reminder text, and no duplicate delivery during repeat or parallel worker passes.
- Completion canceling a pending reminder.
- Invalid time zones, missing/invalid dates, and daylight-saving ambiguity.
- Bounded retries and a stable message identifier; SMTP does not guarantee duplicate prevention.
- Mocked Gemini, OpenAI, and Gmail SMTP request/response contracts without paid calls or real emails.
- Local inbox and local sign-in endpoints being unavailable in production mode.

## Gmail-specific checks

Mocked SMTP tests verify TLS certificate validation, sender authentication,
different recipient addresses, Unicode content, safe errors, and successful
worker delivery. Permanent and uncertain failures stop retries. Cleanup errors
after acceptance do not change a successful send into a failed send.

No real Gmail credentials were used, no email was sent, and no fresh visual
browser check was performed for this update. Live delivery remains a required
user acceptance test. The task display includes grouped steps and optional details.

## Still required with your credentials

1. Test a live AI request with a new document in each supported language.
2. Ask fluent readers to check translations, exceptions, dates, and action wording. Prepared examples are not independent translation-quality validation.
3. Confirm a real sign-in email reaches an account you control.
4. Confirm one real reminder arrives and its link opens the correct task.
5. Verify a completed task does not generate a pending reminder.
6. Confirm your hosted worker and database remain available after restarts.

## Useful challenging inputs

| Input | Expected behavior |
|---|---|
| “Submit this by Friday.” | Do not infer the exact Friday or time zone; ask the user to confirm. |
| “Complete training unless you already completed it this year.” | Preserve the exception; do not assign an unconditional repeat task. |
| A report with observations but no instructions | Return no explicit actions; do not invent professional advice. |
| “Late submission may delay processing.” | Preserve “may”; do not turn a possibility into certainty. |
| Chinese document, Spanish output | Explain in Spanish; retain Chinese source evidence. |
| A task completed before its reminder | Mark pending reminder canceled. |
| A temporarily unavailable email service | Retry within bounds and show errors; do not claim delivery. |
| Commands embedded in the pasted document | Treat them as document content, not authority over the app. |

Record failures honestly. A clean demo should not be presented as proof of universal accuracy.

Gemini update: custom-text processing, consent enforcement, API-key header handling, incomplete/blocked output, and safe quota/key/model diagnostics are covered. Live Gemini access still needs the user-owned key and account.

## Grouped-task regression coverage

Tests cover placeholder removal, untranslated time detection, exact source validation,
independent action preservation, checklist persistence in a single task/reminder,
invalid details, and migration from the previous database layout without deleting tasks.
Live grouping and translation quality require representative documents and human review.

## Task display checks

Run `node tests/check_task_display.cjs` with Node.js for dependency-free DOM-stub
checks of one task card, three steps, hidden empty conditions, and task review.
This exercises the actual rendering functions but is not a visual browser test.
JavaScript syntax is checked with `node --check bridge/static/app.js`.
