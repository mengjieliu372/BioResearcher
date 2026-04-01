# BioResearcher

## Quick Start

### Frontend
```bash
cd frontend
npm install
npm start
```

### Backend
```bash
cd backend
python -m venv .venv
# Windows
.\\.venv\\Scripts\\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Recent Changes
- Added login/auth flow with project-level access control and superuser support.
- Set `Example (94127)` to demo-first behavior (read-only presentation path).
- Added coding result display package workflow (display files + R code + manifest JSON).
- Added global model-call queue control to reduce concurrent model contention.
- Cleaned runtime data folders and kept only `backend/app/data/94127` as current demo data.
