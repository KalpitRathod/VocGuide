import sys, io, requests, json, py_compile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("VOCGUIDE COMPREHENSIVE RECHECK SUITE")
print("=" * 60)

# 1. Python Syntax Validation
print("\n[1/5] Validating Python Syntax...")
try:
    py_compile.compile('app.py', doraise=True)
    print("  ✓ app.py syntax: VALID")
except Exception as e:
    print(f"  ✗ app.py syntax error: {e}")
    sys.exit(1)

# 2. Static Files Symbols & Jargon Audit
print("\n[2/5] Auditing UI Symbols & Terminology...")
files_to_check = ['static/index.html', 'static/app.js', 'static/style.css']
forbidden_tokens = ['🤖', '&#129302;', '✨', '&#10024;', 'dashed', 'stroke-dasharray', 'BGE-M3', 'RAG Active', 'Dual Family AI', '—', '–', '&mdash;', '&ndash;']

all_clean = True
for fpath in files_to_check:
    with open(fpath, encoding='utf-8') as f:
        content = f.read()
    found = [t for t in forbidden_tokens if t in content]
    if found:
        print(f"  ✗ {fpath} contains forbidden tokens: {found}")
        all_clean = False
    else:
        print(f"  ✓ {fpath}: Clean of dashed styles, robot emojis, and AI jargon")

if not all_clean:
    sys.exit(1)

# 3. Trades Data Integrity
print("\n[3/5] Verifying Trades Database Schema & Records...")
with open('data/trades.json', encoding='utf-8') as f:
    trades_data = json.load(f)
trades = trades_data['trades']
print(f"  ✓ Total NSQF Trades Loaded: {len(trades)}")
for t in trades:
    assert 'id' in t and 'name' in t and 'avg_starting_salary' in t and 'parental_concerns_addressed' in t
print("  ✓ All trades have required salary, safety, and parental fields")

# 4. Live Server Endpoints
BASE = "http://127.0.0.1:5000"
print(f"\n[4/5] Testing Live HTTP & API Endpoints on {BASE}...")

r_idx = requests.get(f"{BASE}/")
assert r_idx.status_code == 200, f"Index failed: {r_idx.status_code}"
print("  ✓ GET /: HTTP 200 OK")

r_tr = requests.get(f"{BASE}/api/trades")
assert r_tr.status_code == 200 and len(r_tr.json()) == len(trades), "Trades API failed"
print(f"  ✓ GET /api/trades: HTTP 200 OK ({len(r_tr.json())} trades returned)")

# 5. Multi-turn Language Decoupling & Switching Test
print("\n[5/5] Testing Multi-turn Chat Language Decoupling & Output Switching...")

# Create session with English output
r_sess = requests.post(f"{BASE}/api/sessions", json={
    "learner_name": "Aman",
    "trade_id": "electrician",
    "language": "en"
})
assert r_sess.status_code == 200, "Session creation failed"
sid = r_sess.json()['session_id']
print(f"  ✓ Session created: {sid} (initial lang=en)")

# Case A: Hinglish input with English output selected
r_chat1 = requests.post(f"{BASE}/api/chat", json={
    "session_id": sid,
    "message": "kya he mera naam aur mera trade?",
    "language": "en"
})
assert r_chat1.status_code == 200
ans1 = r_chat1.json()
print(f"  Query (Hinglish): 'kya he mera naam aur mera trade?' | Lang: en")
print(f"  AI Output: {ans1.get('response')[:90]}...")
print(f"  Reported Language: {ans1.get('language')}")
assert ans1.get('language') == 'en', "Language should remain English"

# Case B: Father speaks in Hindi with English output selected
r_chat2 = requests.post(f"{BASE}/api/chat", json={
    "session_id": sid,
    "message": "ji me Aman ka pita baat kar raha hu, electrician me shock ka kitna khatra hai?",
    "language": "en"
})
assert r_chat2.status_code == 200
ans2 = r_chat2.json()
print(f"\n  Query (Father in Hindi): 'ji me Aman ka pita baat kar raha hu, shock ka khatra hai?' | Lang: en")
print(f"  AI Output: {ans2.get('response')[:120]}...")
print(f"  Speaker Title: {ans2.get('speaker_title')}")
assert "Father" in ans2.get('speaker_title', '')

# Case C: Switch Language dynamically at output to Hindi
r_switch = requests.post(f"{BASE}/api/chat/set-language", json={
    "session_id": sid,
    "language": "hi"
})
assert r_switch.status_code == 200 and r_switch.json().get('language') == 'hi'
print(f"\n  ✓ Output Language Switched via /api/chat/set-language to 'hi'")

# Case D: User asks in English with Hindi output selected
r_chat3 = requests.post(f"{BASE}/api/chat", json={
    "session_id": sid,
    "message": "What is my starting salary?",
    "language": "hi"
})
assert r_chat3.status_code == 200
ans3 = r_chat3.json()
print(f"  Query (English): 'What is my starting salary?' | Lang: hi")
print(f"  AI Output (in Hindi): {ans3.get('response')[:90]}...")
print(f"  Reported Language: {ans3.get('language')}")
assert ans3.get('language') == 'hi'

# Case E: Translate endpoint
r_tr_en = requests.post(f"{BASE}/api/translate", json={
    "text": "नमस्ते, आपका स्वागत है।",
    "target": "en"
})
assert r_tr_en.status_code == 200 and 'translated' in r_tr_en.json()
print(f"\n  ✓ Translation HI -> EN: '{r_tr_en.json().get('translated')}'")

r_tr_hi = requests.post(f"{BASE}/api/translate", json={
    "text": "Welcome to career counselling.",
    "target": "hi"
})
assert r_tr_hi.status_code == 200 and 'translated' in r_tr_hi.json()
print(f"  ✓ Translation EN -> HI: '{r_tr_hi.json().get('translated')}'")

print("\n" + "=" * 60)
print("ALL RECHECK TESTS COMPLETED SUCCESSFULLY AND PASSED!")
print("=" * 60)
