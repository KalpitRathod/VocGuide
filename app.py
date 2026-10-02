"""
VocGuide v2 — AI Career Counselling & Family Decision-Support Platform
SIH 2026 | Problem Statement 26241

New in v2:
  - SQLite auth (users + admins) with bcrypt-style hashing
  - RAG via bge-m3 + ChromaDB (temporal + semantic memory harness from SmritiCare)
  - Whisper.cpp offline STT (speech-to-text)
  - AI4Bharat IndicTTS (text-to-speech, Hindi + English)
  - WhatsApp-style voice message endpoints
"""

import os, sys, io, json, uuid, re, math, time, hashlib, base64
import sqlite3, threading, tempfile, subprocess, wave
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests as http_requests

# ── stdout fix for Windows cp1252 ─────────────────────────────────────────────
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / 'data'
DB_FILE       = BASE_DIR / 'vocguide.db'
AUDIO_CACHE   = BASE_DIR / 'audio_cache'
MEMORY_DB     = BASE_DIR / 'memory_db'
INDIC_TTS_DIR = BASE_DIR / 'IndicTTS'
TTS_DIR       = BASE_DIR / 'TTS'
TRAINER_DIR   = BASE_DIR / 'Trainer'
WHISPER_CLI   = BASE_DIR / 'Whisper Model' / 'whisper-bin-x64' / 'Release' / 'whisper-cli.exe'
WHISPER_MODEL = BASE_DIR / 'Whisper Model' / 'whisper-bin-x64' / 'Release' / 'ggml-small.bin'

AUDIO_CACHE.mkdir(exist_ok=True)
MEMORY_DB.mkdir(exist_ok=True)

OLLAMA_URL  = "http://127.0.0.1:11434"
CHAT_MODEL  = "mannix/llama3.1-8b-lexi:latest"
EMBED_MODEL = "bge-m3:latest"
XLAT_MODEL  = "translategemma:latest"
AI4BHARAT_TTS_URL = "https://demo-api.models.ai4bharat.org/inference/tts"

# ── Load trade data ────────────────────────────────────────────────────────────
with open(DATA_DIR / 'trades.json', encoding='utf-8') as f:
    _DATA = json.load(f)
TRADES    = {t['id']: t for t in _DATA['trades']}
PROVIDERS = _DATA['training_providers']
SCHEMES   = _DATA['schemes']

# ═══════════════════════════════════════════════════════════════════════════════
# RAG — LangChain + ChromaDB + BGE-M3 (SmritiCare Temporal+Semantic Harness)
# ═══════════════════════════════════════════════════════════════════════════════
RAG_OK = False
embeddings = vector_store = llm = classifier_llm = None

try:
    from langchain_ollama import ChatOllama, OllamaEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage

    embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_URL)
    vector_store = Chroma(
        persist_directory=str(MEMORY_DB),
        embedding_function=embeddings,
        collection_name="vocguide_counselling"
    )
    llm = ChatOllama(model=CHAT_MODEL, temperature=0.55, base_url=OLLAMA_URL)
    classifier_llm = ChatOllama(model=CHAT_MODEL, temperature=0, num_predict=4, base_url=OLLAMA_URL)
    RAG_OK = True
    print("[RAG] ChromaDB + BGE-M3 initialised successfully")
except Exception as e:
    print(f"[RAG] LangChain unavailable, falling back to basic mode: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TEMPORAL + SEMANTIC MEMORY HARNESS  (ported from SmritiCare)
# ═══════════════════════════════════════════════════════════════════════════════
MONTHS = {
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
    "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,
    "sep":9,"sept":9,"oct":10,"nov":11,"dec":12
}
BARE_MONTH_BLOCKLIST = {"may"}

def extract_time_range(query: str):
    now = datetime.now()
    q = query.lower().strip()
    if "today" in q:
        s = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return s, s + timedelta(days=1)
    if "yesterday" in q:
        e = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return e - timedelta(days=1), e
    if "last week" in q:
        monday = now.replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=now.weekday())
        return monday - timedelta(days=7), monday
    if "last month" in q:
        first = now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        if first.month == 1: start = first.replace(year=first.year-1, month=12)
        else: start = first.replace(month=first.month-1)
        return start, first
    m = re.search(r"(?:last|past)\s+(\d+)\s+days?", q)
    if m: return now - timedelta(days=int(m.group(1))), now
    m = re.search(r"(\d+)\s+days?\s+ago", q)
    if m:
        t = now.replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=int(m.group(1)))
        return t, t + timedelta(days=1)
    for mn, num in MONTHS.items():
        if mn in BARE_MONTH_BLOCKLIST: continue
        if re.search(rf"\b{mn}\b", q):
            s = datetime(now.year, num, 1)
            e = datetime(now.year+1, 1, 1) if num==12 else datetime(now.year, num+1, 1)
            return s, e
    return None, None

def remove_temporal_words(query: str) -> str:
    patterns = [
        r"\btoday\b",r"\byesterday\b",r"\btomorrow\b",
        r"\blast week\b",r"\bthis week\b",r"\blast month\b",r"\bthis month\b",
        r"\b(?:last|past)\s+\d+\s+days?\b",r"\d+\s+days?\s+ago",
    ]
    t = query
    for p in patterns: t = re.sub(p, "", t, flags=re.IGNORECASE)
    month_pat = "|".join(MONTHS.keys())
    t = re.sub(rf"\b({month_pat})\b", "", t, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", t).strip(" ?.,")

def _cosine_sim(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    return dot/(na*nb) if na and nb else 0.0

def _rank_by_similarity(query_text, items, k):
    if not items or not embeddings: return items[:k]
    try:
        qv = embeddings.embed_query(query_text)
        dvs = embeddings.embed_documents([c for c,_ in items])
        scored = [(_cosine_sim(qv,v), c, m) for (c,m),v in zip(items,dvs)]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [(c,m) for _,c,m in scored[:k]]
    except Exception as e:
        print(f"[rank error: {e}]")
        return items[:k]

def format_memories(items):
    if not items: return None
    total = len(items)
    blocks = []
    for i, (content, meta) in enumerate(items, 1):
        ts = (meta or {}).get("timestamp","Unknown")
        blocks.append(f"--- Memory {i} of {total} (from {ts}) ---\n{content}")
    return "\n\n".join(blocks)

FILLER_MESSAGES = {
    "hi", "hii", "hello", "hey", "yo", "namaste", "pranam",
    "ok", "okay", "k", "kk", "theek hai", "accha", "haan", "ha", "yes", "yep", "no", "nahin", "nahi",
    "thanks", "dhanyawad", "shukriya", "thank you", "bye", "goodbye", "alvida", "sure", "fine"
}

def is_filler(msg: str) -> bool:
    clean = re.sub(r'[^a-zA-Z\u0900-\u097f\s]', '', (msg or '').lower()).strip()
    return clean in FILLER_MESSAGES or len(clean) <= 2

def needs_recall(query: str) -> bool:
    q = query.lower()
    recall_triggers = [
        "pehle", "earlier", "remember", "yaad", "naam", "name", "who", "kya baat", "discussed",
        "told", "pichli", "last time", "kal", "yesterday", "today", "aaj", "kya he", "kya hai",
        "history", "what did we say", "what was that", "mere bare me", "mere ladke"
    ]
    return any(w in q for w in recall_triggers)

def save_to_vector_store(session_id: str, user_input: str, ai_response: str, speaker_role: str = "user", trade_id: str = None):
    if not vector_store: return
    now = datetime.now()
    speaker_tag = f"User ({speaker_role})" if speaker_role and speaker_role != "user" else "User"
    text = f"Date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n{speaker_tag}:\n{user_input}\n\nVocGuide AI:\n{ai_response}"
    meta = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": float(now.timestamp()),
        "date": now.strftime("%Y-%m-%d"),
        "year": now.year, "month": now.month, "day": now.day,
        "session_id": session_id,
        "speaker_role": speaker_role or "user",
        "trade_id": trade_id or "",
        "type": "conversation"
    }
    try:
        vector_store.add_texts(texts=[text], metadatas=[meta])
    except Exception as e:
        print(f"[vector_store add error: {e}]")

def recall_from_vector_store(session_id: str, user_query: str, k: int = 5):
    """Temporal + Semantic retrieval with SQLite fallback and recall gating."""
    if not user_query or is_filler(user_query):
        return ""
    if not vector_store:
        return _sqlite_recall(session_id, k) if needs_recall(user_query) else ""
    try:
        start_time, end_time = extract_time_range(user_query)
        semantic_query = remove_temporal_words(user_query) or user_query

        if start_time is None:
            # Check if recall is relevant
            if not needs_recall(user_query) and len(user_query.split()) < 3:
                return ""
            try:
                docs = vector_store.similarity_search(semantic_query, k=k+5, filter={"session_id": session_id})
                items = [(d.page_content, d.metadata) for d in docs]
            except Exception:
                docs = vector_store.similarity_search(semantic_query, k=k+8)
                items = [(d.page_content, d.metadata) for d in docs
                         if (d.metadata or {}).get("session_id") == session_id]
            items.sort(key=lambda p: p[1].get("epoch", 0) if isinstance(p[1], dict) else 0, reverse=True)
            return format_memories(items[:k]) or ""
        else:
            # Time-bounded query
            start_ep = float(start_time.timestamp())
            end_ep   = float(end_time.timestamp())
            tf = {"$and": [{"epoch": {"$gte": start_ep}}, {"epoch": {"$lt": end_ep}}]}
            raw = vector_store._collection.get(where=tf, include=["documents", "metadatas"])
            items = list(zip(raw.get("documents", []), raw.get("metadatas", [])))
            items = [p for p in items if (p[1] or {}).get("session_id") == session_id]
            if semantic_query:
                items = _rank_by_similarity(semantic_query, items, k)
            else:
                items.sort(key=lambda p: p[1].get("epoch", 0) if isinstance(p[1], dict) else 0, reverse=True)
                items = items[:k]
            return format_memories(items) or ""
    except Exception as e:
        print(f"[recall error: {e}]")
        return _sqlite_recall(session_id, k)

def _sqlite_recall(session_id: str, k: int):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT role, message, created_at FROM messages WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
            (session_id, k)
        ).fetchall()
        if not rows: return ""
        items = [(f"{'User' if r['role']=='user' else 'VocGuide'}: {r['message']}", {"timestamp": r['created_at']}) for r in rows]
        return format_memories(items) or ""
    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
