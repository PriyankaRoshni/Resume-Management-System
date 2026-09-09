# NASSCOM Project – Resume Management & Classification System

## 📌 Project Overview

This project is a resume management and classification system designed to automate the process of collecting resumes from email, processing resume documents, extracting relevant information, and organizing candidate data into structured Excel reports.

The system integrates a backend, frontend, email processing pipeline, and database services to provide an organized workflow for resume management.

---

## 🚀 Key Features

- 📧 Fetch resumes and attachments from email
- 📄 Process PDF and DOCX resume files
- 🤖 Classify resumes using a Gemini-based processing pipeline
- 👤 Extract candidate information from resumes
- 📊 Generate structured Excel reports
- 📑 Organize classified candidates into separate Excel sheets
- 🔐 Support authentication and email connectivity
- 🗄️ PostgreSQL database support
- 🌐 React + TypeScript frontend
- ⚙️ Python backend and email-processing system
- 🐳 Docker Compose configuration for PostgreSQL

---

## 🏗️ Project Structure

```text
NASSCOM_Project-/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── db.py
│   │   ├── gmail_sync.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── README.md
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   └── vite.config.ts
│
├── system/
│   ├── __init__.py
│   ├── fetch_emails.py
│   └── requirements.txt
│
├── check_email_connection.py
├── regenerate_excel_improved.py
├── replace_excel.py
├── docker-compose.yml
└── .gitignore
