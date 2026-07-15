# Postman Collection — PranataCRM API

## Import

1. Import `PranataCRM.postman_collection.json` (Collections).
2. Import `PranataCRM.postman_environment.json` (Environments), then select it as the active environment.
3. Make sure the backend is running (`http://localhost:8000` for local `run.py`, or edit the
   `base_url` environment variable to `http://localhost:8230/api/v1` if using `docker compose`).

## How the automation works

- **Tenant slug + auth cookies are injected automatically** on every request via the
  collection-level pre-request script — no manual header/cookie copying.
- **Tokens/IDs are captured automatically** by the collection-level and per-request test
  scripts: `access_token`, `refresh_token`, `tenant_id`, `user_id`, `contact_id`, `company_id`
  all get filled in as you go.
- **`X-Request-ID`** from every response is stored in `last_request_id` — handy for finding the
  matching structured log line if something fails.

## Suggested run order

Run folders top to bottom: **Auth → Users → Contacts → Companies → Cleanup & Extras**. Or just
click "Run collection" to execute everything in order.

- **Search Users / Lookup Users** (Users folder) and **Search Companies / Lookup Companies**
  (Companies folder) are the autocomplete endpoints behind the `owner_id` and `company_id`
  pickers on the frontend contact form — they return a lightweight summary (id + a couple of
  display fields), not the full resource. `Search` matches by name (users: name/email;
  companies: name/domain) and only returns active records; `Lookup` batch-resolves already-saved
  ids back to display labels via a comma-separated `ids` query param.

- `Register Tenant` generates a unique tenant slug + email every time it runs, so the whole
  collection can be re-run (or run via Newman/CI) without ever hitting `AUTH_SLUG_TAKEN` /
  `AUTH_EMAIL_EXISTS`.
- `Logout` is placed in **Cleanup & Extras at the end on purpose** — it clears the session
  cookies, so anything run after it would 401.

## Two manual values

The backend doesn't have list endpoints for these yet, so they can't be auto-captured:

- **`role_id`** (Users folder) — a Role UUID for the tenant. Every tenant gets an
  "Administrator" role auto-created on registration; look it up in the `roles` table.
- **`invite_token`** (Cleanup & Extras / Accept Invite) — the JWT emailed to the invitee by
  `Invite User`. Paste it from the email (or backend logs) into the `invite_token`
  environment variable. Without it, the request intentionally returns 400 and the test script
  skips the assertion instead of failing the run.

## Running headlessly (Newman)

```bash
npx newman run PranataCRM.postman_collection.json \
  -e PranataCRM.postman_environment.json \
  --folder Auth --folder Contacts --folder Companies --folder "Cleanup & Extras"
```

(Skip the `Users` folder unless `role_id` is set in the environment first.)
