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

Setezi variabilele in Railway service:
- `APIFY_TOKEN`
- `COMFY_CLOUD_API_KEY`
- `MIROFISH_API_URL` (URL-ul backend-ului MiroFish deployat)
- optional: Reddit/Twitter
- optional: `DATABASE_URL` (Neon)

## 2) Deploy MiroFish backend pe Railway

In repo MiroFish, creezi un service separat cu start command:
- `cd backend && uv run python run.py`

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
