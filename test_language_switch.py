import sys, io, requests, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://127.0.0.1:5000/api"

print("--- 1. Testing Session Creation with English Output ---")
r = requests.post(f"{BASE}/sessions", json={
    "learner_name": "Kalpit",
    "language": "en",
    "trade_id": "welder"
})
assert r.status_code == 200, f"Failed to create session: {r.text}"
sid = r.json()['session_id']
print(f"Session created: {sid}")

print("\n--- 2. User types in Hinglish with language='en' ---")
# User asks name in Hinglish: "kya he mera naam"
r2 = requests.post(f"{BASE}/chat", json={
    "session_id": sid,
    "message": "kya he mera naam",
    "language": "en"
})
assert r2.status_code == 200, f"Chat failed: {r2.text}"
d2 = r2.json()
print("Input: kya he mera naam")
print("Selected Language: en")
print("AI Response:", d2.get('response'))
print("Returned Language:", d2.get('language'))

print("\n--- 3. Father speaks in Hindi with language='en' ---")
r3 = requests.post(f"{BASE}/chat", json={
    "session_id": sid,
    "message": "ji me Kalpit ka pita baat kar raha hu, welder me safety kaisa hai?",
    "language": "en"
})
assert r3.status_code == 200, f"Chat failed: {r3.text}"
d3 = r3.json()
print("Input: ji me Kalpit ka pita baat kar raha hu, welder me safety kaisa hai?")
print("AI Response:", d3.get('response'))
print("Speaker Title:", d3.get('speaker_title'))
print("Returned Language:", d3.get('language'))

print("\n--- 4. Switch Output Language to Hindi (Testing set-language) ---")
r_switch = requests.post(f"{BASE}/chat/set-language", json={
    "session_id": sid,
    "language": "hi"
})
assert r_switch.status_code == 200
print("Switch response:", r_switch.json())

print("\n--- 5. User speaks in English with language='hi' ---")
r4 = requests.post(f"{BASE}/chat", json={
    "session_id": sid,
    "message": "What is my name and what trade am I learning?",
    "language": "hi"
})
assert r4.status_code == 200
d4 = r4.json()
print("Input: What is my name and what trade am I learning?")
print("Selected Language: hi")
print("AI Response:", d4.get('response'))
print("Returned Language:", d4.get('language'))

print("\n--- 6. Testing /api/translate endpoint ---")
r_tr_en = requests.post(f"{BASE}/translate", json={
    "text": "नमस्ते! आपका नाम कल्पित है और आप वेल्डर ट्रेड सीख रहे हैं।",
    "target": "en"
})
print("Hindi -> English:", r_tr_en.json())

r_tr_hi = requests.post(f"{BASE}/translate", json={
    "text": "Your name is Kalpit and you are exploring the Welder trade.",
    "target": "hi"
})
print("English -> Hindi:", r_tr_hi.json())

print("\n=== ALL TESTS PASSED ===")
