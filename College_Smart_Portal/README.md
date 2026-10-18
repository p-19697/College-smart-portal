# College Smart Portal

A ready-to-run diploma project built with Python, Flask, SQLite, HTML, CSS, Bootstrap, JavaScript and optional Groq API integration.

## Features
- Home dashboard with summary cards
- Student records with search, department filter and pagination
- Admin CRUD for students and project records
- Academic subject information
- College projects and notices
- Student feedback and ratings
- Admission procedure and common document information
- Optional AI Study Tips powered by Groq API
- SQLite database auto-created with sample records

## Requirements
- Python 3.10 or newer
- VS Code (recommended)
- Internet connection for Bootstrap CDN and optional Groq API

## Run in VS Code (Windows)
1. Extract the ZIP file.
2. Open the `College_Smart_Portal` folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt terminal and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
6. Install packages:
   ```powershell
   pip install -r requirements.txt
   ```
7. Start the website:
   ```powershell
   python app.py
   ```
8. Open the local URL printed in the terminal, usually `http://127.0.0.1:5000`.

## Demo admin login
- Username: `admin`
- Password: `admin123`

The demo credentials are for local testing only. Change them before deploying. You can set `ADMIN_USERNAME`, `ADMIN_PASSWORD` and `FLASK_SECRET_KEY` as environment variables.

## Enable AI Study Tips
1. Copy `.env.example` to a new file named `.env`.
2. Replace the placeholder with your own Groq API key:
   ```
   GROQ_API_KEY=your_real_key_here
   ```
3. Restart the Flask app.
4. Keep `.env` private. Never upload your API key to GitHub or include it in your project report/screenshots.

Without a key, the AI page shows fallback study advice and the rest of the portal still works.

## Database
The SQLite database is created automatically at `instance/college_portal.db` when the app starts. It contains sample student, subject, project and notice records. Keep a backup before deleting or replacing it.

## Important project notes
- This is a starter/academic project, not a production-secure student information system.
- Before public deployment, use strong credentials, a strong secret key, HTTPS, CSRF protection, login rate limiting and stricter access controls.
- Replace sample records with authorized test data and update college details to match your institution.
- PythonAnywhere deployment steps and availability can vary by account plan; test the app locally first.
