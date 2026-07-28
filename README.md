# WhatsApp Style Clone

Sistema RAG locale che genera risposte imitando lo stile di scrittura di una
persona specifica, appreso dai suoi messaggi WhatsApp. Il retrieval è semantico
(embedding + similarità coseno) e tutto gira offline con
[Ollama](https://ollama.com) (o altri modelli - come [gemma2:9b](https://ollama.com/library/gemma2:9b))

> **Progetto di apprendimento.** I dati della chat usati per costruire il dataset
> sono privati e **non inclusi** in questo repository. Per eseguirlo serve un
> proprio export di WhatsApp!

## Come funziona

**1. Parsing (`parser.py`)**
L'export `.txt` della chat viene ripulito (caratteri Unicode invisibili,
allegati, messaggi di sistema di whatsapp) e trasformato in coppie *stimolo → reazione*: per
ogni messaggio scritto dalla persona target, i messaggi immediatamente precedenti
diventano lo "stimolo" e il suo messaggio la "reazione", una coppia viene tenuta
solo se la risposta è arrivata entro 180 secondi e se il messaggio precedente non
è della persona stessa (sarebbe una continuazione, non una reazione, per questo).

**2. Indicizzazione (`embedding.py`)**
Ogni stimolo viene trasformato in un vettore da 768 dimensioni (LOL) tramite un modello di embedding
(`bge-m3`). Il risultato è un indice salvato su disco, da calcolare una volta
sola (per 10.000 coppie ci vogliono circa 20 minuti sul mio PC --> (AMD Ryzen 7 5700X 8-Core Processor (3.40 GHz) e AMD Radeon RX 6650 XT (8 GB) con 32,0 GB di RAM).

**3. Retrieval + generazione (`clone.py`)**
La domanda viene vettorizzata e confrontata con tutto l'indice tramite
**similarità coseno**: si recuperano le coppie semanticamente più vicine, che
finiscono nel prompt come esempi, Il modello generativo produce la
risposta, che viene ripulita da eventuali prefissi o righe extra.

## Utilizzo

```bash
pip install -r requirements.txt
ollama pull bge-m3
ollama pull gemma2:9b
```

1. Esporta una chat WhatsApp come `.txt` e mettila in `data/chat.txt`
2. In `parser.py` imposta `YOU` con il nome esatto della persona da clonare (esattamente come salvato nel export di Whatsapp), `EXCLUDED_PEOPLE` (persone da escludere nella chat) e `DISCARD` (parole da escludere), poi:
   ```bash
   python parser.py
   ```
3. in `embedding.py` imposta `YOU` e costruisci l'indice degli embedding (richiede alcuni minuti):
   ```bash
   python embedding.py
   ```
4. In `clone.py` imposta `YOU`, `CHARACTERISTIC` (breve descrizione della persona da clonare) e `YOUR_MODEL`, poi avvia la chat:
   ```bash
   python clone.py
   ```

Il formato dei dati prodotto dal parser è mostrato in
`output_json/pairs_example.json` (dati inventati). `embedding.py` genera
`input/indice_<nome>.json`, con la stessa struttura più un campo `vettore`.

Lo script `test_embed.py` confronta la similarità coseno tra frasi affini ed
estranee: serve a verificare che il modello di embedding funzioni sulla lingua
dei propri dati (vedi *Nota sulla lingua*).

## Configurazione

**In `parser.py`:**

| Variabile | Cosa mettere |
|-----------|--------------|
| `FILE_CHAT` | Percorso dell'export `.txt` (es. `data/chat.txt`) |
| `YOU` | Nome **esatto** della persona da clonare, come appare nella chat (attenzione a maiuscole ed eventuali emoji nel nome) |
| `EXCLUDED_PEOPLE` | Persone da ignorare del tutto (bot, "Meta AI", partecipanti non voluti) |
| `DISCARD` | Parole o pattern che fanno scartare un messaggio |

**In `embedding.py` e `clone.py`:**

| Variabile | Cosa mettere |
|-----------|--------------|
| `YOU` | Deve **combaciare esattamente** in tutti e tre i file |
| `MODELLO_EMBED` | Modello di embedding, deve essere **lo stesso** nei due file (di default `bge-m3`) |
| `CHARACTERISTIC` | Descrizione della persona e regole di stile, inserite nel system prompt |
| `YOUR_MODEL` | Il modello generativo Ollama (vedi sotto) |

> Importante: se si cambia `MODELLO_EMBED` bisogna **ricostruire l'indice**.
> Vettori prodotti da modelli diversi non sono confrontabili tra loro.

### Scelta del modello generativo

`YOUR_MODEL` accetta qualsiasi modello disponibile in Ollama, purché scaricato
con `ollama pull <modello>`. Per esempio: `gemma2:9b`, `llama3.1:8b`,
`mistral-nemo`, `qwen2.5:7b`.

È un compromesso tra qualità e hardware:
- **Modelli piccoli** (7–8B): veloci, girano su GPU con ~8 GB di VRAM, ma meno
  accurati e tendono a "normalizzare" verso l'italiano corretto, perdendo il
  registro informale.
- **Modelli più grandi** (9–12B): migliori sullo stile e sulla lingua, ma
  richiedono più VRAM. Oltre la capacità della GPU girano su CPU e diventano
  molto lenti.

Conviene scegliere il modello più grande che gira fluido sulla propria scheda.

## Nota sulla lingua

Il progetto è pensato per chat in **italiano**, e la scelta del modello di
embedding è determinante: un modello addestrato prevalentemente su inglese
produce vettori che non discriminano il significato su testi italiani.

Misurato con `test_embed.py`, partendo da *"andiamo a mangiare qualcosa?"*:

| Frase confrontata | `nomic-embed-text` | `bge-m3` |
|---|---|---|
| "si esce a cena?" | 0.550 | **0.752** |
| "usciamo stasera?" | 0.632 | **0.725** |
| "hai studiato per l'esame?" | 0.558 | 0.534 |
| "quanto pesi di squat?" | 0.560 | 0.391 |

Con `nomic-embed-text` i punteggi sono tutti schiacciati intorno a 0.55 e
l'ordine è quasi casuale: frasi estranee risultano *più* simili di frasi affini.
`bge-m3`, essendo multilingue, separa correttamente. Per clonare una persona che
scrive in un'altra lingua, verificare il modello di embedding **prima** di
costruire l'indice.

## Scelte tecniche

- **Locale (Ollama) invece di un'API cloud**: i messaggi sono privati e non
  devono uscire dal computer. Nessuna API key, nessuna quota, funziona offline.
- **Retrieval invece di fine-tuning**: più leggero da iterare, e nella pratica
  con risultati equivalenti su questo compito (vedi sotto).
- **Parsing difensivo**: gli export reali contengono caratteri Unicode
  invisibili, formati di data misti e messaggi di sistema da filtrare.
- **Filtro temporale (180 s) e controllo sull'autore precedente**: riducono gli
  accoppiamenti sbagliati dovuti ai thread intrecciati di una chat di gruppo.
- **Vettori normalizzati in anticipo**: portando tutti gli embedding a lunghezza
  1, la similarità coseno si riduce al prodotto scalare, e una singola
  moltiplicazione matrice-vettore (`numpy`) calcola tutti i punteggi in un colpo.
- **Post-processing dell'output**: il modello tende a replicare il formato degli
  esempi (prefissi con il nome, più messaggi di fila). L'output viene troncato
  alla prima riga e ripulito dai prefissi noti.

## Dal retrieval per parole chiave a quello semantico

La prima versione recuperava gli esempi con un punteggio basato sulle parole in
comune, scartando i termini troppo frequenti (un approccio in stile TF-IDF: una
parola presente in oltre il 5% delle coppie non discrimina, quindi veniva
ignorata).

Il limite era strutturale: cercando **stringhe** e non **significati**, una
domanda come *"andiamo a mangiare?"* non trovava scambi in cui si diceva
*"si esce a cena?"*, e in mancanza di corrispondenze il sistema ripiegava su
esempi casuali, inoltre la lista di stopword andava mantenuta a mano, aggiungendo
termini ogni volta che uno di essi intasava i risultati.

La versione attuale sostituisce l'intero blocco (stopword, filtro di frequenza,
conteggio punti) con la ricerca vettoriale: gli esempi recuperati sono
pertinenti anche quando la domanda è formulata con parole del tutto diverse da
quelle usate nella chat.

