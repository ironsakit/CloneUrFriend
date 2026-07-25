# WhatsApp Style Clone

Sistema RAG locale che genera risposte imitando lo stile di scrittura di una
persona specifica, appreso dai suoi messaggi WhatsApp. Gira interamente offline
con [Ollama](https://ollama.com) — nessun dato lascia il computer.

> **Progetto di apprendimento.** I dati della chat usati per costruire il dataset
> sono privati e **non inclusi** in questo repository. Per eseguirlo serve un
> proprio export di WhatsApp.

## Come funziona

Il pipeline ha due fasi:

**1. Parsing (`parser.py`)**
L'export `.txt` della chat viene ripulito (caratteri Unicode invisibili,
allegati, messaggi di sistema) e trasformato in coppie *stimolo → reazione*: per
ogni messaggio scritto dalla persona target, il messaggio immediatamente
precedente diventa lo "stimolo" e il suo messaggio la "reazione". Le coppie
vengono tenute solo se la risposta è arrivata entro 30 secondi, per ridurre gli
accoppiamenti sbagliati dovuti ai thread intrecciati di una chat di gruppo.

**2. Retrieval + generazione (`clone.py`)**
Per ogni domanda, le coppie più pertinenti vengono recuperate con un punteggio
basato sulle parole chiave (un approccio in stile TF-IDF: le parole troppo comuni
vengono scartate, così contano solo i termini distintivi). Le coppie recuperate
vengono inserite nel prompt come esempi di stile, e Llama 3.1 (8B) via Ollama
genera la risposta.

## Utilizzo

```bash
pip install -r requirements.txt
ollama pull llama3.1:8b
```

1. Esporta una chat WhatsApp come `.txt` e mettila in `data/chat.txt`
2. Apri `parser.py` e imposta `YOU` con il nome esatto della persona da clonare
3. Costruisci il dataset:
   ```bash
   python parser.py
   ```
4. Apri `clone.py`, imposta `YOU`, `CHARACTERISTIC` e `YOUR_MODEL`, poi esegui:
   ```bash
   python clone.py
   ```

Il formato dei dati atteso è mostrato in `output_json/esempio_dati.json`.

## Configurazione

Prima di eseguire, vanno impostati alcuni valori (i *placeholder*) in cima ai
due file.

**In `parser.py`:**

| Variabile | Cosa mettere |
|-----------|--------------|
| `FILE_CHAT` | Percorso dell'export `.txt` (es. `data/chat.txt`) |
| `YOU` | Nome **esatto** della persona da clonare, come appare nella chat (attenzione a maiuscole ed eventuali emoji nel nome) |
| `EXCLUDED_PEOPLE` | Lista di persone da ignorare del tutto (bot, "Meta AI", partecipanti non voluti) |
| `DISCARD` | Parole o link che fanno scartare un messaggio |

**In `clone.py`:**

| Variabile | Cosa mettere |
|-----------|--------------|
| `YOU` | Deve **combaciare esattamente** con quello impostato in `parser.py` |
| `CHARACTERISTIC` | Breve descrizione della persona, inserita nel prompt (es. `"un ragazzo ironico di 20 anni"`). Può restare vuota |
| `YOUR_MODEL` | Il modello Ollama da usare (vedi sotto) |

### Scelta del modello

`YOUR_MODEL` accetta **qualsiasi modello disponibile in Ollama**, non solo
`llama3.1:8b`. Basta averlo scaricato prima con `ollama pull <modello>` e
inserire lo stesso nome nella variabile. Per esempio: `llama3.1:8b`,
`mistral-nemo`, `gemma2:9b`, `qwen2.5:7b`.

La scelta è un compromesso tra qualità e hardware:
- **Modelli piccoli** (7–8B): veloci, girano su GPU con poca VRAM (~8 GB), ma
  meno accurati.
- **Modelli grandi** (12B+): più capaci sullo stile e sul linguaggio, ma
  richiedono più VRAM. Oltre la capacità della GPU girano su CPU e diventano
  molto lenti.

Conviene scegliere il modello più grande che gira fluido sulla propria scheda.

## Nota sulla lingua

Il progetto è pensato per chat in **italiano**. Il retrieval usa una lista di
*stopword* (parole comuni da ignorare) scritta in italiano, dentro la funzione
`retrieval` in `clone.py`. Per clonare una persona che scrive in un'altra lingua
è necessario **sostituire la lista `STOPWORD`** con le parole comuni di quella
lingua (articoli, preposizioni, congiunzioni, ausiliari), altrimenti il filtro
scarterebbe i termini sbagliati e il retrieval peggiorerebbe.

## Scelte tecniche

- **Locale (Ollama) invece di un'API cloud**: i messaggi sono privati e non
  devono uscire dal computer. Nessuna API key, nessuna quota, funziona offline.
- **Retrieval invece di fine-tuning**: più leggero da iterare, e sufficiente a
  catturare lo stile senza riaddestrare un modello.
- **Parsing difensivo**: gli export reali contengono caratteri Unicode
  invisibili, formati di data misti e messaggi di sistema da filtrare.
- **Finestra di 30 secondi**: scambia quantità per qualità — meno coppie, ma
  molto più probabilmente accoppiamenti domanda/risposta autentici.

## Limiti e cosa ho imparato

Il sistema riproduce fedelmente il **registro** (lunghezza dei messaggi,
punteggiatura, abbreviazioni), ma la **pertinenza contestuale** è limitata da un
problema strutturale: in una chat di gruppo i thread si intrecciano, e spesso è
impossibile ricostruire a quale messaggio una persona stesse effettivamente
rispondendo. Questo introduce rumore nel dataset che nessuna tecnica di retrieval
può eliminare — perché l'informazione semplicemente non è presente nei dati.

Il retrieval per parole chiave inoltre non riconosce i sinonimi: cerca stringhe,
non significati. Chiedere "andiamo a mangiare?" non trova "si esce a cena?".

Il clone funziona meglio sui temi dove il dataset è denso e le domande
assomigliano a cose realmente dette nella chat. È debole sulle domande che
richiedono informazioni fattuali sulla vita della persona, che il sistema non
possiede.

### Possibili sviluppi futuri
- **Embedding semantici** per un retrieval basato sul significato invece che
  sulle parole esatte
- **Fine-tuning (LoRA)** per assorbire lo stile nei pesi del modello, più adatto
  del retrieval a catturare un registro pervasivo

## Stack

Python 3 · Ollama (Llama 3.1 8B) · nessuna dipendenza cloud
