# Agent Cognitiv CivicAID

## Descriere

Agent cognitiv funcțional care folosește arhitectura **OpenAI Functions Agent** pentru a asambla componentele într-un sistem cognitiv funcțional.

## Arhitectură

### Logica de Execuție

1. **Input**: User Message
2. **LLM Processing**: GPT-4o analizează input-ul și prompt-ul de sistem
3. **Router (Decizie)**:
   - Are nevoie de lege? → Cheamă `consult_legislation`
   - Are nevoie de adresă? → Cheamă `get_institution_address`
   - Este doar conversație ("Salut")? → Răspunde direct
4. **Action**: Execută tool-ul selectat
5. **Observation**: Primește rezultatul (text din lege sau rânduri din SQL)
6. **Final Response**: Sintetizează observația într-un răspuns natural pentru utilizator

## Structură

```
app/agent/
├── __init__.py      # Exportă Agent class
├── agent.py         # Logica principală a agentului
├── tools.py         # Definiții tool-uri pentru OpenAI Functions
└── README.md        # Această documentație
```

## Tool-uri Disponibile

### 1. `consult_legislation`
Consultă legislația română pentru a găsi informații despre legi, articole, reglementări și drepturi.

**Când se folosește:**
- Întrebări despre legi
- Întrebări despre drepturi legale
- Întrebări despre proceduri legale
- Orice aspect juridic

### 2. `get_institution_address`
Găsește adrese, program de lucru și informații de contact pentru instituții publice românești.

**Când se folosește:**
- Întrebări despre unde să meargă
- Întrebări despre adrese
- Întrebări despre program de lucru
- Întrebări despre contact pentru instituții

## Utilizare

### Mod CLI (un singur mesaj):
```bash
python agent_main.py "Ce drepturi am ca pensionar?"
```

### Mod Interactiv:
```bash
python agent_main.py
```

### Programatic:
```python
from app.agent import Agent

agent = Agent()
response = agent.chat("Ce drepturi am ca pensionar?")
print(response)
```

## Exemple

### Exemplu 1: Conversație simplă
```
👤 Utilizator: Salut!
🤖 Agent: Salut! Cu ce te pot ajuta astăzi?
```

### Exemplu 2: Întrebare despre legi
```
👤 Utilizator: Ce drepturi am ca pensionar cu pensie de 2000 de lei?
🤖 Agent: [Folosește consult_legislation și răspunde cu informații despre drepturi]
```

### Exemplu 3: Întrebare despre instituții
```
👤 Utilizator: Unde trebuie să mă duc să depun cererea de pensie?
🤖 Agent: [Folosește get_institution_address și răspunde cu adrese]
```

## Configurare

Agentul folosește variabila de mediu `OPENAI_API_KEY` din fișierul `.env`.

Modelul implicit este `gpt-4o`, dar poate fi schimbat:
```python
agent = Agent(model="gpt-4o-mini", temperature=0.3)
```

## Istoric Conversație

Agentul menține automat istoricul conversației pentru context. Poți șterge istoricul:
```python
agent.clear_history()
```

## Avantaje

1. **Decizie automată**: Agentul decide automat ce tool să folosească
2. **Multi-turn**: Poate folosi mai multe tool-uri în același răspuns
3. **Context**: Menține contextul conversației
4. **Natural**: Răspunsurile sunt sintetizate într-un mod natural

