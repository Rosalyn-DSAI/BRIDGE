# Privacy and limitations

- In demo AI mode, source text is compared to local fixtures; it is not sent to an AI service.
- In live AI mode, the document is sent to the selected provider (Gemini or OpenAI) after consent. Provider policies apply. The Gemini free tier may use submitted content to improve products; OpenAI requests set store=false, which does not guarantee zero retention.
- BRIDGE does not save full source documents or full AI results to SQLite. Browser memory contains them while the page is open.
- Saved task titles, checklists, time/location wording, and conditions may contain sensitive information. They appear in reminder emails. Review these details before saving.
- Live emails go to Gmail SMTP and the recipient's mail provider. BRIDGE cannot recall accepted mail, guarantee inbox delivery, or prove it was read.
- Local inbox contents include usable sign-in links. This mode is deliberately restricted to localhost and is not real email ownership verification.
- Task ownership is enforced on the server. Completion is a user's declaration, not proof from another organization.
- Model output can mistranslate or omit details. Exact source-quote matching checks presence, not semantic correctness. It is not a confidence score or a verification proof.
- The UI requires confirmed dates instead of guessing relative dates, unstated time zones, or missing years. Conditions and exceptions must still be reviewed.
- The application supports pasted text, not scanned PDFs, images, or attachments. Document text that contains instructions to the AI is treated as untrusted data, but prompt injection cannot be completely ruled out.
- There is no automatic account deletion or retention job in this prototype. Users can delete tasks; old local emails and account records remain until the database is reset or retention tooling is added.
- Do not claim universal accuracy, legal compliance, clinical reliability, or access from every country. Test service availability and organizational policies in the intended setting.