# WHISPER OFFLINE STT
# ═══════════════════════════════════════════════════════════════════════════════
def transcribe_audio_whisper(audio_bytes: bytes, lang: str = "en") -> str:
    """Transcribe audio using whisper.cpp CLI. Returns plain text."""
    if not WHISPER_CLI.exists() or not WHISPER_MODEL.exists():
        return ""
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
            tf.write(audio_bytes)
            tmp_path = tf.name

        lang_code = "hi" if lang in ("hi","hindi") else "en"
        cmd = [
            str(WHISPER_CLI),
            "-m", str(WHISPER_MODEL),
            "-f", tmp_path,
            "-l", lang_code,
            "--no-timestamps",
            "-otxt"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30, text=True, encoding='utf-8', errors='replace')
        # whisper-cli writes to .txt alongside input file
        txt_path = tmp_path.replace('.wav', '.wav.txt')
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read().strip()
            os.unlink(txt_path)
        else:
            text = result.stdout.strip()
        os.unlink(tmp_path)
        return text
    except Exception as e:
        print(f"[Whisper STT error: {e}]")
        return ""

# ═══════════════════════════════════════════════════════════════════════════════
# INDIC TTS  (AI4Bharat + local IndicTTS fallback)
# ═══════════════════════════════════════════════════════════════════════════════
LANG_TO_CODE = {
    "hindi":"hi","hi":"hi","english":"en","en":"en",
    "marathi":"mr","mr":"mr","bengali":"bn","bn":"bn",
    "tamil":"ta","ta":"ta","telugu":"te","te":"te",
    "kannada":"kn","kn":"kn","malayalam":"ml","ml":"ml",
    "gujarati":"gu","gu":"gu","punjabi":"pa","pa":"pa",
}
CODE_TO_MODEL = {
    "hi":"ai4bharat/indic-tts-indo-aryan--gpu-t4",
    "mr":"ai4bharat/indic-tts-indo-aryan--gpu-t4",
    "bn":"ai4bharat/indic-tts-indo-aryan--gpu-t4",
    "gu":"ai4bharat/indic-tts-indo-aryan--gpu-t4",
    "pa":"ai4bharat/indic-tts-indo-aryan--gpu-t4",
    "ta":"ai4bharat/indic-tts-dravidian--gpu-t4",
    "te":"ai4bharat/indic-tts-dravidian--gpu-t4",
    "kn":"ai4bharat/indic-tts-dravidian--gpu-t4",
    "ml":"ai4bharat/indic-tts-dravidian--gpu-t4",
    "en":"ai4bharat/indic-tts-misc--gpu-t4",
}
_TTS_CACHE = {}
_TTS_LOCK  = threading.Lock()

def _get_local_synthesizer(lang_code: str):
    with _TTS_LOCK:
        if lang_code in _TTS_CACHE:
            return _TTS_CACHE[lang_code]
        model_path   = INDIC_TTS_DIR / lang_code / "fastpitch" / "best_model.pth"
        config_path  = INDIC_TTS_DIR / lang_code / "fastpitch" / "config.json"
        vocoder_path = INDIC_TTS_DIR / lang_code / "hifigan"   / "best_model.pth"
        vocoder_cfg  = INDIC_TTS_DIR / lang_code / "hifigan"   / "config.json"
        speakers_pth = INDIC_TTS_DIR / lang_code / "fastpitch" / "speakers.pth"
        if not model_path.exists() or not config_path.exists():
            _TTS_CACHE[lang_code] = None
            return None
        try:
            for p in [str(TTS_DIR), str(TRAINER_DIR)]:
                if p not in sys.path and Path(p).exists():
                    sys.path.insert(0, p)
            from TTS.utils.synthesizer import Synthesizer
            syn = Synthesizer(
                tts_checkpoint=str(model_path),
                tts_config_path=str(config_path),
                tts_speakers_file=str(speakers_pth) if speakers_pth.exists() else None,
                vocoder_checkpoint=str(vocoder_path) if vocoder_path.exists() else None,
                vocoder_config=str(vocoder_cfg) if vocoder_cfg.exists() else None,
                use_cuda=False
            )
            _TTS_CACHE[lang_code] = syn
            print(f"[TTS] Loaded in-memory synthesizer for '{lang_code}'")
            return syn
        except Exception as e:
            print(f"[TTS] Local TTS load error for {lang_code}: {e}")
            _TTS_CACHE[lang_code] = None
            return None

def synthesize_speech(text: str, lang: str = "en", gender: str = "female") -> dict:
    """Returns dict with audioContent (base64 WAV) or offline_mode=True."""
    clean = re.sub(r"[*_#`~\[\]]", "", text.strip())
    if not clean: return {"offline_mode": True}
    lang_code  = LANG_TO_CODE.get(lang.lower(), "en")
    gender_str = "male" if gender.lower() == "male" else "female"
    model_name = CODE_TO_MODEL.get(lang_code, "ai4bharat/indic-tts-misc--gpu-t4")
    cache_key  = hashlib.md5(f"{lang_code}:{gender_str}:{clean}".encode()).hexdigest()
    cache_file = AUDIO_CACHE / f"{cache_key}.wav"

    # 1. Disk cache hit
    if cache_file.exists() and cache_file.stat().st_size > 100:
        return {"audioContent": base64.b64encode(cache_file.read_bytes()).decode(), "format":"audio/wav", "cached":True, "language":lang_code}

    # 2. Local in-memory neural TTS
    syn = _get_local_synthesizer(lang_code)
    if syn:
        try:
            wav = syn.tts(clean, speaker_name=gender_str)
            if wav:
                syn.save_wav(wav, str(cache_file))
                if cache_file.exists() and cache_file.stat().st_size > 100:
                    return {"audioContent": base64.b64encode(cache_file.read_bytes()).decode(), "format":"audio/wav", "cached":False, "language":lang_code}
        except Exception as e:
            print(f"[TTS local error: {e}]")

    # 3. AI4Bharat remote API (fast 3.5s timeout)
    payload = {
        "controlConfig":{"dataTracking":True},
        "input":[{"source":clean}],
        "config":{"gender":gender_str,"language":{"sourceLanguage":lang_code}}
    }
    try:
        r = http_requests.post(AI4BHARAT_TTS_URL, json=payload, timeout=3.5)
        r.raise_for_status()
        rd = r.json()
        if "audio" in rd and rd["audio"]:
            b64 = rd["audio"][0].get("audioContent","")
            if b64:
                wav_bytes = base64.b64decode(b64)
                cache_file.write_bytes(wav_bytes)
                return {"audioContent":b64,"format":"audio/wav","cached":False,"language":lang_code,"model":model_name}
    except Exception as e:
        print(f"[TTS AI4Bharat timeout/error: {e}]")

    return {"offline_mode":True,"language":lang_code,"text":clean}

