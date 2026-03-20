# Verificare proiect – ce merge și ce mai e de făcut

Ultima verificare: ce funcționează și ce lipsește.

## ✅ Ce merge

| Componentă | Status |
|------------|--------|
| **Python & pachete** | pandas, streamlit, tweepy, praw, requests, python-dotenv – importuri OK. |
| **Dashboard principal** | `streamlit run app.py` – se încarcă (trends, TikTok, Comfy). |
| **trends.py** | Twitter + Reddit (cu fallback dacă credentials lipsesc / API-uri blocate). |
| **tiktok_trends.py** | Apify – funcțional cu `APIFY_TOKEN` și actor configurat. |
| **collect_trends.py** | Script pentru colectare zilnică (Twitter, Reddit, TikTok → CSV + grafic). |
| **Pipeline ML** | `data/processed/`: corpus.csv, topics_assigned.csv, influencers.csv – există. `run_pipeline.ps1` rulează cluster_topics → influencer_scores. |
| **Comfy – imagine** | API key setat. Workflow: există `workflow_api.json.json`; codul îl folosește automat (fallback). Node ID 6 prezent în workflow. |
| **.env** | APIFY_TOKEN, COMFY_CLOUD_API_KEY, Reddit, Twitter – completat. |

## ⚠️ Ce depinde de config / servicii

| Ce | Notă |
|----|------|
| **Twitter** | Dacă API-ul returnează 403 (plan limitat), dashboard-ul afișează doar Reddit + TikTok. |
| **Reddit** | Dacă PRAW dă 401, verifica REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET (script app, nu Devvit). |
| **TikTok (Apify)** | Actor-ul (ex. clockworks~tiktok-scraper) trebuie să aibă input valid (searchQueries, hashtags sau profiles). |

## ❌ Ce mai e de făcut (opțional)

| Pas | Acțiune |
|-----|--------|
| **Comfy – video** | Pentru „Generează reel”: pune **`workflow_video_api.json`** (sau `workflow_video_api.json.json`) în rădăcina proiectului. Fără el, doar generarea de imagine va merge. |
| **Workflow imagine – nume clar** | Ai `workflow_api.json.json`. Poți redenumi în `workflow_api.json` ca să fie consistent cu documentația. |
| **requirements.txt** | Adăugat **tweepy** și **praw**; rulează `pip install -r requirements.txt` dacă le lipseau. |

## Cum verifici rapid

```powershell
cd "c:\Users\octav\Desktop\social trends"
# Pachete
pip install -r requirements.txt
# Dashboard
streamlit run app.py
# Colectare (opțional)
python collect_trends.py
# Pipeline (clustering + scoring)
.\run_pipeline.ps1
```

---

**Rezumat:** Dashboard-ul, TikTok, Comfy (imagine) și pipeline-ul de date sunt ok. Pentru Comfy video mai trebuie doar fișierul workflow video în root. Twitter/Reddit pot fi indisponibile din cauza planului API; aplicația continuă cu celelalte surse.
