import json
import random
import re

import ollama

YOU = "TargetName"
CHARACTERISTIC = ""
YOUR_MODEL = ""

with open("output_json/Stimuli_Reactions.json", "r", encoding="utf-8") as f:
    PAIRS = json.load(f)

def retrieval(question):

    STOPWORD = {"il", "lo", "la", "i", "gli", "le", "un", "una", "di", "a", "da",
                "in", "con", "su", "per", "tra", "fra", "e", "o", "ma", "che",
                "non", "hai", "ho", "sei", "sono", "è", "al", "del", "come",
                "cosa", "mi", "ti", "si", "ci", "vi", "se", "poi", "anche", "sta", "stai",
                "fatto", "fare", "dai", "già", "più", "tutto", "quando", "dove", "perché"}

    words = re.findall(r"\w+", question.lower())  # estrae solo le sequenze di caratteri alfanumerici, scartando punteggiatura ed emoji
    keys = [p for p in words if p not in STOPWORD and len(p) >= 3]

    # -------------- Filtro di frequenza -----------------------------#
    frequency = {}
    for k in keys:
        frequency[k] = sum(1 for pair in PAIRS if k in " ".join(pair["stimuli"]).lower())
    keys = [k for k in keys if frequency[k] < len(PAIRS) * 0.05]  # se questa parola è presente nel meno del 5% delle coppie la tengo, sennò la scarto
    # ----------------------------------------------------------------#

    results = []

    for pair in PAIRS:
        text = " ".join(pair["stimuli"]).lower()
        points = sum(1 for k in keys if k in text)  # somma ogni volta che una chiave k delle chiavi viene trovata nel testo
        if points > 0:
            results.append((points, pair))

    results.sort(key=lambda x: x[0], reverse=True)  # riordino in base al punteggio
    best = [c for _, c in results[:50]]  # solo le 50 migliori

    if not best:
        best = random.sample(PAIRS, 20)

    best_results = random.sample(best, min(20, len(best)))  # prendo 20 a caso dalle 50 migliori
    return best_results

def generate_prompt(best):
    examples = ""
    for c in best:
        examples += f"Stimoli: {c['stimuli']} --> Risposta tua: {c['reaction']}\n\n"

    prompt = f"""Sei {YOU}, {CHARACTERISTIC}.
DEVI SCRIVERE ESATTAMENTE COME LUI, RISPETTARE IL SUO MODO DI SCRIVERE, LA SUA PUNTEGGIATURA, MODI DI DIRE, TUTTO.
Ecco come rispondi di solito:
{examples}"""
    return prompt

history = []

while True:
    print("(Write \"exit\" to exit the program.)")
    question = input("You: ")
    if question == "exit":
        break

    best = retrieval(question)  # il tuo retrieval
    prompt = generate_prompt(best)

    messages = [{"role": "system", "content": prompt}]
    messages.extend(history[-6:])  # i turni precedenti (una cronologia primitiva)
    messages.append({"role": "user", "content": question})

    response = ollama.chat(
        model=f"{YOUR_MODEL}",
        messages=messages,
        options={"temperature": 0.8}
    )
    text = response["message"]["content"]
    print(f"{YOU}: {text}")

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": text})