# ═══════════════════════════════════════════════════════════════════════════════
# SQLite DATABASE  — Auth + Sessions + Messages + Admin
# ═══════════════════════════════════════════════════════════════════════════════
def get_db():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'user',
        email TEXT,
        phone TEXT,
        location TEXT,
        created_at TEXT,
        last_login TEXT,
        is_active INTEGER DEFAULT 1
    )""")

    # Sessions table
    c.execute("""CREATE TABLE IF NOT EXISTS counselling_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT,
        learner_name TEXT,
        location TEXT,
        education TEXT,
        family_income TEXT,
        trade_id TEXT,
        parent_concerned TEXT,
        language TEXT DEFAULT 'en',
        created_at TEXT,
        updated_at TEXT,
        status TEXT DEFAULT 'active'
    )""")

    # Messages table
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_id TEXT,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        sentiment TEXT DEFAULT 'neutral',
        concern_topic TEXT,
        language TEXT DEFAULT 'en',
        has_audio INTEGER DEFAULT 0,
        audio_cache_key TEXT,
        created_at TEXT
    )""")

    # Escalations table
    c.execute("""CREATE TABLE IF NOT EXISTS escalations (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        user_id TEXT,
        name TEXT,
        phone TEXT,
        concern TEXT,
        trade_id TEXT,
        location TEXT,
        sentiment TEXT,
        status TEXT DEFAULT 'pending',
        assigned_to TEXT,
        created_at TEXT,
        resolved_at TEXT,
        notes TEXT
    )""")

    # Engagement log
    c.execute("""CREATE TABLE IF NOT EXISTS engagement_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        event TEXT,
        details TEXT,
        created_at TEXT
    )""")

    # Admin settings
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    )""")

    # Seed default admin account
    c.execute("SELECT COUNT(*) as n FROM users WHERE role='admin'")
    if c.fetchone()['n'] == 0:
        c.execute("""INSERT INTO users (id,username,password_hash,full_name,role,email,created_at)
                     VALUES (?,?,?,?,?,?,?)""",
                  (str(uuid.uuid4()), 'admin', _hash_password('admin123'),
                   'VocGuide Administrator', 'admin', 'admin@vocguide.in',
                   datetime.now().isoformat()))
        print("[DB] Default admin created — username: admin, password: admin123")

    # Schema migrations (safe)
    for tbl, col, defval in [
        ("messages","has_audio","0"),
        ("messages","audio_cache_key","NULL"),
        ("messages","speaker_role","'user'"),
        ("escalations","assigned_to","NULL"),
        ("escalations","notes","NULL"),
    ]:
        try: c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT {defval}")
        except: pass

    # Session facts table (SmritiCare-grade deterministic memory)
    c.execute("""CREATE TABLE IF NOT EXISTS session_facts (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        category TEXT NOT NULL,
        fact_key TEXT NOT NULL,
        fact_value TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        last_mentioned_at TEXT,
        created_at TEXT
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_session_facts ON session_facts (session_id, fact_key)")

    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
# SMRITICARE-STYLE FACT EXTRACTION & EPISODIC PERSONA MEMORY
# ═══════════════════════════════════════════════════════════════════════════════
def upsert_session_fact(cursor, session_id: str, category: str, key: str, value: str, confidence: float = 1.0):
    now = datetime.now().isoformat()
    cursor.execute(
        "SELECT id FROM session_facts WHERE session_id=? AND LOWER(fact_key)=LOWER(?)",
        (session_id, key)
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE session_facts SET fact_value=?, category=?, confidence=?, last_mentioned_at=? WHERE id=?",
            (value, category, confidence, now, row['id'])
        )
        return False
    else:
        fid = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO session_facts (id, session_id, category, fact_key, fact_value, confidence, last_mentioned_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (fid, session_id, category, key, value, confidence, now, now)
        )
        return True

def get_session_facts(cursor, session_id: str) -> dict:
    cursor.execute("SELECT category, fact_key, fact_value FROM session_facts WHERE session_id=?", (session_id,))
    rows = cursor.fetchall()
    facts = {}
    for r in rows:
        facts[r['fact_key'].lower()] = r['fact_value']
    return facts

def extract_family_and_session_facts(session_id: str, user_message: str, session: dict, cursor):
    """
    Extracts learner name, family speaker transitions (Father, Mother, Learner),
    trade interest, and parental concerns from natural conversational messages.
    Ported and adapted from SmritiCare's auto_extract_facts architecture.
    """
    if not user_message or len(user_message.strip()) < 1:
        return {}
    
    msg = user_message.strip()
    low = msg.lower()
    extracted = {}
    now = datetime.now().isoformat()
    
    # 1. SPEAKER ROLE & PERSONA DETECTION
    if any(re.search(pat, low) for pat in [
        r'\b(?:me|main|mai|hum)\s+.*(?:pita|pitaji|father|baap|dad|papa)\b',
        r'\b(?:pita|pitaji|father|papa)\s+(?:baat\s+kar\s+raha|bol\s+raha)\b',
        r'\b(?:me|mai)\s+([a-zA-Z\u0900-\u097f]+)\s+ka\s+(?:pita|pitaji|baap|father)\b',
        r'\bmera\s+(?:ladka|beta|putra|bacha)\b',
        r'\bmere\s+(?:ladke|bete|putra|bache)\b',
        r'\bmy\s+son\b',
        r'\bi\s+am\s+(?:his|the)?\s*father\b'
    ]):
        extracted['speaker_role'] = 'father'
        upsert_session_fact(cursor, session_id, 'family', 'speaker_role', 'father')
        # Check if learner name is in sentence: e.g. "me Kalpit ka pita"
        m = re.search(r'\b(?:me|main|mai)\s+([a-zA-Z\u0900-\u097f]+)\s+ka\s+(?:pita|pitaji|father)\b', low)
        if m:
            cname = m.group(1).capitalize()
            if cname.lower() not in ['unka', 'iska', 'apne', 'mera']:
                extracted['learner_name'] = cname
                upsert_session_fact(cursor, session_id, 'identity', 'learner_name', cname)
                session['learner_name'] = cname

    elif any(re.search(pat, low) for pat in [
        r'\b(?:me|main|mai|hum)\s+.*(?:mata|mummy|mother|maa)\b',
        r'\b(?:mata|mummy|mother|maa)\s+(?:baat\s+kar\s+rahi|bol\s+rahi)\b',
        r'\b(?:me|mai)\s+([a-zA-Z\u0900-\u097f]+)\s+ki\s+(?:mata|mummy|mother|maa)\b',
        r'\bmeri\s+(?:beti|ladki|bache)\b',
        r'\bmy\s+daughter\b',
        r'\bi\s+am\s+(?:his|her|the)?\s*mother\b'
    ]):
        extracted['speaker_role'] = 'mother'
        upsert_session_fact(cursor, session_id, 'family', 'speaker_role', 'mother')

    elif any(re.search(pat, low) for pat in [
        r'\b(?:me|main|mai)\s+([a-zA-Z\u0900-\u097f]+)\s+(?:bol\s+raha|baat\s+kar\s+raha)\b',
        r'\bi\s+am\s+the\s+student\b',
        r'\bi\s+am\s+learner\b'
    ]):
        extracted['speaker_role'] = 'learner'
        upsert_session_fact(cursor, session_id, 'family', 'speaker_role', 'learner')

    # 2. LEARNER NAME DETECTION
    m_name = re.search(r'\b(?:mera\s+naam|my\s+name\s+is|i\s+am|naam\s+hai)\s+([a-zA-Z\u0900-\u097f]+)', msg, re.I)
    if m_name:
        cand = m_name.group(1).strip()
        if cand.lower() not in ['kya', 'hai', 'vocguide', 'what', 'learner', 'student']:
            extracted['learner_name'] = cand.capitalize()
            upsert_session_fact(cursor, session_id, 'identity', 'learner_name', cand.capitalize())
            session['learner_name'] = cand.capitalize()
    
    # Or single-word name answer if previous bot turn asked for name
    if len(msg.split()) <= 2 and not any(ch in msg for ch in ['?', '!', '/', '\\', ':']) and len(msg) >= 3:
        cursor.execute("SELECT message FROM messages WHERE session_id=? AND role='assistant' ORDER BY created_at DESC LIMIT 1", (session_id,))
        last_bot = cursor.fetchone()
        if last_bot:
            bot_text = (last_bot['message'] or '').lower()
            if any(k in bot_text for k in ['aapka naam', 'your name', 'naam kya', 'what is your name']):
                cand = msg.strip().title()
                if cand.lower() not in ['nahi', 'no', 'hello', 'hi', 'kuch nahi']:
                    extracted['learner_name'] = cand
                    upsert_session_fact(cursor, session_id, 'identity', 'learner_name', cand)
                    session['learner_name'] = cand

    # 3. TRADE RECOGNITION
    trade_match = None
    if any(k in low for k in ['fabrication', 'welder', 'welding', 'वेल्डर', 'फैब्रिकेशन', 'लोहा']):
        trade_match = 'welder'
    elif any(k in low for k in ['electrician', 'electrical', 'bijli', 'wiring', 'इलेक्ट्रीशियन', 'बिजली']):
        trade_match = 'electrician'
    elif any(k in low for k in ['copa', 'computer', 'data entry', 'programming', 'कंप्यूटर']):
        trade_match = 'computer_operator'
    elif any(k in low for k in ['plumber', 'plumbing', 'pipe', 'fitting', 'नल', 'प्लम्बर']):
        trade_match = 'plumber'
    elif any(k in low for k in ['beauty', 'parlour', 'wellness', 'makeup', 'ब्यूटी']):
        trade_match = 'beauty_wellness'
    elif any(k in low for k in ['auto', 'car', 'motor', 'mechanic', 'automobile', 'ऑटोमोबाइल']):
        trade_match = 'automobile_service'
    elif any(k in low for k in ['hospital', 'gda', 'nurse', 'health', 'healthcare', 'स्वास्थ्य']):
        trade_match = 'healthcare_assistant'
    elif any(k in low for k in ['sewing', 'tailor', 'dress', 'cloth', 'सिलाई', 'दर्जी']):
        trade_match = 'sewing_technology'
    
    if trade_match:
        extracted['trade_id'] = trade_match
        upsert_session_fact(cursor, session_id, 'trade', 'trade_id', trade_match)
        session['trade_id'] = trade_match

    # 4. PARENTAL CONCERNS
    concerns = []
    if any(k in low for k in ['risk', 'safety', 'danger', 'chot', 'accident', 'suraksha', 'khatra', 'pain', 'physical pain', 'dard', 'health', 'toxic', 'fumes', 'aankh', 'problem']):
        concerns.append("Physical Safety, Health Hazards & Strain")
    if any(k in low for k in ['salary', 'income', 'earn', 'paisa', 'kamai', 'veytan', 'rupaye', 'kharcha']):
        concerns.append("Earning Potential & Livelihood")
    if any(k in low for k in ['status', 'respect', 'samaj', 'izzat', 'society', 'dignity']):
        concerns.append("Social Status & Dignity of Labor")
    if any(k in low for k in ['degree', 'b.tech', 'diploma', 'future', 'bhavishya', 'career growth']):
        concerns.append("Career Progression & Degree Mobility")
        
    if concerns:
        c_str = ", ".join(concerns)
        extracted['concerns'] = c_str
        upsert_session_fact(cursor, session_id, 'concerns', 'active_concerns', c_str)
        session['parent_concerned'] = c_str

    cursor.execute("""
        UPDATE counselling_sessions 
        SET learner_name = COALESCE(NULLIF(?, ''), learner_name),
            trade_id = COALESCE(NULLIF(?, ''), trade_id),
            parent_concerned = COALESCE(NULLIF(?, ''), parent_concerned),
            updated_at = ?
        WHERE session_id = ?
    """, (session.get('learner_name', ''), session.get('trade_id', ''), session.get('parent_concerned', ''), now, session_id))

    return extracted

# ═══════════════════════════════════════════════════════════════════════════════
# OLLAMA HELPERS (Multi-turn dialogue support)
# ═══════════════════════════════════════════════════════════════════════════════
def ollama_chat(messages_or_prompt, system: str = "", model: str = CHAT_MODEL, temperature: float = 0.55, num_predict: int = 400) -> str:
    if isinstance(messages_or_prompt, list):
        msgs = messages_or_prompt
    else:
        msgs = []
        if system: msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": str(messages_or_prompt)})
    try:
        payload = {
            "model": model,
            "messages": msgs,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict
            }
        }
        r = http_requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()['message']['content'].strip()
    except Exception as e:
        print(f"[Ollama chat error: {e}]", file=sys.stderr)
        return f"[AI unavailable: {e}]"

