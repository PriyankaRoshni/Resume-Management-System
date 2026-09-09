## Backend (FastAPI)

### Setup

1. Create `.env` from `.env.example` and set `GEMINI_API_KEY`.
2. Start Postgres (optional, recommended):

```bash
docker compose up -d
```

3. Install deps:

```bash
python -m pip install -r backend/requirements.txt
```

### Run

```bash
uvicorn backend.app.main:app --reload
```

### Endpoints

- `GET /health`
- `POST /resumes/upload` (multipart file `.pdf`/`.docx`)
- `GET /resumes`
- `GET /resumes/{id}`






Goals





Replace static/demo email data with real Gmail messages for the logged‑in user.



Use Google OAuth for login and mailbox access.



Implement a basic end‑to‑end flow for a single Gmail account per user: login → fetch emails from Gmail → store in DB → show in Dashboard/Inbox/Excel.

High‑level architecture





Frontend (Vite React)





Add Google OAuth login and store auth state (tokens/session) instead of the current fake localStorage flag.



After login, call backend endpoints to sync Gmail and then read /emails, /dashboard/overview, /reports/excel as today.



Backend (FastAPI)





Add Google OAuth routes (/auth/google/start, /auth/google/callback).



Use Google OAuth tokens to call the Gmail REST API from the backend.



Map Gmail messages + attachments into existing EmailMessage/Resume DB models.



Reuse existing /emails, /dashboard/overview, /reports/excel endpoints; they will now operate on synced real data.

flowchart LR
  user[User] --> browser[Frontend]
  browser --> authStart["/auth/google/start"]
  authStart --> googleAuth[GoogleOAuth]
  googleAuth --> authCallback["/auth/google/callback"]
  authCallback --> backend[FastAPIBackend]
  backend --> gmailAPI[GmailAPI]
  gmailAPI --> backend
  backend --> db[(Postgres/SQLite DB)]
  browser --> emailsAPI["/emails, /dashboard/overview, /reports/excel"]
  emailsAPI --> backend
  backend --> db
  backend --> browser

Backend changes





1) Decide on storage for users & tokens





Add a simple User table (if not present) with at least: id, email, google_sub (Google user id), created_at.



Add a UserToken (or extend User) to store:





access_token



refresh_token



token_expiry



Use SQLite or the existing DB via current SQLAlchemy engine in backend/app/db.py.



2) Add Google OAuth config





In backend/.env (and README.md): add variables like:





GOOGLE_CLIENT_ID



GOOGLE_CLIENT_SECRET



GOOGLE_REDIRECT_URI (e.g. http://localhost:8000/auth/google/callback).



In backend/app/main.py (or a new auth.py module), load these via os.getenv.



3) Implement OAuth endpoints





**GET /auth/google/start**





Builds the Google OAuth URL (scope: https://www.googleapis.com/auth/gmail.readonly and basic profile/email), including state to prevent CSRF.



Redirects browser to Google.



**GET /auth/google/callback**





Accepts code & state from Google.



Exchanges code for access_token and refresh_token using Google token endpoint.



Calls Google userinfo endpoint to get the user’s email and sub.



Upserts a User row; stores/updates tokens.



Issues a session token or JWT for the frontend (simplest: HTTP‑only cookie with a signed session id) and redirects to SPA (e.g. /dashboard).



4) Add a dependency for authenticated user





Create get_current_user dependency in, say, backend/app/auth.py that:





reads the session cookie / Authorization header,



validates it,



loads User from DB, and



raises 401 if missing/invalid.



Apply Depends(get_current_user) to email‑related endpoints like /emails, /dashboard/overview, /reports/excel (so data is scoped per user in a later step; for the basic flow we can still use a single user but structure it this way).



5) Gmail sync service





Create a new module, e.g. [backend/app/gmail_sync.py](backend/app/gmail_sync.py):





Function fetch_gmail_messages(user: User, db: Session, max_messages: int = 100) that:





Uses the user’s stored OAuth access_token (refreshes it if expired using refresh_token).



Calls Gmail API users.messages.list with filters (e.g. q="has:attachment" and date range).



For each message id, calls users.messages.get to fetch headers, date, labels, and attachment metadata.



Downloads attachments (PDF/DOCX) as needed using users.messages.attachments.get.



Saves/updates rows in EmailMessage and Resume models:





sender = From header



subject = Subject header



received_at = Date header



source = EmailSource.GMAIL



attachment_type = EmailAttachmentType.PDF / DOCX



status initially UNPROCESSED or PENDING.



Saves attachment files into UPLOAD_DIR (same as current /resumes/upload).



Optionally calls existing pipeline.extract_text + parse_resume_with_gemini to classify each resume and populate Resume records.



6) Sync endpoint





Add a new endpoint in main.py, e.g. POST /emails/sync:





current_user: User = Depends(get_current_user)



db: Session = Depends(get_db)



Calls fetch_gmail_messages(current_user, db).



Returns a summary JSON: { fetched: n, processed: m }.



For now, keep /emails implementation as is but:





Remove demo seeding once real data is flowing.



Optionally filter by the current user when User → Email linkage is added.



7) Dashboard and Excel linkage





Ensure /dashboard/overview counts use real EmailMessage and Resume rows (they mostly already do).



Ensure /reports/excel pulls from Resume records that correspond to Gmail‑fetched resumes.

Frontend changes





1) Replace fake login with Google login





In [frontend/src/pages/LoginPage.tsx](frontend/src/pages/LoginPage.tsx):





Replace manual email/password form with a "Sign in with Google" button.



On click, redirect browser to backend GET /auth/google/start (full page redirect, not XHR).



After Google redirects back and the backend sets a session cookie, the SPA loads as usual.



2) Auth state handling





In [frontend/src/App.tsx](frontend/src/App.tsx) / AppShell:





Replace isAuthed() check that uses localStorage.getItem('auth') with a backend‑driven check, e.g.:





GET /me to verify session and return the logged‑in user info, or



rely on a simple GET /health//me at app load that, if 401, redirects to /login.



Store a lightweight user object in React state/context.



3) Trigger email sync





After confirming the user is logged in (e.g. on first mount of AppShell or DashboardOverviewPage):





Call POST /emails/sync via apiFetch.



Show a spinner / toast while syncing.



Once done, call existing endpoints:





Inbox: GET /emails.



Dashboard: GET /dashboard/overview.



Excel Reports: existing /reports/excel download.



4) Minor UI tweaks





Update texts to reflect that data comes from Gmail.



Add a sign‑out button that clears session (e.g. POST /auth/logout and redirect to /login).

Configuration & local setup





Backend





Update [backend/README.md](backend/README.md) with steps to obtain Google OAuth credentials:





Create a Google Cloud project.



Enable Gmail API & OAuth consent screen.



Create OAuth client (type "Web application") with redirect URI http://localhost:8000/auth/google/callback.



Put GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI into .env.



Document how to run:





uvicorn backend.app.main:app --reload (as already present).



Frontend





Keep VITE_API_URL optional; default to http://localhost:8000 for dev.



Document normal npm install / npm run dev steps (already present in frontend/package.json).

Incremental implementation steps





Step 1: Add DB models for User and token storage and basic /me endpoint.



Step 2: Implement Google OAuth config + /auth/google/start and /auth/google/callback endpoints with a simple cookie‑based session.



Step 3: Implement Gmail sync module and /emails/sync for one user; verify DB rows are created and /emails returns real data.



Step 4: Wire frontend login page to Google OAuth and update auth guards in App.tsx / AppShell.



Step 5: Trigger /emails/sync after login and confirm Inbox, Dashboard, and Excel are populated from real Gmail messages.



Step 6: Clean up: remove demo seeding, polish error handling, and adjust UI copy.

