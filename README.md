# Public Service Request System (Mini eCitizen-style)

A Flask web application demo where citizens can register, submit public-service requests, track request status, and administrators can review and update requests.

## Features
- Citizen registration and sign-in
- Submit requests for services such as permits, water, roads, sanitation, and other county services
- Reference number generated for each request
- Citizen dashboard showing submitted requests and status
- Public tracking page using the reference number
- Admin dashboard with status counts and request status updates
- SQLite database for a simple demonstration
- Responsive Bootstrap interface

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create and activate a virtual environment:
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start the app: `python app.py`
6. Visit `http://127.0.0.1:5000`

## Demo administrator
- Email: `admin@example.com`
- Password: `Admin123!`

Change these credentials and set a strong `SECRET_KEY` before deploying a real system. This is a coursework prototype, not a production government service.

## Deploy to Render
1. Create a GitHub repository and upload all files in this folder.
2. In Render, choose **New + → Web Service**, connect the repository, and use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
3. Add an environment variable named `SECRET_KEY` with a long random value.
4. Deploy, then copy the public `https://...onrender.com` URL into the assignment portal.

**Important database note:** SQLite is suitable for a small coursework demo. On hosting platforms, local files may not persist across redeployments unless persistent storage is configured. For a durable public deployment, use a managed PostgreSQL database and CSRF protection, rate limiting, and stronger production access controls. Passwords in this prototype are hashed.

## Suggested GitHub repository name
`public-service-request-system`

## Assignment submission
- GitHub / GitLab Repository URL: your repository's actual URL
- Live / Deployed URL: the URL Render gives you after deployment
- Notes: `Mini eCitizen-style public service request system with citizen registration, service request submission, reference-based tracking, and an administrator dashboard for updating request status.`