## Limiti e cosa ho imparato

**Il rumore nei dati è il vero collo di bottiglia.** In una chat di gruppo i
thread si intrecciano, spesso è impossibile ricostruire a quale messaggio una
persona stesse rispondendo, e una parte delle coppie risulta accoppiata male.
Nessuna tecnica di retrieval può rimediare, perché l'informazione non è presente
nei dati, il sistema riproduce fedelmente il **registro** (lunghezza,
punteggiatura, abbreviazioni), mentre la **pertinenza** resta il punto debole.

**La similarità è anche uno strumento diagnostico**, sui temi presenti in
abbondanza nel dataset i punteggi sono alti, su domande fuori distribuzione
scendono sotto 0.55, e in quel caso il modello sta di fatto improvvisando.
Vale la pena stampare i punteggi durante lo sviluppo: metà dei risultati deludenti si
spiega guardando *cosa* è stato recuperato, non la risposta generata.

**Il modello base conta più della tecnica.** A parità di prompt e di esempi, un
modello grande via API produce risultati molto più convincenti di un
modello da 8–9B in locale, perché riesce a estrarre più segnale da un contesto
rumoroso, la versione locale è una scelta consapevole per la privacy dei dati in
cambio di qualità inferiore (purtroppo).

**Il fine-tuning non è una scorciatoia.** Ho addestrato una variante con QLoRA
(LoRA su Llama 3.1 8B quantizzato a 4 bit, una epoca su ~5.000 coppie, su GPU
cloud), la loss è scesa da 5.8 a circa 2.9 e si è assestata lì: un valore alto,
che riflette proprio il rumore del dataset, il modello non può prevedere
risposte che non hanno relazione con il loro stimolo, Il risultato cattura lo
stile in modo un po' più naturale del retrieval, ma la pertinenza resta
identica, perché la causa è la stessa: con dati rumorosi il RAG rende quanto il
fine-tuning a una frazione del costo e con molta più flessibilità, per cambiare
i dati basta re-indicizzare, non riaddestrare (al posto di 40 minuti di fine-tuning
spendiamo circa 20 minuti di re-indicizzazione).
