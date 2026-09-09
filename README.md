
# NASSCOM Project – Resume Management & Classification System

## 📌 Overview

A resume management system that automates resume collection, processing, classification, and candidate data organization.

## 🚀 Features

- 📧 Fetch resumes from email
- 📄 Process PDF and DOCX resumes
- 🤖 AI-based resume classification
- 👤 Extract candidate information
- 📊 Generate Excel reports
- 🗄️ PostgreSQL database support
- 🌐 React + TypeScript frontend
- 🐍 Python backend
- 🐳 Docker support

## 🛠️ Technologies

**Frontend:** React, TypeScript, Vite  
**Backend:** Python, FastAPI  
**Database:** PostgreSQL  
**AI/Data:** Gemini, Pandas, OpenPyXL  
**APIs:** Gmail API, Microsoft Graph API  
**Tools:** Git, GitHub, Docker

## 🔄 Workflow

```text
Email
  ↓
Resume Attachments
  ↓
Text Extraction
  ↓
AI Classification
  ↓
Candidate Information
  ↓
Excel Report
````

## 📁 Project Structure

```text
NASSCOM_Project-/
├── backend/
├── frontend/
├── system/
├── .gitignore
├── docker-compose.yml
└── README.md
```

## ⚙️ Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database

```bash
docker compose up -d
```

## 🔐 Security

Sensitive files such as `.env`, `credentials.json`, `token.pickle`, databases, and candidate resumes are excluded from the repository.

## 👩‍💻 Author

**Priyanka Roshni**

GitHub: [https://github.com/PriyankaRoshni](https://github.com/PriyankaRoshni)


