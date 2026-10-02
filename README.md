# 🎓 VocGuide — AI Career Counselling & Family Decision-Support Platform

**SIH 2026 | Problem Statement ID: 26241**

An AI-enabled career counselling platform for vocational education in India, designed to engage **both learners AND their families** together, addressing parental concerns with verified data and regional language support.

---

## 🚀 Quick Start

### 1. Install Python dependencies
```bash
pip install flask flask-cors requests
```

### 2. Start Ollama (AI model)
```bash
ollama serve
# Ensure mannix/llama3.1-8b-lexi and translategemma models are available
```

### 3. Start VocGuide
```bash
python app.py
# Or double-click: start.bat
```

### 4. Open in browser
```
http://localhost:5000
```

---

## 🗂️ Project Structure

```
SIHProject/
├── app.py                  # Flask backend (API + AI integration)
├── requirements.txt        # Python dependencies
├── start.bat              # One-click startup script
├── data/
│   └── trades.json        # Verified trade data (8 trades)
└── static/
    ├── index.html         # Main frontend (4 sections)
    ├── style.css          # Premium dark theme CSS
    └── app.js             # Frontend JavaScript + API calls
```

---

## ✨ Features

### 🤖 AI Family Counsellor
- Powered by **Ollama (mannix/llama3.1-8b-lexi)** running locally
- Addresses both **learner AND parent** questions in one session
- Responds with **verified NSQF/ITI data** — not generic content
- Detects sentiment shifts (positive / neutral / concerned) in real-time
- Suggests human counsellor escalation when needed

### 🌐 Multilingual Support (Hindi + English)
- Full UI translation between English and Hindi
- Chat works in both languages (auto-detected from user input)
- Translation powered by **translategemma** model
- Devanagari text rendering with Noto Sans Devanagari font

### 📊 Verified Trade Data (8 Trades)
| Trade | NSQF | Avg Salary | Placement |
|-------|------|-----------|-----------|
| Electrician | 3 | ₹28,000/mo | 87% |
| Computer Operator | 4 | ₹25,000/mo | 88% |
| Healthcare Assistant | 4 | ₹20,000/mo | 93% |
| Beauty & Wellness | 3 | ₹20,000/mo | 91% |
| Plumber | 3 | ₹22,000/mo | 82% |
| Welder | 3 | ₹25,000/mo | 84% |
| Automobile Technician | 4 | ₹24,000/mo | 86% |
| Sewing Technology | 2 | ₹18,000/mo | 79% |

### 📈 Admin Dashboard
- **KPI cards**: Sessions, messages, escalations, sentiment %
- **Session trend chart**: 7-day SVG line chart
- **Sentiment donut chart**: Canvas-rendered distribution
- **Resistance concentration map**: Where/why families resist
- **Session monitor**: Live table of all counselling sessions
- **Escalation queue**: Manage human counsellor callbacks

### ☎️ Human Escalation
- One-click request for human counsellor callback
- Session context (trade, concerns, sentiment) carried over
- Admin can track and resolve escalation requests
- Toll-free number shown for direct contact

### ♿ Accessibility Features
- Large, readable font sizes
- High contrast dark theme
- Voice input support (Web Speech API)
- Simple UI with icons for low-literacy users
- Mobile responsive design

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trades` | List all trades |
| GET | `/api/trades/<id>` | Get trade details |
| GET | `/api/providers` | Training providers |
| GET | `/api/schemes` | Government schemes |
| POST | `/api/sessions` | Create counselling session |
| POST | `/api/chat` | Send message to AI |
| POST | `/api/translate` | Translate text |
| POST | `/api/escalate` | Request human counsellor |
| GET | `/api/admin/stats` | Admin dashboard data |
| GET | `/api/admin/sessions` | All sessions |
| GET | `/api/admin/escalations` | Escalation requests |
| GET | `/api/admin/resistance-map` | Resistance data by location |
| GET | `/api/ollama/status` | AI model status |

---

## 🎯 Addressing Problem Requirements

| Requirement | Implementation |
|-------------|----------------|
| Engage learners + parents jointly | Session context captures both; AI prompted for family counselling |
| Regional language support | Hindi + English with `translategemma` model |
| Verified outcome data | `trades.json` with placement rates, salaries, NSQF levels |
| NSQF qualification pathway | Career progression shown in trade detail modal |
| Human escalation | Dedicated escalation modal + admin queue |
| Engagement/sentiment tracking | Per-message sentiment analysis + admin dashboard |
| Low-literacy design | Icon-heavy UI, large text, voice input |
| Admin resistance map | Location × concern-topic concentration visualization |

---

## 🛠️ Tech Stack

- **Backend**: Python 3.14 + Flask + Flask-CORS
- **AI**: Ollama (mannix/llama3.1-8b-lexi for chat, translategemma for translation)
- **Frontend**: Vanilla HTML5/CSS3/JavaScript (no framework)
- **Fonts**: Inter + Noto Sans Devanagari (Google Fonts)
- **Data**: JSON-based trade database (easily replaceable with real NSDC data)

---

## 🔒 Data Privacy

- All sessions stored in-memory (not persisted to disk)
- No personal data stored beyond the session
- Escalation requests store only name and phone (as provided)
- Ollama runs fully locally — no cloud API calls

---

*Built for Smart India Hackathon 2026 — Ministry of Skill Development & Entrepreneurship*
