import json
import numpy as np
import ollama

YOU = "NameTarget"
CHARACTERISTIC = f"""Sei {YOU}, uno studente universitario di 20 anni. Stai chattando in un gruppo WhatsApp con i tuoi amici.

DEVI ASSOLUTAMENTE rispettare queste regole di scrittura:
- Scrivi TUTTO in minuscolo, non usare MAI le maiuscole, nemmeno a inizio frase o per i nomi.
- Niente virgole o punti, punteggiatura inesistente.
- Rispondi con frasi cortissime, spesso senza verbo (es. "si vabbè", "non so", "ci sta").
- Usa parole banalissime, linguaggio da strada/chat.
- PARLA SOLO ED ESCLUSIVAMENTE IN ITALIANO. Vietato usare lo slang americano o parole inglesi (no "bro", no "dude", no "no way").
- NON usare mai parole formali come "inoltre", "tuttavia", "quindi".
- NON fare liste e NON fare la morale.
- Genera SOLO ed ESCLUSIVAMENTE il testo del tuo messaggio. NON inserire mai il tuo nome, prefissi (es. "{YOU}:") o etichette.
- Inoltre non mettere mai '|' nelle tue frasi"""
YOUR_MODEL = "gemma2:9b"
MODELLO_EMBED = "bge-m3"
CHOOSE_INPUT = f"input/indice_{YOU}.json"

with open(CHOOSE_INPUT, "r", encoding="utf-8") as f:
    INDICE = json.load(f)

# prendiamo ogni chiave "embedding" di ogni coppia nell'indice, la inseriamo in una lista che diventa un array numpy, ovvero una matrice (float a 32 bit perchè non ci serve la precisione a 64 per un embedding)
MATRICE = np.array([v["vettore"] for v in INDICE], dtype=np.float32)
# trasformo ogni vettore di lunghezza 1, mantenendo la direzione, np.align genera la normale per ogni vettore, axis=1 dice di fare la divisione per ogni riga, e keepdims=True mantiene la forma a colonna, in modo da allineare la divisione riga per riga
MATRICE /= np.linalg.norm(MATRICE, axis=1, keepdims=True)

print(f"Indice caricato: {len(INDICE)} coppie")

def retrieval(question, k=8):
    question_array = ollama.embed(model=MODELLO_EMBED, input=question)["embeddings"][0]
    q = np.array(question_array, dtype=np.float32)
    q /= np.linalg.norm(q)

    similarity = MATRICE @ q  # moltiplicazione matrice per vettore ottenendo un vettore (visto che avevamo resto i vettori lunghi 1, non serve dividere per il prodotto delle due lunghezze perchè entrambe sono 1, quindi basta il prodotto scalare)
    best_idx = np.argsort(similarity)[::-1][:k]   # ordina dando solo gli indici ordinati, [::-1] ci permette di invertire la lista, perchè argsort ordina in modo crescente ma noi vogliamo in ordine decrescente (dal + simile al - simile alla domanda) e prendiamo i primi k = 8

    results = []
    for i in best_idx:
        results.append({
            "stimuli": INDICE[i]["stimuli"],
            "reaction": INDICE[i]["reaction"]
        })
        print(f"  [debug] {similarity[i]:.3f}  {INDICE[i]["stimuli"]} {INDICE[i]["reaction"]}}}")
    return results


def generate_prompt(best):
    examples = ""
    for i, c in enumerate(best, 1):
        # c["stimuli"] è una lista del tipo: ["x: ciao", "y: stasera usciamo?"]
        chat_context = "\n".join(c["stimuli"])
        examples += f"--- ESEMPIO {i} ---\n{chat_context}\n[Risposta di {YOU}]: {c['reaction']}\n\n"

    prompt = f"""{CHARACTERISTIC}

Ecco alcuni esempi reali di conversazioni di gruppo passate e di come hai risposto:

{examples}--- CHAT ATTUALE ---
Ora leggi i messaggi recenti nel gruppo qui sotto e genera SOLO la tua risposta come {YOU}."""
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
    messages.extend(history[-4:])  # i turni precedenti (una cronologia primitiva)
    messages.append({"role": "user", "content": question})

    response = ollama.chat(
        model=YOUR_MODEL,
        messages=messages,
        options={
            "temperature": 0.65,  # Più creatività umana
            "stop": ["Utente:", "Esempio", "\n\n"]  # Ferma il modello se prova a simulare l'utente
        }
    )
    text = response["message"]["content"].strip()

    text = text.split("\n")[0]
    for prefisso in [YOU + ":", "[tu]", "assistant:"]:
        if text.lower().startswith(prefisso.lower()):
            text = text[len(prefisso):].strip()

    print(f"\n{YOU}: {text}\n")

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": text})