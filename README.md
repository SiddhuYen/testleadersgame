# World Leader Smash

A simple FaceSmash-style voting game with separate frontend and backend folders, now configured for Neon Postgres.

## Structure

- `backend/`: FastAPI API, Neon Postgres storage, CSV loading, Elo vote updates
- `frontend/`: Static HTML/CSS/JS interface for the matchup game and leaderboard

## CSV Format

The backend looks for `backend/data/leaders.csv` with this header:

```csv
name,country,photo_url
```

It also accepts your alternate headers:

```csv
countryLabel,headLabel,image
```

Rows missing any required field are skipped. If the CSV has rows, the Neon database syncs to that file on startup.

## Run Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend reads `backend/.env` and connects using `DATABASE_URL`.

API base URL: `http://127.0.0.1:8000`

## Run Frontend

Serve the `frontend/` folder with any static file server. One simple option:

```bash
cd frontend
python3 -m http.server 3000
```

Then open:

- `http://127.0.0.1:3000`
- `http://127.0.0.1:3000/leaderboard.html`
