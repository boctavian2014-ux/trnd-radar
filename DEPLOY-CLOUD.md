# Deploy fara terminale locale (Railway + Neon)

Obiectiv: sa nu mai depinzi de terminalele locale. Rulezi tot in cloud.

## Arhitectura

- Service 1: **social-trends-dashboard** (acest repo) pe Railway
  - Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`
- Service 2: **mirofish-backend** (repo MiroFish) pe Railway
  - Start command: `cd backend && uv run python run.py`
- Service 3: **mirofish-frontend** (repo MiroFish) pe Railway (optional)
  - Start command: `cd frontend && npm run dev -- --host 0.0.0.0 --port $PORT`
- Database: **Neon Postgres**

## 1) Deploy social-trends-dashboard pe Railway

In repo `social trends` ai deja:
- `Procfile`
- `railway.toml`
- `.env.cloud.example`

### Pas cu pas (Railway UI)

1. **Push** codul pe GitHub (repo-ul conectat la Railway, ex. `trnd-radar`).
2. In Railway: **Project** → serviciul dashboard → **Settings**.
3. **Source**: repo + branch `main` (sau ce folosesti).
4. **Root Directory**: lasa gol (root repo) daca `app.py` e in radacina.
5. **Build**: builder **NIXPACKS** (deja in `railway.toml`).  
   - **Custom Build Command**: optional `pip install -r requirements.txt` daca build-ul nu instaleaza deps singur.  
   - Nu pune comenzi MiroFish (`uv sync`) aici — alea sunt pentru alt serviciu.
6. **Deploy → Custom Start Command**: trebuie sa fie (sau echivalent in `railway.toml`):
   ```bash
   streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
   ```
7. **Pre-deploy step**: lasa **gol / dezactivat** daca nu ai nevoie explicit (altfel deploy-ul pica acolo).
8. **Networking → Generate Domain** pentru URL public.
9. **Target port**: foloseste portul pe care il seteaza Railway pentru proces (Streamlit foloseste `$PORT` din start command).

### Variabile de mediu (Railway → Variables)

Obligatorii pentru functii concrete:
- `APIFY_TOKEN` — TikTok / Apify
- `COMFY_CLOUD_API_KEY` — Comfy Cloud
- `PERPLEXITY_API_KEY` — Auto Research (Perplexity)
- `PERPLEXITY_PRESET` — optional, default recomandat: `fast-search`
- `PERPLEXITY_MODEL` — optional (lasa gol pentru preset-only, sau pune model daca Perplexity cere)

MiroFish (daca ai backend separat deployat):
- `MIROFISH_API_URL` — URL public, **fara** `/` la final (ex. `https://mirofish-production.up.railway.app`)

Optional:
- Reddit/Twitter (vezi `.env.cloud.example`)
- `DATABASE_URL` (Neon Postgres, cu `?sslmode=require`)

## 2) Deploy MiroFish backend pe Railway

In repo MiroFish, creezi un service separat:
- **Root Directory**: `backend`
- **Start command** (port Railway):
  ```bash
  export FLASK_PORT=${PORT:-5001} && uv run python run.py
  ```
- **Build** (exemplu): `curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH" && uv sync --frozen`

Env obligatoriu:
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL_NAME`
- `ZEP_API_KEY`

Daca ai 401/403 pe model:
- cheia e invalida sau modelul nu e activat in provider.

## 3) Leaga dashboard-ul de MiroFish cloud

In service-ul social-trends-dashboard seteaza:
- `MIROFISH_API_URL=https://<mirofish-backend>.up.railway.app`

In dashboard, la sectiunea MiroFish, URL API poate ramane implicit daca env este setat.

## 4) Neon

Ai deja proiectul Neon creat.
- Setezi `DATABASE_URL` in Railway pentru service-urile care au nevoie de DB.

## 5) Verificare finala

- Dashboard URL: deschis in browser fara local terminal
- Endpoint MiroFish health: `<MIROFISH_API_URL>/health`
- In dashboard, sectiunea MiroFish trebuie sa arate "backend pornit"

## Rezultat

Dupa deploy cloud, poti inchide laptopul si aplicatia ramane online.
