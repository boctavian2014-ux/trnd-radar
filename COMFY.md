# Comfy Cloud – integrare

Generare **imagini** și **video (reels)** din topic + descriere. Folosit în dashboard principal și în dashboard-ul de influenceri.

## Ce mai trebuie ca Comfy să meargă

| Pas | Status | Ce faci |
|-----|--------|--------|
| 1. API Key în `.env` | ✅ (ai setat) | `COMFY_CLOUD_API_KEY=...` |
| 2. Workflow imagine | ✅ | Fișier **`workflow_api.json`** în root. (Dacă ai doar `workflow_api.json.json`, codul îl găsește automat.) |
| 3. Workflow video (opțional) | ❌ lipsește | Pentru reel: **`workflow_video_api.json`** (sau `workflow_video_api.json.json`) în același folder. |
| 4. Node ID în workflow | Depinde | În JSON, un node trebuie să aibă input de tip text. Codul caută implicit **node ID `"6"`**, input **`"text"`**. Dacă workflow-ul tău are alt ID, folosește dashboard-ul de influenceri și setează acolo Node ID / Input key. |

**Rezumat:** După ce pui `workflow_api.json` (și eventual `workflow_video_api.json`) în folderul proiectului, secțiunea Comfy din dashboard va putea rula. Fără aceste fișiere vei primi „Lipseste fisierul workflow” / FileNotFoundError.

## Unde apare

- **Dashboard principal** (`streamlit run app.py`) – secțiunea „Comfy Cloud” la final: Topic + Descriere → Imagine / Reel.
- **Dashboard influenceri** (`streamlit run src/dashboards/influencers_app.py`) – cover și reels pentru influencerul ales.

## Configurare

1. **API Key**  
   [cloud.comfy.org](https://cloud.comfy.org) → Settings/API → copiază cheia. În `.env`:
   ```env
   COMFY_CLOUD_API_KEY=cheia_ta
   ```

2. **Workflow-uri** (în rădăcina proiectului, lângă `app.py`):
   - `workflow_api.json` – imagine (text → model → Save Image).
   - `workflow_video_api.json` – video (ex. AnimateDiff).

   În Comfy UI: construiește workflow → Export → **format API** → salvează cu numele de mai sus.

3. **Node pentru prompt**  
   Implicit: node ID **`"6"`**, input **`"text"`**. Dacă workflow-ul tău e diferit:
   - În **dashboard principal**: secțiunea Video/Reel → expander „Avansat: Node ID / Input”.
   - În **dashboard influenceri**: câmpurile Node ID și Input key.
   - Mai jos: **pas cu pas** cum găsești Node ID și Input key în JSON și cum le pui în dashboard.

4. **Verificare**  
   Repornește `streamlit run app.py` → secțiunea Comfy: dacă cheia e setată, apar câmpurile Topic/Descriere și butoanele Imagine/Reel.

## Node ID pentru Reel – pas cu pas

**Pentru workflow-ul din acest proiect** (`workflow_api.json` / `workflow_video_api.json`):
- **Node ID prompt:** `6` (nodul CLIP Text Encode pentru prompt pozitiv)
- **Input key:** `text`

Le poți seta în dashboard la Video/Reel → „Avansat: Node ID / Input (workflow video)”; valorile implicite sunt deja 6 și text.

---

1. **Deschide fișierul workflow video**  
   În Explorer (sau în Cursor): du-te în folderul proiectului (`social trends`) și deschide **`workflow_video_api.json`** sau **`workflow_video_api.json.json`** cu un editor de text (Notepad, VS Code, Cursor).

2. **Caută în fișier nodurile care au prompt (text)**  
   - Apasă Ctrl+F și caută **`"text"`** (cu ghilimele).  
   - Sau caută **`CLIPTextEncode`** – de obicei acolo e nodul de prompt.  
   - Vei vedea blocuri de forma:
     ```json
     "2": {
       "inputs": {
         "text": "aurora, pink princess...",
         "clip": ["4", 1]
       },
       "class_type": "CLIPTextEncode"
     }
     ```
     Aici **`"2"`** (cheia din stânga) este **Node ID**, iar **`"text"`** (din `inputs`) este **Input key**.

3. **Notează Node ID și Input key**  
   - **Node ID** = numărul (sau string-ul) care e **cheia** obiectului (ex. `2`, `6`). În exemplu de mai sus e **2**.  
   - **Input key** = numele câmpului unde e scris promptul; în aproape toate cazurile e **text**.

4. **Deschide dashboard-ul**  
   Pornește aplicația: `streamlit run app.py`. În browser, scroll până la secțiunea **„Comfy Cloud – imagine / video”**.

5. **Completează Topic și Descriere**  
   Scrie ce vrei în „Topic” și „Descriere prompt” (ex. „Viral Romania”, „Clip vertical, stil modern”).

6. **Deschide setările pentru reel**  
   La **„Video / Reel”**, dă click pe expanderul **„Avansat: Node ID / Input (workflow video)”**.

7. **Pune valorile din JSON**  
   - În **„Node ID prompt”**: tastezi exact ID-ul găsit (ex. **2** sau **6**).  
   - În **„Input key”**: tastezi **text** (sau alt nume dacă în JSON e diferit).

8. **Generează reel**  
   Apasă butonul **„Genereaza reel”**. Aplicația va injecta promptul tău (Topic + Descriere) în nodul ales din workflow.

---

## Erori frecvente

| Mesaj | Soluție |
|-------|--------|
| COMFY_CLOUD_API_KEY nu este setat | Adaugă cheia în `.env`, repornește app. |
| Node ID 6 nu exista | Verifică în JSON ID-ul node-ului de text; setează-l în dashboard influenceri. |
| Lipseste fisierul workflow | Pune `workflow_api.json` / `workflow_video_api.json` în root. |
| Timeout / job failed | Verifică workflow-ul și status-ul job-urilor pe cloud.comfy.org. |

## Fișiere

- `src/comfy/comfy_client.py` – API Comfy Cloud.
- `src/comfy/comfy_topics.py` – `generate_topic_image()`, `generate_topic_reel()`.
- `app.py` – secțiunea Comfy în dashboard principal.
- `src/dashboards/influencers_app.py` – Comfy pentru influenceri.