def is_hindi(text: str) -> bool:
    return sum(1 for c in text if '\u0900' <= c <= '\u097F') > 3

def detect_sentiment(text: str) -> str:
    concern = ['worried','scared','doubt','no','bad','low','risk','danger',
               'chinta','dar','nahin','kharab','\u091a\u093f\u0902\u0924\u093e','\u0921\u0930','problem','pain']
    pos     = ['good','great','yes','interested','excited','helpful',
               'accha','haan','behtar','\u0905\u091a\u094d\u091b\u093e','\u0939\u093e\u0901']
    tl = text.lower()
    cc = sum(1 for w in concern if w in tl)
    pc = sum(1 for w in pos    if w in tl)
    return "concerned" if cc > pc else ("positive" if pc > 0 else "neutral")

def detect_concern_topic(text: str) -> str:
    tl = text.lower()
    if any(w in tl for w in ['salary','money','earn','income','pay','paisa','kamai','वेतन']): return "income"
    if any(w in tl for w in ['safe','danger','risk','accident','suraksha','खतरा','pain','health']): return "safety"
    if any(w in tl for w in ['status','respect','society','maan','izzat','इज्जत']): return "social_status"
    if any(w in tl for w in ['future','growth','career','degree','bhavishy','भविष्य']): return "career_growth"
    return "general"

def build_counsellor_prompt(session: dict, facts: dict, memories: str, target_lang: str = None) -> str:
    now_dt = datetime.now()
    now_str = now_dt.strftime("%A, %d %B %Y, %I:%M %p")
    
    learner_name = facts.get('learner_name') or session.get('learner_name') or ''
    speaker_role = facts.get('speaker_role') or 'learner'
    trade_id = facts.get('trade_id') or session.get('trade_id')
    concerns = facts.get('active_concerns') or session.get('parent_concerned') or 'General vocational enquiry'
    
    if not target_lang:
        target_lang = session.get('language') or 'en'
    is_english = (target_lang == 'en')
    
    # Speaker title & guideline
    if speaker_role == 'father':
        speaker_title = f"{learner_name + '\'s' if learner_name else 'Learner\'s'} Father (पिता जी)"
        if is_english:
            speaker_guideline = f"""
CURRENT SPEAKER: {speaker_title}.
YOU ARE SPEAKING DIRECTLY TO THE FATHER RIGHT NOW!
- Greet him with high cultural respect: "Respected Father" or "Namaste Sir".
- DO NOT ask him if you should talk to his son! You are speaking directly with the father.
- Validate his protective paternal feelings immediately: acknowledge that worrying about his child's safety, eyesight, physical strain, and health is 100% natural and shows loving, responsible parenting.
- Address his exact doubts directly, calmly, and authoritatively in English:
  * In modern NCVT/ITI training and organized industries (Tata Steel, L&T, Indian Railways, BHEL), comprehensive safety PPE is mandatory: auto-darkening welding helmets (100% UV/IR protection), heavy-duty leather safety jackets, fume extraction respirators, and steel-toe safety boots.
  * Modern semi-automated MIG/TIG welding, robotic welding, and CNC plasma cutters have eliminated the old-fashioned heavy physical strain and toxic smoke of unorganized roadside workshops.
  * Organized industrial employers provide full ESI medical insurance covering the entire family, provident fund (PF), and regulated 8-hour shifts.
  * Clear upward career ladder: With 2-5 years experience and NSQF progression, the learner advances to Welding Inspector, Quality Control Supervisor, or Workshop In-charge, which are respected supervisory and inspection roles.
- Provide a reassuring, structured explanation in respectful English. Keep answer under 200 words."""
        else:
            speaker_guideline = f"""
CURRENT SPEAKER: {speaker_title}.
YOU ARE SPEAKING DIRECTLY TO THE FATHER RIGHT NOW!
- Greet him with highest Indian cultural respect (e.g. "नमस्ते आदरणीय पिता जी" or "प्रणाम अंकल जी").
- DO NOT ask him if you should talk to his son! You are talking directly with the father right now.
- Validate his protective paternal feelings immediately: acknowledge that worrying about his child's safety, eyesight, physical strain, and health is 100% natural and shows good parenting.
- Address his exact doubts directly and calmly:
  * In modern NCVT/ITI training and organized industries (Tata Steel, L&T, Railways, BHEL), full safety PPE is mandatory: auto-darkening helmets (100% UV/IR eye protection), leather safety jackets, fume extraction respirators, and steel-toe safety boots.
  * Modern semi-automated MIG/TIG welding and CNC plasma machines have eliminated the old-fashioned heavy physical strain and toxic smoke of unorganized roadside workshops.
  * Organized employers provide ESI medical insurance covering the entire family, provident fund (PF), and fixed 8-hour shifts.
  * Clear upward career ladder: With 2-5 years experience and NSQF progression, the learner advances to Welding Inspector, Quality Control Supervisor, or Workshop In-charge, which are respected technical supervisory roles.
- Provide a reassuring, structured explanation in respectful Hindi. Keep answer focused and under 200 words."""
    elif speaker_role == 'mother':
        speaker_title = f"{learner_name + '\'s' if learner_name else 'Learner\'s'} Mother (माता जी)"
        if is_english:
            speaker_guideline = f"""
CURRENT SPEAKER: {speaker_title}.
YOU ARE SPEAKING DIRECTLY TO THE MOTHER RIGHT NOW!
- Address her with deep respect ("Respected Mother" or "Namaste Ma'am").
- Validate her maternal care for her child's wellbeing, safety, and daily comfort.
- Reassure her in English about safe working conditions, government recognized certifications, medical protections (ESI), and a respectable livelihood."""
        else:
            speaker_guideline = f"""
CURRENT SPEAKER: {speaker_title}.
YOU ARE SPEAKING DIRECTLY TO THE MOTHER RIGHT NOW!
- Address her with deep cultural respect ("नमस्ते आदरणीय माता जी").
- Validate her maternal care for her child's wellbeing, safety, and daily comfort.
- Reassure her about safe working conditions, government recognized certifications, medical protections (ESI), and a respectable livelihood."""
    else:
        speaker_title = f"{learner_name} (Learner)" if learner_name else "Learner"
        speaker_guideline = f"""
CURRENT SPEAKER: {speaker_title}.
- Be warm, encouraging, practical, and clear about skill progression, apprenticeships (NAPS), and hands-on career growth.
- Address questions on starting stipends, course duration, and job prospects directly."""

    # Trade ground truth
    if trade_id and trade_id in TRADES:
        t = TRADES[trade_id]
        trade_ground_truth = f"""
SPECIFIC TRADE GROUND TRUTH ({t['name']} / {t.get('name_hi', '')}):
- NSQF Level: {t['nsqf_level']} | Duration: {t['duration_months']} months
- Starting Salary: ₹{t['avg_starting_salary']:,}/month (plus ESI medical coverage & PF in organized companies)
- Experienced (3-5 yr): ₹{t['avg_experienced_salary']:,}/month
- Top Earners: ₹{t['top_salary']:,}/month domestic; certified international/Gulf roles earn ₹60,000–₹1,20,000/month
- Placement Rate: {t['placement_rate']}% | Annual Job Growth: {t['job_growth_percent']}%
- Safety & Physical Risk: {t['safety_rating']} Risk.
- Top Employers: {', '.join(t['top_employers'][:5])}
- Career Progression: {' -> '.join(f"{p['role']} (₹{p['salary']}/mo)" for p in t['career_progression'])}
- Verified Parental Protections: {json.dumps(t['parental_concerns_addressed'], ensure_ascii=False)}"""
    else:
        trade_ground_truth = """
VERIFIED NSQF VOCATIONAL TRADES SUMMARY (OFFICIAL GROUND TRUTH - RECOMMEND ONLY THESE):
1. Electrician (NSQF Level 3-5): Starting ₹12,000–₹16,000/mo, 3-5yr ₹25,000–₹35,000/mo, Top ₹55,000+/mo. (L&T, Tata Projects, Adani, Electrical contractor license).
2. Computer Operator & Programming Assistant (COPA) (NSQF Level 4): Starting ₹10,000–₹15,000/mo, 3-5yr ₹25,000–₹40,000/mo, Top ₹70,000+/mo. (IT Support, BPO, Office automation).
3. Welder & Precision Fabrication (NSQF Level 3-5): Starting ₹11,000–₹16,000/mo, 3-5yr ₹22,000–₹35,000/mo, Top ₹50,000+/mo domestic; Gulf/overseas certified ₹70,000–₹1,20,000/mo. (Tata Steel, BHEL, Railways, L&T).
4. Automobile Service Technician (NSQF Level 4): Starting ₹11,000–₹15,000/mo, 3-5yr ₹22,000–₹35,000/mo, Top ₹55,000+/mo. (Maruti Suzuki, Tata Motors, EV service).
5. Plumber (NSQF Level 3-5): Starting ₹10,000–₹14,000/mo, 3-5yr ₹20,000–₹30,000/mo, Top ₹45,000+/mo, High self-employment potential.
6. General Duty Assistant - Healthcare (NSQF Level 4): Starting ₹9,000–₹14,000/mo, 3-5yr ₹18,000–₹28,000/mo, Top ₹40,000+/mo. (Apollo, AIIMS, Fortis).
7. Beauty & Wellness Technician (NSQF Level 3-5): Starting ₹8,000–₹14,000/mo, 3-5yr ₹20,000–₹35,000/mo, Top ₹60,000+/mo.
8. Sewing Technology & Dress Making (NSQF Level 2-4): Starting ₹7,000–₹12,000/mo, 3-5yr ₹16,000–₹28,000/mo, Top ₹45,000+/mo."""

    if is_english:
        name_instruction = f"- The learner's name is {learner_name}. If asked 'What is my name?' or 'Kya he mera naam?', answer directly and warmly: 'Your name is {learner_name}!'" if learner_name else "- If the user asks 'What is my name?' or 'Kya he mera naam?' and their name is not known yet, warmly reply: 'You haven\'t shared your name yet. Please tell me your name so I can assist you better!'"
        language_rule = "4. CRITICAL OUTPUT LANGUAGE RULE: The user has selected ENGLISH as their output language. You MUST generate your entire response in clear, fluent, professional, empathetic ENGLISH. DO NOT respond in Hindi or Hinglish. Even if the user typed in Hindi, Hinglish, or Devanagari script (e.g., 'kya he mera naam', 'mere pitaji mana kar rahe hai', 'ji me Kalpit ka pita baat kar raha hu'), understand their query fully, but output your response 100% in English."
    else:
        name_instruction = f"- The learner's name is {learner_name}. If asked 'Kya he mera naam?' or 'What is my name?', answer directly and warmly: 'आपका नाम {learner_name} है!'" if learner_name else "- If the user asks 'Kya he mera naam?' or 'What is my name?' and their name is not known yet, warmly reply: 'आपने अभी तक अपना शुभ नाम नहीं बताया है, कृपया बताएं ताकि मैं आपकी बेहतर सहायता कर सकूँ!'"
        language_rule = "4. CRITICAL OUTPUT LANGUAGE RULE: The user has selected HINDI as their output language. You MUST generate your response in respectful, natural, clear HINDI (Devanagari script or standard Hindi). Even if the user typed in English, understand their query and output your response in HINDI."

    mem_block = f"\nRELEVANT PAST CONVERSATION MEMORIES:\n{memories}\n" if memories and memories.strip() else ""

    return f"""You are VocGuide, a compassionate, highly knowledgeable AI Vocational Career and Family Counsellor for India's Vocational Education System (NSQF & NCVT aligned).

Right now, the actual current date and time is: {now_str}.
Use this as ground truth whenever someone mentions today, yesterday, tomorrow, dates, or time of day.

KNOWN FAMILY PROFILE:
- Learner Name: {learner_name or 'Not specified yet'}
- Active Speaker: {speaker_title}
- Target Trade: {trade_id or 'General exploration'}
- Active Concerns: {concerns}
- Location: {session.get('location') or 'Not specified'}

{trade_ground_truth}
{mem_block}
{speaker_guideline}

CRITICAL RULES:
1. NEVER recommend university academic degrees (e.g. Software Engineering B.Tech, Computer Aerodynamics, or Data Science Masters). You are advising on vocational / ITI / NSQF trade skilling.
2. {name_instruction}
3. Maintain conversational coherence: do not start messages with repetitive praise or canned templates. Speak naturally, empathetically, and intelligently.
{language_rule}"""

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def get_user_from_token(token: str):
    """Simple token = base64(user_id:timestamp). For demo — use JWT in production."""
    if not token: return None
    try:
        decoded = base64.b64decode(token).decode()
        uid = decoded.split(':')[0]
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE id=? AND is_active=1", (uid,)).fetchone()
        conn.close()
        return dict(row) if row else None
    except: return None

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Auth-Token') or request.args.get('token')
        user = get_user_from_token(token)
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

