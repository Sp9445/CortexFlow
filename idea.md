# CortexFlow – Architecture Freeze v1.1

## 🎯 Product Goal (Phase 1–2)

CortexFlow is a secure, AI-assisted personal diary application where:

- Users write raw diary entries in any language
- AI improves the writing while maintaining tone
- Users review and approve the improved version
- Users can also save raw text without AI
- Previous entries can be viewed and edited
- Authentication is required

This version focuses on a clean, production-aligned MVP without over-engineering.

---

# 🖥️ Frontend (Angular)

## Pages

### 1️⃣ Authentication
- Register
- Login
- Logout
- JWT-based protected routes

---

### 2️⃣ Dashboard
- List previous diary entries (latest first)
- Click to open entry
- Basic pagination (optional)

---

### 3️⃣ New Entry Flow

#### Step 1 – Raw Text
Single textarea for writing.

#### Step 2 – Improve
User clicks "Improve".

Backend sends raw text to AI.
Improved text is returned.

#### Step 3 – Improved Text Handling
- AI improved text replaces textarea content
- Original raw text temporarily stored in frontend state
- UI label indicates "AI Improved Version"

#### Step 4 – User Options
- Save Final
- Revert to Raw
- Improve Again
- Save Without AI

---

### 4️⃣ View / Edit Entry

When opening an entry:
- If `improved_text` exists → load improved_text
- Else → load raw_text

User can:
- Edit content
- Improve again
- Save (overwrite existing entry)

No version history in v1.

---

# 🧠 Backend (FastAPI)

Single backend service.

## Core Modules

- auth
- diary
- ai_service
- db
- config

No microservices.

---

# 📡 API Endpoints

## Auth
POST `/auth/register`  
POST `/auth/login`

---

## Diary
POST `/diary/improve`  
POST `/diary/save`  
GET `/diary/list`  
GET `/diary/{id}`  
PUT `/diary/{id}`  

---

# 🗄️ Database Schema

## User

- id (UUID)
- email (unique)
- password_hash
- created_at

---

## DiaryEntry

- id (UUID)
- user_id (FK)
- raw_text (TEXT)
- improved_text (TEXT, nullable)
- created_at
- updated_at

Rules:
- If saved without AI → improved_text = NULL
- raw_text always stores original submission
- improved_text stores final approved/edited content

Overwrite strategy for edits (no versioning yet).

---

# 🤖 AI Layer (Phase 2)

Flow:
Raw text → AI API → Improved text → Return to user

Responsibilities:
- Detect language
- Improve clarity and structure
- Preserve emotional tone
- Maintain authenticity

No personalization memory in v1.
No embeddings.
No vector DB.

---

# 🔐 Security Decisions

- Password hashing (bcrypt/argon2)
- JWT authentication
- HTTPS required in production
- DB encryption at rest (provider-level)
- AI receives raw text directly
- No application-level encryption yet
- No diary content logging in production logs

Limited users deployment.

---

# 🌍 Deployment Strategy

Backend:
- Free tier hosting (Render / Railway type)

Frontend:
- Vercel / Netlify

Database:
- Managed PostgreSQL (free tier)

Public internet deployment with limited users.

---

# 🚫 Explicitly Out of Scope (v1)

- OAuth login
- Role-based access
- Version history
- Vector DB / embeddings
- Tone memory personalization
- Zero-knowledge encryption
- Admin panel
- CI/CD automation
- Advanced rate limiting
- Microservices architecture

---

# 🧱 Engineering Principles

1. Keep it simple first
2. Make it work
3. Then refactor
4. Then harden
5. Incremental evolution
