# Backend Startup (Local / Ubuntu)

Use a single backend entrypoint only:

- `backend/main.py` (which runs `app.main:app`)

## Local start

```powershell
cd backend
python main.py
```

## Ubuntu start (recommended)

```bash
cd backend
python3 main.py
```

## Notes

- Do not start a second uvicorn process with another app path.
- Frontend proxy should target `http://127.0.0.1:8000`.
- Keep `backend/app/data/94127` for Example read-only demo display.
