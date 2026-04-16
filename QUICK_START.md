# 🚀 Quick Start - Ramy Web Application

## One-Command Setup & Run

### Windows (PowerShell)

```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies (first time only)
pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" uvicorn jinja2 markupsafe python-multipart pandas numpy

# 3. Run the server
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

### Linux/macOS (Bash)

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install dependencies (first time only)
pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" uvicorn jinja2 markupsafe python-multipart pandas numpy

# 3. Run the server
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

---

## Access the Application

Open your browser and go to: **http://localhost:8000**

---

## Stop the Server

Press `CTRL+C` in the terminal

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Module not found | `pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" uvicorn jinja2 markupsafe` |
| Port already in use | Change port: `--port 8001` |
| Permission denied | Run as administrator or use `sudo` (Linux/macOS) |

---

## Full Documentation

See `WEBAPP_SETUP.md` for complete setup guide.
