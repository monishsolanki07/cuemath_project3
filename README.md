# 🎓 AI Teacher Interview System

![Build](https://img.shields.io/badge/build-passing-brightgreen) ![License](https://img.shields.io/badge/license-MIT-blue) ![Next.js](https://img.shields.io/badge/Frontend-Next.js-black) ![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688) ![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange) ![Deploy](https://img.shields.io/badge/Deploy-Vercel%20%2B%20Render-blueviolet)

> A real-time, voice-based AI interviewer that evaluates teaching candidates across **any subject** using context-aware questioning and adaptive feedback.

---

## 🚀 Overview

The **AI Teacher Interview System** is an intelligent, real-time interview platform designed to assess candidates for teaching roles across multiple domains — Mathematics, Science, English, History, and beyond.

Recruiters simply provide a **Job Description (JD)** and optionally a **candidate resume**, and the system dynamically adapts its questioning strategy — no hardcoding needed.

---

## 🧠 Key Features

- 🎤 Voice-based interview (Speech-to-Text + Text-to-Speech)
- ⚡ Real-time interaction using WebSockets
- 🧠 Context-aware AI questioning (Google Gemini 2.5 Flash)
- 🎭 Dynamic interviewer personas
- 📊 Automated feedback & evaluation report
- ⏱️ Silence detection & smart response handling
- 📄 PDF report generation
- 🌍 Subject-independent architecture

---

## 🏗️ System Architecture
Client (Next.js)
↓
Speech-to-Text (Browser API)
↓
WebSocket (Real-time)
↓
FastAPI Backend
↓
Gemini AI Engine (gemini-2.5-flash)
↓
Text-to-Speech (Edge TTS / gTTS)
↓
Audio Stream → Client

---

```
THE_ONE/
│
├── 📁 Backend/
│   ├── main.py              ← FastAPI app, WebSocket, AI logic
│   ├── requirements.txt     ← Python dependencies
│   ├── .env                 ← API keys (not committed)
│   └── .gitignore
│
└── 📁 Frontend/
    └── interviewer/
        │
        ├── 📁 app/
        │   ├── layout.tsx   ← Root layout
        │   ├── page.tsx     ← Main interview UI
        │   ├── globals.css  ← Global styles
        │   └── favicon.ico
        │
        ├── 📁 public/       ← Static assets (SVGs, icons)
        │
        ├── next.config.ts
        ├── tsconfig.json
        ├── package.json
        └── .env             ← Frontend env vars
```

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Speech | react-speech-recognition, Edge TTS, gTTS |
| Backend | FastAPI, WebSockets, Python asyncio |
| AI | Google Gemini 2.5 Flash (google-genai SDK) |
| PDF | pdfplumber, jsPDF |
| Deploy | Vercel (Frontend) + Render (Backend) |

---

## 🔄 How It Works

1. User uploads a **Job Description** (and optional Resume)
2. Backend creates a session and parses document context
3. WebSocket connection established
4. AI Interviewer introduces itself with a dynamic persona
5. Candidate speaks → converted to text via STT
6. Text sent to backend → passed to Gemini with full conversation history
7. Gemini generates the next context-aware question
8. Response converted to audio via TTS and streamed back
9. Loop continues until interview ends
10. Final report generated: Strengths, Weaknesses, JD Match Score, PDF export

---

## 🧪 Running Locally

### Prerequisites
- Node.js >= 18
- Python >= 3.9
- Google Gemini API Key → https://makersuite.google.com/app/apikey

### 1. Clone the repo

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Backend Setup

```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `Backend/.env`:
API_KEY=your_google_gemini_api_key

Run:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd Frontend/interviewer
npm install
```

Create `Frontend/interviewer/.env`:
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

Run:
```bash
npm run dev
```

---

## 🌐 Environment Variables

| File | Variable | Description |
|---|---|---|
| `Backend/.env` | `API_KEY` | Google Gemini API key |
| `Frontend/.env` | `NEXT_PUBLIC_BACKEND_URL` | FastAPI backend URL |

---

## ⚠️ Current Limitations

- In-memory session storage (not persistent)
- No database integration
- No user authentication
- Single-instance WebSocket handling

---

## 🔮 Roadmap

- [ ] Redis / DB-based persistent sessions
- [ ] Recruiter analytics dashboard
- [ ] User authentication
- [ ] Multi-language interview support
- [ ] Video interview mode
- [ ] Horizontal scaling support

---

## 🎯 Unique Value Proposition

- 🎯 Domain-agnostic — works for any subject, not just coding
- 🎤 Fully voice-driven interaction
- 🧠 Adaptive questioning using full conversation context
- ⚡ Real-time WebSocket-based experience
- 📄 Evaluation grounded in the actual JD

---
