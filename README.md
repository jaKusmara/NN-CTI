# NN-CTI

Projekt na testovanie modelu **Llama 3 cez Ollama** nad benchmarkom **CTIBench** na predmet Neuronove Siete.

## O projekte

Tento projekt slúži na:
- načítanie `.tsv` súborov benchmarku CTIBench,
- odoslanie promptov do lokálne bežiaceho modelu cez **Ollama API**,
- uloženie odpovedí modelu do výstupných `.csv` súborov.

Aktuálne sa testujú tieto súbory:
- `cti-mcq.tsv`
- `cti-rcm.tsv`
- `cti-rcm-2021.tsv`
- `cti-vsp.tsv`
- `cti-ate.tsv`

Výstupy sa ukladajú do priečinka vo formáte:

```text
outputs_<meno>/
```
---

## Požiadavky

Pred spustením je potrebné mať nainštalované:

- **Python 3.10+**
- **Ollama**
- Python knižnice:
  - `pandas`
  - `requests`

---

## Inštalácia

### 1. Klonovanie alebo otvorenie projektu

Uisti sa, že si v koreňovom priečinku projektu:

```bash
cd NN-CTI
```

---

### 2. Vytvorenie virtuálneho prostredia

#### Windows
```bash
python -m venv .venv
```

#### Aktivácia vo Windows CMD
```bash
.venv\Scripts\activate.bat
```

#### Aktivácia vo Windows PowerShell
```powershell
.venv\Scripts\Activate.ps1
```

---

### 3. Inštalácia Python balíčkov

```bash
pip install pandas requests
```

---

## Inštalácia a spustenie Ollama

### 1. Nainštaluj Ollamu
Stiahni a nainštaluj Ollamu z oficiálnej stránky.

### 2. Stiahni model
V termináli spusti:

```bash
ollama run llama3
```

Pri prvom spustení sa model stiahne.  
Po stiahnutí môžeš Ollamu nechať bežať.

### 3. Overenie, že Ollama funguje
V novom termináli skús:

```bash
curl http://localhost:11434/api/tags
```

Ak všetko funguje, uvidíš zoznam dostupných modelov.

---

## Spustenie skriptu

Spusti hlavný skript:

```bash
python ctibench.py
```

Skript:
1. načíta všetky zadané `.tsv` súbory,
2. pošle každý `Prompt` do modelu `llama3:8b` / `llama3:70b`,
3. získa odpoveď,
4. uloží výsledky do `.csv`.

---

## Štruktúra projektu

Príklad štruktúry:

```text
NN-CTI/
│
├── .venv/
├── ctibench.py
├── cti-mcq.tsv
├── cti-rcm.tsv
├── cti-rcm-2021.tsv
├── cti-vsp.tsv
├── cti-ate.tsv
├── outputs_markus/
├── README.md
└── .gitignore
```

---

## Konfigurácia skriptu

V súbore `ctibench.py` je možné upraviť:

### Meno používateľa / názov výstupného priečinka
```python
NAME = "name"
```

### Použitý model
```python
MODEL = "llama3:8b"
MODEL = "llama3:70b"
```

### Zoznam vstupných súborov
```python
INPUT_FILES = [
    "cti-mcq.tsv",
    "cti-rcm.tsv",
    "cti-rcm-2021.tsv",
    "cti-vsp.tsv",
    "cti-ate.tsv"
]
```

---

## Výstupy

Pre každý `.tsv` súbor sa vytvorí samostatný `.csv` výsledok.

Príklad:

```text
outputs_name_model/cti-mcq-res.csv
outputs_name_model/cti-rcm-res.csv
outputs_name_model/cti-rcm-2021-res.csv
outputs_name_model/cti-vsp-res.csv
outputs_name_model/cti-ate-res.csv
```

Každý výstup obsahuje typicky stĺpce:
- `Prompt`
- `GT`
- `Prediction`

---

## Autor

Projekt `NN-CTI` slúži na experimenty s benchmarkom CTIBench a lokálnym LLM modelom cez Ollama.
