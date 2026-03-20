# trnd-radar

Social trends dashboard with:
- Twitter/Reddit/TikTok trend aggregation
- Comfy Cloud image/video generation
- MiroFish API integration (simulation/report flow in RO UI)
- Perplexity API auto-research with citations

## Quick Start (local)

```powershell
cd C:\Users\octav\Desktop\social trends
pip install -r requirements.txt
streamlit run app.py
```

Dashboard: `http://localhost:8501`

### Quick Start (local + MiroFish auto-start)

If you also have local MiroFish at `C:\Users\octav\Desktop\MiroFish`, run:

```powershell
cd C:\Users\octav\Desktop\social trends
python run_local_with_mirofish.py
```

This starts:
- MiroFish backend (`uv run python run.py` in `MiroFish\backend`)
- Streamlit dashboard with `MIROFISH_API_URL=http://localhost:5001`

## Cloud Deploy (Railway + Neon)

This repo includes:
- `Procfile`
- `railway.toml`
- `.env.cloud.example`
- `DEPLOY-CLOUD.md`

### 1) Deploy dashboard service on Railway

Start command (already configured):

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

Set environment variables in Railway:
- `APIFY_TOKEN`
- `COMFY_CLOUD_API_KEY`
- `MIROFISH_API_URL` (your deployed MiroFish backend URL)
- `PERPLEXITY_API_KEY`
- optional: `PERPLEXITY_MODEL` (default `sonar`)
- optional: Reddit/Twitter credentials
- optional: `DATABASE_URL` (Neon)

### 2) Neon Postgres

Create DB in Neon and copy connection string to:
- `DATABASE_URL`

Use SSL mode require:
- `...?sslmode=require`

### 3) MiroFish backend (separate service)

Deploy MiroFish backend separately (Railway) and set:
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL_NAME`
- `ZEP_API_KEY`

Then set this repo var:
- `MIROFISH_API_URL=https://<your-mirofish-backend>.up.railway.app`

## Notes

- `.env` is ignored by git.
- `workflow_api.json` is used for Comfy image workflow.
- For reel generation, add `workflow_video_api.json` in project root.
