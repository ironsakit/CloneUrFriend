from datetime import datetime
import json

# --------------- CONFIGURATION SECTION ------------------  IMPORTANT
import os
os.makedirs("output_json", exist_ok=True)  # in caso la cartella non esiste la crea, (exists_ok=True evita l'errore in caso la cartella esista già)

FILE_CHAT = "data/chat.txt"         # Path to the exported WhatsApp chat file
YOU = "NameTarget"             # Exact name of the person to clone
EXCLUDED_PEOPLE = ["Fede T.", "Meta AI"]  # People to completely ignore
DISCARD = ["🔴 FLASH", "omesso", "omessa", "sticker non incluso", "https",
 "❗️", "Questo messaggio è stato eliminato.", "ha aggiunto",
 "ha rimosso", "è uscito", "ha cambiato", "Contatto"]    # Words/links to discard messages
OUTPUT = f"output_json/pairs_{YOU}.json"

# ------------------ FILTERING FUNCTION -------------------

def is_valid(msg):
    if len(msg) < 10:
        return False
    if not any(c.isalnum() for c in msg):
        return False
    # Check if the message contains forbidden words (case-insensitive)
    if any(s.lower() in msg.lower() for s in DISCARD):
        return False
    return True

# ------------------- CHAT PROCESSING ---------------------

with open(FILE_CHAT, "r", encoding="utf-8") as f:
    rows = f.readlines()

lasts = []  # Recent context messages (up to 3)
pairs = []  # Final result: stimuli -> reaction pairs

for row in rows:
    # Clean invisible/unicode characters typical of WhatsApp exports
    row = (row.replace("\u2069", "").replace("\u200e", "")
           .replace("@⁨", "").replace("\"", "").strip())

    if not row or not row.startswith("["):
        continue

    parts = row.split("]", 1)
    if len(parts) != 2:
        continue

    resto = parts[1].split(":", 1)
    if len(resto) != 2:
        continue

    author = resto[0].strip()
    msg = resto[1].strip()

    # 1. Filter excluded people
    if author in EXCLUDED_PEOPLE:
        continue

    # 2. Filter messages that are too short or contain elements from DISCARD
    if not is_valid(msg):
        continue

    # 3. Timestamp extraction
    timestamp_str = parts[0].lstrip("[").strip()
    try:
        ts = datetime.strptime(timestamp_str, "%d/%m/%y, %H:%M:%S")
    except ValueError:
        continue  # Unexpected date format, skip row

    # 4. Create Stimuli -> Reaction pair
    if author == YOU and lasts:
        delta = (ts - lasts[-1]["ts"]).total_seconds()
        if delta <= 180 and lasts[-1]["author"] != YOU:
            pairs.append({
                "stimuli": [last["text"] for last in lasts],
                "reaction": msg
            })

    # 5. Update message history
    lasts.append({"ts": ts, "author": author, "text": f"{author}: {msg}"})

    # Keep at most the last 3 messages
    if len(lasts) > 3:
        lasts.pop(0)

# ---------------------- SAVE RESULTS ------------------------------

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(pairs, f, ensure_ascii=False, indent=2)

print(f"Completed! Saved {len(pairs)} conversation pairs in '{OUTPUT}'.")