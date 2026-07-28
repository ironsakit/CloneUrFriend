import json
import ollama

import os
os.makedirs("input", exist_ok=True)  # in caso la cartella non esiste la crea, (exists_ok=True evita l'errore in caso la cartella esista già)

MODELLO_EMBED = "bge-m3"
YOU = "NameTarget"
INPUT = f"output_json/pairs_{YOU}.json"
OUTPUT = f"input/indice_{YOU}.json"

with open(INPUT, "r", encoding="utf-8") as f:
    PAIRS = json.load(f)

print(f"coppie da indicizzare: {len(PAIRS)}")

indice = []
for i, pair in enumerate(PAIRS):
    testo = " ".join(pair["stimuli"])
    vettore = ollama.embed(model=MODELLO_EMBED, input=testo)["embeddings"][0]
    indice.append({
        "stimuli": pair["stimuli"],
        "reaction": pair["reaction"],
        "vettore": vettore
    })
    if(i + 1) % 100 == 0:
        print(f"{i + 1} / {len(PAIRS)}")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(indice, f)

print("COMPLETED!")