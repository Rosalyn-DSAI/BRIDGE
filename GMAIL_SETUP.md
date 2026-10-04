# Configure Gmail email delivery for BRIDGE

Use this guide after completing the Windows or macOS/Linux setup.

BRIDGE uses Gmail SMTP for real sign-in links and reminder emails.

## Requirements

- A Gmail/Google account you are allowed to use as the sender
- 2-Step Verification enabled on that account
- A Google app password

The app password is used by BRIDGE instead of your normal Google password.

## 1. Add Gmail settings to `.env`

Set:

```dotenv
MAIL_MODE=gmail
SMTP_USER=YOUR_SENDER_ADDRESS@gmail.com
SMTP_APP_PASSWORD=YOUR_GOOGLE_APP_PASSWORD
MAIL_FROM=
```

Leave `MAIL_FROM` blank unless you intentionally need a different supported configuration. BRIDGE normally uses the authenticated Gmail sender.

Never commit your app password or real `.env` file to GitHub.

## 2. Restart BRIDGE

After changing `.env`, stop and restart both:

```bash
python run.py
```

and:

```bash
python worker.py
```

## 3. Test SMTP login

Run:

```bash
python scripts/check_email.py
```

This checks the connection and authentication without sending a normal reminder email.

If your virtual environment is not activated, use the OS-specific Python path from [WINDOWS_SETUP.md](WINDOWS_SETUP.md) or [MAC_LINUX_SETUP.md](MAC_LINUX_SETUP.md).

## 4. Test sign-in

1. Open BRIDGE.
2. Select **Email sign-in**.
3. Enter an email address you can access.
4. Check that inbox and spam folder.
5. Open the BRIDGE sign-in link and confirm within 15 minutes.

When running on localhost, the link points to `127.0.0.1`, so it must be opened on the same computer running BRIDGE.

## 5. Test a reminder

1. Explain a message and select **Track this task**.
2. Confirm a deadline a few minutes in the future.
3. Set the reminder earlier than the deadline.
4. Save the task.
5. Keep `worker.py` running.
6. Check the signed-in user's email inbox when the reminder time arrives.

BRIDGE sends one reminder per saved task. Marking a task complete cancels a reminder that has not already been sent.

## Troubleshooting

| Problem | What to check |
|---|---|
| Gmail authentication fails | Sender address, 2-Step Verification, and app password |
| Cannot connect to SMTP | Internet/firewall access to Gmail SMTP over SSL |
| Sign-in email does not arrive | Spam folder, sender account, and web-server logs |
| Reminder does not arrive | `worker.py`, saved reminder time, time zone, and spam folder |
| Sign-in link expired | Request another link |

Gmail sending limits and spam filtering still apply. A successful SMTP send means the mail service accepted the message; it does not prove that the recipient read it.

Google reference: [App passwords](https://support.google.com/accounts/answer/185833)
