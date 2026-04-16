# 🌐 Ramy Web Application - Complete Guide

## 📁 Documentation Files

This project now includes comprehensive documentation for running the web application:

| File | Purpose | Size |
|------|---------|------|
| `QUICK_START.md` | Quick reference - get started in 30 seconds | 1.3 KB |
| `WEBAPP_SETUP.md` | Complete setup guide with troubleshooting | 7.3 KB |
| `CHANGES_SUMMARY.md` | What was fixed and why | 3.5 KB |
| `run_webapp.bat` | Windows launcher script (double-click to run) | 1.4 KB |
| `run_webapp.sh` | Linux/macOS launcher script | 1.4 KB |
| `requirements.txt` | Updated with correct dependency versions | - |

---

## 🚀 Three Ways to Run

### Method 1: Double-Click Launcher (Easiest)

**Windows:**
```
Double-click: run_webapp.bat
```

**Linux/macOS:**
```bash
chmod +x run_webapp.sh
./run_webapp.sh
```

### Method 2: Manual Command (Recommended)

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Run server
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

### Method 3: Background Process (Windows)

```powershell
Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","webapp.main:app","--host","0.0.0.0","--port","8000" -WindowStyle Minimized
```

---

## 📦 Installation

### Quick Install (Web Only)
```bash
pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" uvicorn jinja2 markupsafe python-multipart pandas numpy
```

### Full Install (Including ML)
```bash
pip install -r requirements.txt
```

---

## 🔗 Access Points

Once running, access the application at:

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## ✅ What Was Fixed

### Dependency Issues Resolved
- ✅ FastAPI version compatibility
- ✅ Starlette version compatibility  
- ✅ Pydantic v1 vs v2 conflict
- ✅ Missing markupsafe dependency
- ✅ Missing python-multipart dependency

### Documentation Added
- ✅ Quick start guide
- ✅ Complete setup guide
- ✅ Troubleshooting section
- ✅ Launcher scripts for easy execution

---

## 📊 Application Features

### Frontend Dashboard
- Overview with sentiment distribution
- Sentiment explorer with filters
- Geographic insights by wilaya
- Aspect-based analysis
- Live sentiment analyzer
- Data export functionality

### Frontend Entrypoint (Important)
- Active UI is loaded from `webapp/templates/index.html`.
- Active stylesheet: `webapp/static/dashboard.css`.
- Active React app: `webapp/static/dashboard-app.jsx`.
- Legacy files: `webapp/static/app.js` and `webapp/static/styles.css` are archived for older UI and are not loaded by current `index.html`.

### Backend API
- RESTful API with FastAPI
- Real-time data processing
- Filtering and pagination
- CSV export
- Model prediction endpoints
- Comprehensive API documentation

---

## 🆘 Need Help?

1. **Quick fixes**: See `QUICK_START.md`
2. **Detailed guide**: See `WEBAPP_SETUP.md`
3. **What changed**: See `CHANGES_SUMMARY.md`
4. **API docs**: http://localhost:8000/docs (when running)

---

## 🎯 Verification Checklist

After installation, verify:

- [ ] Virtual environment activated
- [ ] Dependencies installed without errors
- [ ] Server starts successfully
- [ ] Can access http://localhost:8000
- [ ] Dashboard loads in browser
- [ ] API returns data correctly

---

## 📝 Quick Commands Reference

```bash
# Install dependencies
pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" uvicorn jinja2 markupsafe python-multipart pandas numpy

# Run server
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000

# Run with auto-reload (development)
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload

# Check health
curl http://localhost:8000/api/health

# Stop server
Press CTRL+C
```

---

## 🔧 Configuration

### Environment Variables (Optional)

Create `.env` file:
```env
FINETUNED_MODEL_PATH=/path/to/model
REVIEW_DATA_PATH=/path/to/data.csv
```

### Default Paths
- Data: `data/augmented/Ramy_data_augmented_target_1500.csv`
- Model: `models/runtime/ramy_h100_finetuned_model/`

---

## 🌟 Key Dependencies

```
fastapi==0.109.0      # Web framework
starlette==0.35.1     # ASGI framework
pydantic<2            # Data validation (v1.x)
uvicorn>=0.32.0       # ASGI server
jinja2>=3.1.0         # Template engine
markupsafe>=3.0.0     # HTML escaping
pandas>=2.1.0         # Data processing
numpy>=1.24.0         # Numerical computing
```

---

## 📈 Project Structure

```
Ramy/
├── webapp/
│   ├── main.py              # FastAPI application
│   ├── static/              # Frontend assets
│   │   ├── dashboard-app.jsx
│   │   ├── dashboard.css
│   │   ├── app.js           # Legacy UI (not loaded by current index.html)
│   │   ├── styles.css       # Legacy UI styles (not loaded by current index.html)
│   │   └── logo.jpg
│   └── templates/
│       └── index.html       # Main HTML template
├── data/
│   └── augmented/           # Dataset files
├── models/
│   └── runtime/             # Model files (optional)
├── requirements.txt         # Python dependencies
├── run_webapp.bat          # Windows launcher
├── run_webapp.sh           # Linux/macOS launcher
├── QUICK_START.md          # Quick reference
├── WEBAPP_SETUP.md         # Complete guide
└── CHANGES_SUMMARY.md      # Changes log
```

---

## 🚀 Production Deployment

For production use:

1. Use Gunicorn with Uvicorn workers
2. Set up reverse proxy (Nginx)
3. Enable HTTPS/SSL
4. Configure environment variables
5. Set up monitoring and logging
6. Use process manager (systemd, supervisor)

See `WEBAPP_SETUP.md` for details.

---

## 🧭 8-Line Architecture (Meeting Ready)

1. **Data**: Reviews are collected from real Algerian channels (Darija/Arabic/French mix) and stored as semicolon CSV.
2. **Train Split**: The notebook builds a leakage-free setup (train + dev + held-out test).
3. **Modeling**: AraBERT is fine-tuned, then improved with pseudo-label self-training from unlabeled feedback.
4. **Calibration**: Threshold tuning is done on dev only; final metrics are reported on held-out test.
5. **Artifacts**: Trained model/tokenizer and metrics are exported under `models/checkpoints` or `models/runtime`.
6. **Serve**: FastAPI in `webapp/main.py` exposes `/api/model/predict` and analytics endpoints.
7. **Post-Process**: Rule calibration fixes Darija edge cases (negation/question cues) after raw model output.
8. **UI**: `index.html` loads `dashboard-app.jsx` + `dashboard.css` to render the live dashboard and call API endpoints.

---

## 📅 Version History

- **v3.0.0** (April 2026) - Fixed dependencies, added documentation
- **v2.0.0** - Added web application
- **v1.0.0** - Initial release

---

## 📄 License

This project is submitted as a competition entry for AI EXPO 2026.

---

**Ready to start?** Run `run_webapp.bat` (Windows) or `./run_webapp.sh` (Linux/macOS)!
