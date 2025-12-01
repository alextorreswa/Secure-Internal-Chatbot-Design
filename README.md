# Secure Internal Chatbot Design – Prototype

**Course:** AD331 – Fall 2025  
**Company:** Cascade Freight Systems  
**Team:** Jeremy Clements · Ermiyas Hailemichael · Alex Torres · David Davis

## Project Overview

This repository contains a **minimal proof-of-concept** for the Cascade Freight Systems
**secure, in-house compliance chatbot**.

For this milestone, we focus on demonstrating **one core security feature** from the
full design: **secure login with role-based access control**, implemented on a local
backend. The prototype simulates how employees (e.g., warehouse supervisors and
compliance officers) authenticate before accessing the internal chatbot, which will
eventually answer compliance-related questions using internal documents only.

This aligns with our system design for an on-premise, locally hosted LLM-based chatbot
where all data stays inside Cascade Freight’s private network and all user actions are
audited for compliance.  

## Key Security Feature Demonstrated

- **Secure Login & Auth Flow**
  - Passwords are **hashed** using `bcrypt` (no plain-text storage).
  - Users receive a **short-lived JWT** access token on successful login.
  - Protected endpoints require a valid JWT, illustrating access control.
- **Role-Based Access Concept**
  - Demo accounts illustrate four roles:
    - `warehouse_supervisor`
    - `compliance_officer`
    - `warehouse_manager`
    - `ceo`
  - The protected chat page shows different access messages depending on the role,
    representing how access to audit logs vs. basic checklists would be restricted.
- **Foundations for Compliance & Auditability**
  - The prototype lays the groundwork for:
    - Local-only LLM inference (e.g., Mistral 7B via Ollama).
    - Encrypted storage and access logging in a real PostgreSQL database.
    - Integration with MFA and centralized identity (e.g., Keycloak) in future work.

> Note: For simplicity, user accounts are stored in an in-memory dictionary and
> tokens are displayed on screen. In production, these would be moved to encrypted
> PostgreSQL tables, HttpOnly cookies, and integrated with the company’s IAM stack.

## Technologies Used

**Backend:**

- [FastAPI](https://fastapi.tiangolo.com/) – async Python web framework
- [Uvicorn](https://www.uvicorn.org/) – ASGI server
- [python-jose](https://python-jose.readthedocs.io/) – JWT creation & validation
- [passlib[bcrypt]](https://passlib.readthedocs.io/) – secure password hashing
- [Jinja2](https://jinja.palletsprojects.com/) – HTML templating for the login/chat pages

**Planned (not fully implemented in this prototype but part of the design):**

- Local LLM hosting with **Ollama** (e.g., Mistral 7B / LLaMA 3)
- **PostgreSQL** with encryption at rest for user data and chat logs
- **Next.js + TailwindCSS** frontend for a production-ready dashboard UI
- **Keycloak** for centralized identity and MFA

## Repository Structure

```text
Secure-Internal-Chatbot-Design/
├─ backend/
│  ├─ app/
│  │  ├─ main.py          # FastAPI app with secure login + protected chat
│  │  └─ templates/
│  │      ├─ login.html   # Login form
│  │      └─ chat.html    # Protected chat page (prototype UI)
│  └─ requirements.txt
└─ README.md
```

## Setup & Run Instructions

Follow the steps below to install dependencies, activate the virtual environment, and run the secure-login prototype.

---

### 1. Clone the Repository

```bash
git clone https://github.com/alextorreswa/AI-ML-Assignment-7-LLM-FineTuning-LoRA.git
cd Secure-Internal-Chatbot-Design/backend
```

---

### 2. Create and Activate the Virtual Environment

#### Windows (PowerShell):
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Windows (Git Bash):
```bash
python -m venv .venv
source .venv/Scripts/activate
```

#### macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should now see `(.venv)` at the beginning of your terminal prompt.

---

### 3. Install All Dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, Passlib, python-jose, Jinja2, and more.

---

### 4. Run the Development Server

```bash
uvicorn app.main:app --reload
```

If uvicorn is not recognized:

```bash
python -m uvicorn app.main:app --reload
```

You should see:

```
Uvicorn running on http://127.0.0.1:8000
```

---

### 5. Access the Prototype

#### Login Page:
```
http://127.0.0.1:8000/login
```

Demo accounts:

- Warehouse Supervisor  
  - `alext / supervisor123`
- Compliance Officer  
  - `jeremyc / compliance123`
- Warehouse Manager
  - `ermiyash / manager123`
- CEO
  - `davidd / ceo123`

---

### 6. Test Protected API (Swagger)

Open:

```
http://127.0.0.1:8000/docs
```

1. Click **Authorize**
2. Login or paste your token
3. Test:
```
/api/chat?query=Show last three violations in Tacoma
```

Expected JSON reply includes user, role, and prototype answer.

---

### 7. Stop the Server

Press:

```
CTRL + C
```

---

## System is Operational

Your secure login prototype is ready for demonstration and assignment submission.