def make_token(user_id: str) -> str:
    payload = f"{user_id}:{int(time.time())}"
    return base64.b64encode(payload.encode()).decode()

# ═══════════════════════════════════════════════════════════════════════════════
# STATIC FILES
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/')
def serve_index(): return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path): return send_from_directory('static', path)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH API
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/auth/register', methods=['POST'])
def register():
    b = request.json or {}
    username = (b.get('username') or '').strip()
    password = (b.get('password') or '').strip()
    full_name = (b.get('full_name') or '').strip()
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    conn = get_db()
    if conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
        conn.close()
        return jsonify({'error': 'Username already taken'}), 409
    uid = str(uuid.uuid4())
    conn.execute("""INSERT INTO users (id,username,password_hash,full_name,role,email,phone,location,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                 (uid, username, _hash_password(password), full_name, 'user',
                  b.get('email',''), b.get('phone',''), b.get('location',''),
                  datetime.now().isoformat()))
    conn.commit(); conn.close()
    token = make_token(uid)
    return jsonify({'token': token, 'user_id': uid, 'role': 'user', 'username': username})

@app.route('/api/auth/login', methods=['POST'])
def login():
    b = request.json or {}
    username = (b.get('username') or '').strip()
    password = (b.get('password') or '').strip()
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,)).fetchone()
    if not row or row['password_hash'] != _hash_password(password):
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401
    uid = row['id']
    conn.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now().isoformat(), uid))
    conn.commit(); conn.close()
    token = make_token(uid)
    return jsonify({'token': token, 'user_id': uid, 'role': row['role'],
                    'username': row['username'], 'full_name': row['full_name']})

@app.route('/api/auth/me', methods=['GET'])
def me():
    token = request.headers.get('X-Auth-Token')
    user = get_user_from_token(token)
    if not user: return jsonify({'error': 'Not authenticated'}), 401
    safe = {k: user[k] for k in ['id','username','full_name','role','email','phone','location','created_at']}
    return jsonify(safe)

# ═══════════════════════════════════════════════════════════════════════════════
# TRADES / PROVIDERS / SCHEMES
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/trades', methods=['GET'])
def get_trades():
    result = list(TRADES.values())
    sector = request.args.get('sector')
    if sector: result = [t for t in result if sector.lower() in t['sector'].lower()]
    return jsonify(result)

@app.route('/api/trades/<tid>', methods=['GET'])
def get_trade(tid):
    if tid not in TRADES: return jsonify({'error':'Not found'}), 404
    return jsonify(TRADES[tid])

@app.route('/api/providers', methods=['GET'])
def get_providers():
    res = PROVIDERS
    state = request.args.get('state')
    trade = request.args.get('trade')
    if state: res = [p for p in res if state.lower() in p['state'].lower()]
    if trade: res = [p for p in res if trade in p.get('trades_offered',[])]
    return jsonify(res)

@app.route('/api/schemes', methods=['GET'])
def get_schemes(): return jsonify(SCHEMES)

# ═══════════════════════════════════════════════════════════════════════════════
# COUNSELLING SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/sessions', methods=['POST'])
def create_session():
    b = request.json or {}
    sid = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    token = request.headers.get('X-Auth-Token')
    user  = get_user_from_token(token)
    uid   = user['id'] if user else None
    conn = get_db()
    conn.execute("""INSERT INTO counselling_sessions
        (session_id,user_id,learner_name,location,education,family_income,trade_id,parent_concerned,language,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (sid, uid, b.get('learner_name',''), b.get('location',''),
         b.get('education',''), b.get('family_income',''),
         b.get('trade_id'), b.get('parent_concerned',''),
         b.get('language','en'), now, now))
    conn.execute("INSERT INTO engagement_log (session_id,event,details,created_at) VALUES (?,?,?,?)",
                 (sid,'session_created', json.dumps({'trade_id':b.get('trade_id')}), now))
    conn.commit(); conn.close()
    return jsonify({'session_id': sid})

@app.route('/api/sessions/<sid>', methods=['GET'])
def get_session(sid):
    conn = get_db()
    row = conn.execute("SELECT * FROM counselling_sessions WHERE session_id=?", (sid,)).fetchone()
    if not row: conn.close(); return jsonify({'error':'Not found'}), 404
    session = dict(row)
    msgs = conn.execute("SELECT * FROM messages WHERE session_id=? ORDER BY created_at ASC", (sid,)).fetchall()
    session['messages'] = [dict(m) for m in msgs]
    conn.close()
    return jsonify(session)

# ═══════════════════════════════════════════════════════════════════════════════
# CHAT  (Multi-Turn, Dynamic Persona, Time-Aware, Fact Memory & RAG)
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/chat', methods=['POST'])
def chat():
    b = request.json or {}
    message = (b.get('message') or '').strip()
    sid     = b.get('session_id')
    if not message: return jsonify({'error':'message required'}), 400

    now = datetime.now().isoformat()
    conn = get_db()
    try:
        # Get or create session
        if sid:
            row = conn.execute("SELECT * FROM counselling_sessions WHERE session_id=?", (sid,)).fetchone()
            session = dict(row) if row else {}
        else:
            sid = str(uuid.uuid4())[:8]
            session = {}
            conn.execute("""INSERT INTO counselling_sessions
                (session_id,learner_name,location,trade_id,parent_concerned,language,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                (sid, b.get('learner_name',''), b.get('location',''),
                 b.get('trade_id'), b.get('parent_concerned',''),
                 b.get('language','en'), now, now))

        # Update session context from request
        for field in ['trade_id','learner_name','location','family_income','education','parent_concerned']:
            if b.get(field): session[field] = b[field]

        # Explicit output language chosen by user (defaults to request language, or session language, or 'en')
        req_lang = (b.get('language') or '').lower().strip()
        if req_lang in ('en', 'hi'):
            session['language'] = req_lang
        elif not session.get('language') or session.get('language') not in ('en', 'hi'):
            session['language'] = 'en'

        target_lang = session['language']
        is_eng = (target_lang == 'en')

        # SmritiCare-grade deterministic fact extraction & persona tracking
        cursor = conn.cursor()
        extracted_facts = extract_family_and_session_facts(sid, message, session, cursor)
        facts = get_session_facts(cursor, sid)
        conn.commit()

        # Fetch recent turns from SQLite for multi-turn dialogue buffer (convert to dicts)
        cursor.execute("SELECT role, speaker_role, message FROM messages WHERE session_id=? ORDER BY created_at ASC", (sid,))
        recent_rows = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    # Detect sentiment & concern
    sentiment = detect_sentiment(message)
    concern   = detect_concern_topic(message)

    # RAG: retrieve relevant past conversation memories
    memories = ""
    if RAG_OK:
        memories = recall_from_vector_store(sid, message, k=4)

    # Build dynamic prompt with time grounding, family persona, verified trade data, and TARGET OUTPUT LANGUAGE
    system_prompt = build_counsellor_prompt(session, facts, memories, target_lang=target_lang)

    # Build structured messages array for Ollama
    chat_messages = [{"role": "system", "content": system_prompt}]
    for r in recent_rows[-8:]:
        role = "user" if r.get('role') == 'user' else "assistant"
        prefix = ""
        if role == 'user':
            s_role = r.get('speaker_role') or 'user'
            if s_role == 'father': prefix = "[Father]: " if is_eng else "[Father / पिता जी]: "
            elif s_role == 'mother': prefix = "[Mother]: " if is_eng else "[Mother / माता जी]: "
            elif facts.get('learner_name'): prefix = f"[{facts['learner_name']}]: "
        chat_messages.append({"role": role, "content": f"{prefix}{r.get('message', '')}"})

    # Add current user message with speaker prefix and strict output language directive
    current_speaker_role = facts.get('speaker_role', 'learner')
    curr_prefix = ""
    if current_speaker_role == 'father': curr_prefix = "[Father]: " if is_eng else "[Father / पिता जी]: "
    elif current_speaker_role == 'mother': curr_prefix = "[Mother]: " if is_eng else "[Mother / माता जी]: "
    elif facts.get('learner_name'): curr_prefix = f"[{facts['learner_name']}]: "

    lang_directive = "[Output required in 100% fluent English]" if is_eng else "[Output required in fluent Hindi / हिंदी में उत्तर दें]"
    chat_messages.append({"role": "user", "content": f"{curr_prefix}{message}\n\n({lang_directive})"})

    # Inference via Ollama with full multi-turn context
    ai_response = ollama_chat(chat_messages, model=CHAT_MODEL, temperature=0.55, num_predict=400)

    # Save to vector store (RAG memory) with speaker & trade metadata
    save_to_vector_store(sid, message, ai_response, speaker_role=current_speaker_role, trade_id=session.get('trade_id'))

    # Save to SQLite with a fresh connection
    conn = get_db()
    try:
        msg_id = str(uuid.uuid4())
        conn.execute("""INSERT INTO messages (id,session_id,role,speaker_role,message,sentiment,concern_topic,language,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                     (str(uuid.uuid4()), sid, 'user', current_speaker_role, message, sentiment, concern, session.get('language','en'), now))
        conn.execute("""INSERT INTO messages (id,session_id,role,speaker_role,message,sentiment,concern_topic,language,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                     (msg_id, sid, 'assistant', 'vocguide', ai_response, 'neutral', '', session.get('language','en'), now))
        conn.execute("UPDATE counselling_sessions SET updated_at=?,language=? WHERE session_id=?",
                     (now, session.get('language','en'), sid))
        conn.execute("INSERT INTO engagement_log (session_id,event,details,created_at) VALUES (?,?,?,?)",
                     (sid,'message', json.dumps({'sentiment':sentiment,'concern':concern, 'speaker':current_speaker_role}), now))
        conn.commit()
    finally:
        conn.close()

    suggest_esc = any(w in ai_response.lower() for w in ['cannot','unable','not sure','human counsellor'])

    learner_display = facts.get('learner_name') or session.get('learner_name')
    if is_eng:
        speaker_title_display = f"{learner_display + '\'s ' if learner_display else ''}Father" if current_speaker_role == 'father' else (f"{learner_display + '\'s ' if learner_display else ''}Mother" if current_speaker_role == 'mother' else (learner_display or "Student"))
    else:
        speaker_title_display = f"{learner_display + ' के ' if learner_display else ''}पिता जी" if current_speaker_role == 'father' else (f"{learner_display + ' की ' if learner_display else ''}माता जी" if current_speaker_role == 'mother' else (learner_display or "विद्यार्थी"))

    return jsonify({
        'session_id': sid, 'response': ai_response,
        'sentiment': sentiment, 'concern_topic': concern,
        'suggest_escalation': suggest_esc,
        'language': session.get('language','en'),
        'rag_memories_used': bool(memories),
        'learner_name': learner_display,
        'trade_id': session.get('trade_id'),
        'speaker_role': current_speaker_role,
        'speaker_title': speaker_title_display
    })

@app.route('/api/chat/set-language', methods=['POST'])
def set_chat_language():
    b = request.json or {}
    sid = b.get('session_id')
    lang = (b.get('language') or 'en').lower().strip()
    if lang not in ('en', 'hi'): lang = 'en'
    if sid:
        conn = get_db()
        conn.execute("UPDATE counselling_sessions SET language=?, updated_at=? WHERE session_id=?",
                     (lang, datetime.now().isoformat(), sid))
        conn.commit()
        conn.close()
    return jsonify({'success': True, 'language': lang, 'session_id': sid})

# ═══════════════════════════════════════════════════════════════════════════════
# VOICE — WhatsApp-style audio message flow
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe():
    """Receives audio blob, returns transcript via Whisper."""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    audio_file = request.files['audio']
    lang = request.form.get('lang', 'en')
    audio_bytes = audio_file.read()
    transcript = transcribe_audio_whisper(audio_bytes, lang)
    if not transcript:
        # Fallback: return empty so frontend can show error
        return jsonify({'transcript': '', 'error': 'Transcription failed or Whisper not available'})
    return jsonify({'transcript': transcript, 'lang': lang})

@app.route('/api/voice/synthesize', methods=['POST'])
def synthesize():
    """Text -> audio (WAV/base64) via IndicTTS."""
    b = request.json or {}
    text   = (b.get('text') or '').strip()
    lang   = b.get('lang', 'en')
    gender = b.get('gender', 'female')
    if not text: return jsonify({'error':'text required'}), 400
    result = synthesize_speech(text, lang, gender)
    return jsonify(result)

@app.route('/api/voice/chat', methods=['POST'])
def voice_chat():
    """Full voice round-trip: audio -> transcript -> AI response -> TTS audio."""
    if 'audio' not in request.files:
        return jsonify({'error':'No audio file'}), 400
    audio_file = request.files['audio']
    lang    = request.form.get('lang', 'en')
    sid     = request.form.get('session_id')
    trade_id= request.form.get('trade_id')

    # 1. STT
    audio_bytes  = audio_file.read()
    transcript   = transcribe_audio_whisper(audio_bytes, lang)
    if not transcript:
        return jsonify({'error': 'Could not transcribe audio. Is Whisper installed?'})

    # 2. AI chat
    chat_payload = {
        'message': transcript, 'session_id': sid,
        'language': lang, 'trade_id': trade_id
    }
    with app.test_request_context('/api/chat', method='POST',
                                   data=json.dumps(chat_payload),
                                   content_type='application/json'):
        from flask import g
        chat_resp = chat()
        chat_data = json.loads(chat_resp.get_data(as_text=True)) if hasattr(chat_resp, 'get_data') else {}

    # 3. TTS
    ai_text = chat_data.get('response', '')
    tts_result = synthesize_speech(ai_text, lang, 'female') if ai_text else {"offline_mode":True}

    return jsonify({
        'transcript': transcript,
        'response_text': ai_text,
        'session_id': chat_data.get('session_id', sid),
        'sentiment': chat_data.get('sentiment','neutral'),
        'audio': tts_result
    })

# ═══════════════════════════════════════════════════════════════════════════════
# TRANSLATE
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/translate', methods=['POST'])
def translate():
    b = request.json or {}
    text   = (b.get('text') or '').strip()
    target = (b.get('target') or 'hi').lower().strip()
    if not text: return jsonify({'translated':''})

    lang_name = 'English' if target == 'en' else {'hi':'Hindi','mr':'Marathi','ta':'Tamil','te':'Telugu',
                 'kn':'Kannada','bn':'Bengali','ml':'Malayalam','gu':'Gujarati'}.get(target,'Hindi')
    try:
        prompt = f"Translate the following vocational guidance text into natural, fluent {lang_name}. Output ONLY the translated text without preamble, explanations, or quotes:\n\n{text}"
        r = http_requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False, "options": {"num_predict":400,"temperature":0.2}
        }, timeout=30)
        result = r.json().get('response','').strip()
        if result.startswith('"') and result.endswith('"'): result = result[1:-1].strip()
        return jsonify({'translated': result or text, 'target': target})
    except Exception as e:
        return jsonify({'translated': text, 'error': str(e)})

# ═══════════════════════════════════════════════════════════════════════════════
# ESCALATION
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/escalate', methods=['POST'])
def escalate():
    b = request.json or {}
    sid = b.get('session_id', str(uuid.uuid4())[:8])
    now = datetime.now().isoformat()
    conn = get_db()
    sess_row = conn.execute("SELECT * FROM counselling_sessions WHERE session_id=?", (sid,)).fetchone()
    sess = dict(sess_row) if sess_row else {}
    msgs = conn.execute("SELECT COUNT(*) as n FROM messages WHERE session_id=?", (sid,)).fetchone()
    msg_count = msgs['n'] if msgs else 0
    last_sent = conn.execute("SELECT sentiment FROM messages WHERE session_id=? AND role='user' ORDER BY created_at DESC LIMIT 1", (sid,)).fetchone()
    sentiment = last_sent['sentiment'] if last_sent else 'neutral'
    eid = str(uuid.uuid4())[:8]
    conn.execute("""INSERT INTO escalations
        (id,session_id,user_id,name,phone,concern,trade_id,location,sentiment,status,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (eid, sid, sess.get('user_id'), b.get('name','Anonymous'),
         b.get('phone',''), b.get('concern',''), sess.get('trade_id', b.get('trade_id')),
         sess.get('location',''), sentiment, 'pending', now))
    conn.execute("INSERT INTO engagement_log (session_id,event,details,created_at) VALUES (?,?,?,?)",
                 (sid,'escalation_requested', json.dumps({'concern':b.get('concern')}), now))
    conn.commit(); conn.close()
    return jsonify({'request_id': eid, 'message': 'A human counsellor will contact you within 24 hours'})

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN — protected endpoints (Strict Role & Data Separation)
# ═══════════════════════════════════════════════════════════════════════════════
def save_trades_data():
    global _DATA, TRADES
    try:
        _DATA['trades'] = list(TRADES.values())
        with open(DATA_DIR / 'trades.json', 'w', encoding='utf-8') as f:
            json.dump(_DATA, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[save_trades_data error: {e}]", file=sys.stderr)
        return False

@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def admin_stats():
    conn = get_db()
    total_sessions  = conn.execute("SELECT COUNT(*) as n FROM counselling_sessions").fetchone()['n']
    total_messages  = conn.execute("SELECT COUNT(*) as n FROM messages").fetchone()['n']
    total_users     = conn.execute("SELECT COUNT(*) as n FROM users WHERE role='user'").fetchone()['n']
    esc_total       = conn.execute("SELECT COUNT(*) as n FROM escalations").fetchone()['n']
    esc_pending     = conn.execute("SELECT COUNT(*) as n FROM escalations WHERE status='pending'").fetchone()['n']
    esc_resolved    = conn.execute("SELECT COUNT(*) as n FROM escalations WHERE status='resolved'").fetchone()['n']

    # Sentiment distribution
    rows = conn.execute("SELECT sentiment, COUNT(*) as n FROM messages WHERE role='user' GROUP BY sentiment").fetchall()
    sent_dist = {r['sentiment']: r['n'] for r in rows}

    # Concern topic distribution
    rows = conn.execute("SELECT concern_topic, COUNT(*) as n FROM messages WHERE role='user' AND concern_topic != '' GROUP BY concern_topic").fetchall()
    concern_dist = {r['concern_topic']: r['n'] for r in rows}

    # Trade interest
    rows = conn.execute("SELECT trade_id, COUNT(*) as n FROM counselling_sessions WHERE trade_id IS NOT NULL GROUP BY trade_id").fetchall()
    trade_dist = {r['trade_id']: r['n'] for r in rows}

    # Language distribution
    rows = conn.execute("SELECT language, COUNT(*) as n FROM counselling_sessions GROUP BY language").fetchall()
    lang_dist = {r['language']: r['n'] for r in rows}

    # Session trend (last 7 days)
    trend = []
    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        ds  = day.strftime('%Y-%m-%d')
        n   = conn.execute("SELECT COUNT(*) as n FROM counselling_sessions WHERE created_at LIKE ?", (f"{ds}%",)).fetchone()['n']
        trend.append({'date': day.strftime('%b %d'), 'sessions': n})

    # Resistance map: location x concern
    rows = conn.execute("""SELECT s.location, m.concern_topic, COUNT(*) as n
        FROM messages m JOIN counselling_sessions s ON m.session_id=s.session_id
        WHERE m.role='user' AND m.concern_topic != '' AND s.location != ''
        GROUP BY s.location, m.concern_topic""").fetchall()
    resistance = {}
    for r in rows:
        loc = r['location']
        if loc not in resistance: resistance[loc] = {}
        resistance[loc][r['concern_topic']] = r['n']

    conn.close()
    return jsonify({
        'total_sessions': total_sessions,
        'total_messages': total_messages,
        'total_users': total_users,
        'avg_messages_per_session': round(total_messages / max(total_sessions, 1), 1),
        'sentiment_distribution': sent_dist,
        'concern_distribution': concern_dist,
        'trade_interest': trade_dist,
        'language_distribution': lang_dist,
        'escalation_stats': {'total': esc_total, 'pending': esc_pending, 'resolved': esc_resolved},
        'session_trend': trend,
        'rag_enabled': RAG_OK,
        'engagement_events': 0
    })

@app.route('/api/admin/sessions', methods=['GET'])
@require_admin
def admin_sessions():
    conn = get_db()
    rows = conn.execute("""SELECT s.*, COUNT(m.id) as message_count,
        MAX(m.created_at) as last_message,
        MAX(CASE WHEN m.role='user' THEN m.sentiment END) as last_sentiment
        FROM counselling_sessions s LEFT JOIN messages m ON s.session_id=m.session_id
        GROUP BY s.session_id ORDER BY s.updated_at DESC LIMIT 100""").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── TRADE MANAGEMENT (Admin can add, edit, remove trades) ───────────────
@app.route('/api/admin/trades', methods=['GET'])
@require_admin
def admin_get_trades():
    return jsonify(list(TRADES.values()))

@app.route('/api/admin/trades', methods=['POST'])
@require_admin
def admin_create_trade():
    b = request.json or {}
    name = (b.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Trade name is required'}), 400
    
    tid = b.get('id') or re.sub(r'[^a-z0-9_]', '', name.lower().replace(' ', '_'))
    if not tid: tid = f"trade_{int(time.time())}"

    trade_obj = {
        "id": tid,
        "name": name,
        "name_hi": b.get('name_hi') or name,
        "nsqf_level": int(b.get('nsqf_level') or 4),
        "duration_months": int(b.get('duration_months') or 12),
        "sector": b.get('sector') or 'Technical & Industrial',
        "sector_hi": b.get('sector_hi') or b.get('sector') or 'तकनीकी और औद्योगिक',
        "description": b.get('description') or f"Certified {name} training aligned with NSQF framework.",
        "description_hi": b.get('description_hi') or b.get('description') or f"{name} ट्रेड में प्रमाणित प्रशिक्षण।",
        "avg_starting_salary": int(b.get('avg_starting_salary') or 12000),
        "avg_experienced_salary": int(b.get('avg_experienced_salary') or 26000),
        "top_salary": int(b.get('top_salary') or 55000),
        "placement_rate": int(b.get('placement_rate') or 85),
        "job_growth_percent": int(b.get('job_growth_percent') or 18),
        "top_employers": b.get('top_employers') or ["Tata Projects", "L&T", "Indian Railways", "Self Employment"],
        "career_progression": b.get('career_progression') or [
            {"level": f"NSQF {b.get('nsqf_level') or 4}", "role": f"Junior {name}", "years": "0-2", "salary": "10,000-15,000"},
            {"level": f"NSQF {(int(b.get('nsqf_level') or 4)) + 1}", "role": f"Senior {name}", "years": "2-5", "salary": "18,000-28,000"},
            {"level": f"NSQF {(int(b.get('nsqf_level') or 4)) + 2}", "role": f"{name} Supervisor", "years": "5-8", "salary": "30,000-45,000"}
        ],
        "self_employment_potential": b.get('self_employment_potential') or "High",
        "self_employment_potential_hi": b.get('self_employment_potential_hi') or "उच्च",
        "safety_rating": b.get('safety_rating') or "Low",
        "social_perception": b.get('social_perception') or "Good",
        "social_perception_hi": b.get('social_perception_hi') or "अच्छी",
        "states_high_demand": b.get('states_high_demand') or ["All States", "Maharashtra", "Gujarat"],
        "gender_diversity": b.get('gender_diversity') or {"male": 75, "female": 25},
        "certifications": b.get('certifications') or ["ITI Certificate", f"NSQF Level {b.get('nsqf_level') or 4}"],
        "parental_concerns_addressed": b.get('parental_concerns_addressed') or {
            "income": f"{name} professionals earn steady livelihoods with starting salaries up to ₹16,000/mo.",
            "safety": "Standard protective equipment and health protocols ensure safe workplace practices.",
            "social_status": f"{name} is an essential industrial technical vocation.",
            "growth": "Clear progression ladder from Technician to Supervisor."
        }
    }
    
    TRADES[tid] = trade_obj
    save_trades_data()
    return jsonify({'success': True, 'trade': trade_obj})

@app.route('/api/admin/trades/<tid>', methods=['PUT'])
@require_admin
def admin_update_trade(tid):
    if tid not in TRADES:
        return jsonify({'error': 'Trade not found'}), 404
    b = request.json or {}
    t = TRADES[tid]
    for k in ['name', 'name_hi', 'sector', 'sector_hi', 'description', 'description_hi',
              'self_employment_potential', 'self_employment_potential_hi', 'safety_rating',
              'social_perception', 'social_perception_hi']:
        if k in b: t[k] = b[k]
    for k in ['nsqf_level', 'duration_months', 'avg_starting_salary', 'avg_experienced_salary',
              'top_salary', 'placement_rate', 'job_growth_percent']:
        if k in b:
            try: t[k] = int(b[k])
            except: pass
    save_trades_data()
    return jsonify({'success': True, 'trade': t})

@app.route('/api/admin/trades/<tid>', methods=['DELETE'])
@require_admin
def admin_delete_trade(tid):
    if tid not in TRADES:
        return jsonify({'error': 'Trade not found'}), 404
    del TRADES[tid]
    save_trades_data()
    return jsonify({'success': True, 'deleted_id': tid})

# ── USER MANAGEMENT (Admin can manage users, roles, and status) ─────────
@app.route('/api/admin/users', methods=['GET'])
@require_admin
def admin_users():
    conn = get_db()
    rows = conn.execute("SELECT id,username,full_name,role,email,phone,location,created_at,last_login,is_active FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/users', methods=['POST'])
@require_admin
def admin_create_user():
    b = request.json or {}
    username = (b.get('username') or '').strip()
    password = (b.get('password') or '').strip()
    role     = b.get('role','user')
    if not username or not password:
        return jsonify({'error':'username and password required'}), 400
    conn = get_db()
    uid = str(uuid.uuid4())
    try:
        conn.execute("""INSERT INTO users (id,username,password_hash,full_name,role,email,phone,location,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                     (uid, username, _hash_password(password), b.get('full_name',''),
                      role, b.get('email',''), b.get('phone',''), b.get('location',''),
                      datetime.now().isoformat()))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error':'Username already taken'}), 409
    conn.close()
    return jsonify({'user_id': uid, 'username': username, 'role': role})

@app.route('/api/admin/users/<uid>/toggle', methods=['POST'])
@require_admin
def admin_toggle_user(uid):
    conn = get_db()
    conn.execute("UPDATE users SET is_active = 1 - is_active WHERE id=?", (uid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/users/<uid>/role', methods=['POST'])
@require_admin
def admin_change_user_role(uid):
    b = request.json or {}
    new_role = b.get('role')
    if new_role not in ('admin', 'user'):
        return jsonify({'error': 'Invalid role'}), 400
    conn = get_db()
    conn.execute("UPDATE users SET role=? WHERE id=?", (new_role, uid))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'new_role': new_role})

@app.route('/api/admin/users/<uid>', methods=['DELETE'])
@require_admin
def admin_delete_user(uid):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'deleted_uid': uid})

@app.route('/api/admin/escalations', methods=['GET'])
@require_admin
def admin_escalations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/escalations/<eid>/resolve', methods=['POST'])
@require_admin
def resolve_escalation(eid):
    b = request.json or {}
    conn = get_db()
    conn.execute("UPDATE escalations SET status='resolved', resolved_at=?, notes=? WHERE id=?",
                 (datetime.now().isoformat(), b.get('notes',''), eid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/resistance-map', methods=['GET'])
@require_admin
def resistance_map():
    conn = get_db()
    rows = conn.execute("""SELECT s.location, m.concern_topic, COUNT(*) as n
        FROM messages m JOIN counselling_sessions s ON m.session_id=s.session_id
        WHERE m.role='user' AND m.concern_topic != '' AND s.location != ''
        GROUP BY s.location, m.concern_topic""").fetchall()
    conn.close()
    result = {}
    for r in rows:
        loc = r['location']
        if loc not in result: result[loc] = {}
        result[loc][r['concern_topic']] = r['n']
    return jsonify(result)

@app.route('/api/admin/engagement', methods=['GET'])
@require_admin
def admin_engagement():
    conn = get_db()
    rows = conn.execute("SELECT * FROM engagement_log ORDER BY created_at DESC LIMIT 200").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM STATUS
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/ollama/status', methods=['GET'])
def ollama_status():
    try:
        r = http_requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m['name'] for m in r.json().get('models',[])]
        return jsonify({'status':'online','models':models,'rag_enabled':RAG_OK,
                        'whisper_available': WHISPER_CLI.exists(),
                        'indic_tts_available': bool(list(INDIC_TTS_DIR.glob('*/fastpitch/best_model.pth')))
                                               if INDIC_TTS_DIR.exists() else False})
    except:
        return jsonify({'status':'offline','models':[],'rag_enabled':False,
                        'whisper_available':WHISPER_CLI.exists(),'indic_tts_available':False})

# ═══════════════════════════════════════════════════════════════════════════════
# RAG: seed trades data into vector store for domain context
# ═══════════════════════════════════════════════════════════════════════════════
def seed_trade_knowledge():
    if not RAG_OK: return
    try:
        existing = vector_store._collection.count()
        if existing > 20:
            print(f"[RAG] Vector store already has {existing} docs — skip seed")
            return
        texts, metas = [], []
        for tid, t in TRADES.items():
            doc = f"""Trade: {t['name']} (NSQF Level {t['nsqf_level']})
Sector: {t['sector']}
Duration: {t['duration_months']} months
Starting Salary: Rs{t['avg_starting_salary']}/month
Average Salary (experienced): Rs{t['avg_experienced_salary']}/month
Top Earners: Rs{t['top_salary']}/month
Placement Rate: {t['placement_rate']}%
Job Growth: {t['job_growth_percent']}% per year
Self Employment Potential: {t['self_employment_potential']}
Safety Rating: {t['safety_rating']}
Top Employers: {', '.join(t['top_employers'])}
Career Progression: {' -> '.join(f"{p['role']} ({p['salary']}/mo in {p['years']} years)" for p in t['career_progression'])}
Parental Concerns: {json.dumps(t['parental_concerns_addressed'], ensure_ascii=False)}"""
            texts.append(doc)
            metas.append({"type":"trade_knowledge","trade_id":tid,"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"epoch":float(datetime.now().timestamp())})

        for s in SCHEMES:
            doc = f"Government Scheme: {s['name']}\n{s['description']}\nBenefit: {s['benefit']}\nEligibility: {s['eligibility']}"
            texts.append(doc)
            metas.append({"type":"scheme","timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"epoch":float(datetime.now().timestamp())})

        vector_store.add_texts(texts=texts, metadatas=metas)
        print(f"[RAG] Seeded {len(texts)} trade/scheme documents into vector store")
    except Exception as e:
        print(f"[RAG seed error: {e}]")

# ═══════════════════════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("VocGuide v2 - AI Career Counselling Platform")
    print("=" * 55)
    init_db()
    print("Database initialised")
    # Seed trade knowledge into RAG (non-blocking background thread)
    threading.Thread(target=seed_trade_knowledge, daemon=True).start()
    print(f"RAG (BGE-M3 + ChromaDB): {'ENABLED' if RAG_OK else 'DISABLED (install langchain-ollama)'}")
    print(f"Whisper STT:  {'AVAILABLE' if WHISPER_CLI.exists() else 'Not found'}")
    print(f"IndicTTS:     {'AVAILABLE' if INDIC_TTS_DIR.exists() else 'Not found'}")
    print(f"Server: http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, port=5000, host='0.0.0.0')
