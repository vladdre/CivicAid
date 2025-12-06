# 🔢 Cum Funcționează Embeddings-urile și Vectorii

## Procesul de Creare a Vectorilor

### 1. **Încărcare PDF-uri** (`ingest_laws.py`)
```
PDF → PyPDFLoader → Text brut
```

### 2. **Segmentare în Chunks**
```
Text lung → RecursiveCharacterTextSplitter → Chunks de 1000 caractere
```
- Fiecare chunk = o bucată de text din lege
- Overlap de 200 caractere pentru a păstra contextul

### 3. **Creare Embeddings (Vectorizare)**
```
Chunk text → OpenAIEmbeddings (text-embedding-3-small) → Vector numeric
```

**Ce se întâmplă:**
- Textul "accident de mașină" → devine un vector de ~1536 numere
- Fiecare cuvânt/expresie are o "poziție" în spațiul vectorial
- Texte similare au vectori similari (aproape în spațiu)

**Model folosit:** `text-embedding-3-small`
- Dimensiune vector: 1536
- Cost: foarte mic
- Calitate: bună pentru text românesc

### 4. **Stocare în ChromaDB**
```
Vector + Metadata → ChromaDB → data/vector_store/
```
- Fiecare chunk este salvat cu:
  - Vectorul său (embedding)
  - Textul original (page_content)
  - Metadata (sursa, calea fișierului)

## Procesul de Căutare

### 1. **Query de la Utilizator**
```
"Am avut un accident de mașină"
```

### 2. **Creare Embedding pentru Query**
```
Query text → OpenAIEmbeddings (ACELAȘI MODEL!) → Vector query
```
**IMPORTANT:** Trebuie să folosești **ACELAȘI MODEL** (`text-embedding-3-small`) 
ca la creare, altfel vectorii nu vor fi compatibili!

### 3. **Căutare Similaritate**
```
Vector query → Comparare cu toți vectorii din store → Top K cele mai apropiate
```

**Algoritm:** Cosine Similarity
- Calculează distanța între vectorul query și fiecare vector din store
- Returnează cele mai apropiate (scor mai mic = mai relevant)

### 4. **Rezultate**
```
Top K chunks → Text original + Metadata → Afișare utilizator
```

## De Ce Rezultatele Pot Să Nu Fie Relevante?

### ❌ Problema 1: Model Diferit
**Sintom:** Rezultate complet nerelevante
**Cauză:** Folosești un model diferit la căutare decât la creare
**Soluție:** Verifică că ambele folosesc `text-embedding-3-small`

### ❌ Problema 2: Query Prea Optimizat
**Sintom:** Rezultate relevante dar nu pentru ceea ce ai întrebat
**Cauză:** LLM-ul schimbă prea mult sensul query-ului
**Soluție:** Dezactivează optimizarea (`use_optimization=False`)

### ❌ Problema 3: Vector Store Gol sau Incomplet
**Sintom:** Nu găsește nimic sau găsește doar din anumite surse
**Cauză:** Nu ai rulat `ingest_laws.py` sau PDF-urile nu conțin informații relevante
**Soluție:** Rulează `python scripts/ingest_laws.py` și verifică PDF-urile

### ❌ Problema 4: Chunks Prea Mici sau Prea Mari
**Sintom:** Rezultate parțiale sau fără context
**Cauză:** `chunk_size=1000` poate fi prea mic/mare pentru anumite legi
**Soluție:** Ajustează `CHUNK_SIZE` în `ingest_laws.py`

## Verificare și Debug

### Script de Diagnostic
```bash
python tests/debug_embeddings.py
```

Acest script verifică:
- ✓ Modelul de embeddings folosit
- ✓ Conținutul vector store-ului
- ✓ Testează căutări simple
- ✓ Verifică crearea embeddings-urilor

### Verificare Manuală

1. **Verifică modelul:**
   ```python
   embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
   # Trebuie să fie ACELAȘI în ingest_laws.py și find_law.py
   ```

2. **Verifică conținutul:**
   ```bash
   python tests/test_vector_store.py
   ```

3. **Verifică scorurile:**
   - Folosește `similarity_search_with_score()` pentru a vedea relevanța
   - Scoruri mici (< 0.5) = foarte relevante
   - Scoruri mari (> 1.0) = puțin relevante

## Best Practices

1. **Folosește același model** pentru creare și căutare
2. **Testează fără optimizare** mai întâi (`use_optimization=False`)
3. **Verifică scorurile** pentru a înțelege relevanța
4. **Re-indexează** dacă adaugi PDF-uri noi
5. **Folosește query-uri clare** - "accident de mașină" > "am avut o problemă"

## Exemplu de Flux Complet

```
1. User: "Am avut un accident de mașină"
   ↓
2. Query embedding: [0.123, -0.456, 0.789, ...] (1536 numere)
   ↓
3. Comparare cu toți vectorii din store
   ↓
4. Top 5 cele mai apropiate:
   - Chunk 1: "ARTICOLUL 1356 - Răspundere civilă pentru daune..." (score: 0.23)
   - Chunk 2: "Accidente rutiere - procedură..." (score: 0.31)
   - ...
   ↓
5. Return: Textul original din chunks + metadata
```

