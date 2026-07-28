import ollama

def embedding(testo):
    return ollama.embed(model="bge-m3", input=testo)["embeddings"][0]

def similarity(a, b):
    # similarità è il prodotto scalare diviso il prodotto delle lunghezze
    prodotto = sum(x * y for x, y in zip(a, b))  # zip(a, b) accoppia i due elementi dei due vettori
    normale_a = sum(x * x for x in a) ** 0.5 # la somma del quadrato di ogni componente tutto sotto radice
    normale_b = sum(y * y for y in b) ** 0.5
    return prodotto / (normale_a * normale_b)

base = embedding("andiamo a mangiare qualcosa?")

prove = [
    "si esce a cena?",              # stesso senso, zero parole in comune
    "usciamo stasera?",             # senso vicino
    "hai studiato per l'esame?",    # senso lontano
    "quanto pesi di squat?",        # senso lontanissimo
]

for p in prove:
    s = similarity(base, embedding(p))
    print(f"{s:.3f} <-- {p}")