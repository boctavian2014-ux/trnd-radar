# Structura de foldere – Social Trends

```
social trends/
├── .cursorrules
├── .env
├── .env.example
├── .vscode/
│   └── settings.json
├── app.py                 # Entry Streamlit (dashboard principal)
├── collect_trends.py      # Colectare zilnica Twitter + Reddit + TikTok
├── COMFY.md               # Ghid integrare Comfy Cloud
├── requirements.txt
├── run.ps1                # Pornire dashboard
├── run_pipeline.ps1       # Pipeline: clustering → scoring → dashboard
├── setup-scheduler.ps1    # Windows Task Scheduler
├── tiktok_trends.py       # Apify TikTok trends
├── trends.py              # Twitter + Reddit + logic dashboard
├── VERIFICARE.md          # Raport verificare proiect
├── workflow_api.json.json # Workflow Comfy (imagine)
├── Live Portrait Workflow OpalSky.json
├── Workflow_Screen_Shot.png
│
├── data/
│   ├── social_trends_*.csv      # Exporturi colectare
│   ├── social_trends_latest.csv
│   ├── charts/
│   │   └── top_trends_*.png
│   └── processed/
│       ├── corpus.csv           # Input clustering
│       ├── topics_assigned.csv  # Output clustering
│       ├── topic_terms.csv
│       └── influencers.csv      # Output scoring
│
├── logs/
│   └── scheduler.log
│
├── src/
│   ├── comfy/
│   │   ├── comfy_client.py   # API Comfy Cloud
│   │   └── comfy_topics.py    # generate_topic_image, generate_topic_reel
│   ├── dashboards/
│   │   └── influencers_app.py # Dashboard influenceri + Comfy
│   ├── influencers/
│   │   └── influencer_scores.py
│   └── topics/
│       └── cluster_topics.py
│
├── Example Videos/        # Clipuri exemplu
├── social-trends202/      # (subproiect Devvit/Reddit)
├── trend-scout-ro/        # (subproiect)
└── waoe123/               # (subproiect Devvit)
```

## Legenda

| Folder / fișier | Rol |
|-----------------|-----|
| **app.py** | Pornește dashboard-ul: `streamlit run app.py` |
| **data/processed/** | Date pentru pipeline: corpus → topics → influencers |
| **src/comfy/** | Integrare Comfy Cloud (imagini + video) |
| **src/dashboards/influencers_app.py** | Dashboard influenceri + generare cover/reels |
| **src/topics/** | Clustering pe texte (TF-IDF + KMeans) |
| **src/influencers/** | Scoruri și metrici influenceri |
