# Ramy Sentiment Intelligence - Web Application Setup Guide

This guide explains how to set up and run the Ramy Sentiment Intelligence web application (frontend + backend).

---

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Windows, macOS, or Linux

---

## 🚀 Quick Start

### 1. Clone or Navigate to Project Directory

```bash
cd /path/to/Ramy
```

### 2. Create Virtual Environment (if not exists)

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Web Application Dependencies

The web application requires specific versions to work correctly. Install them using:

```bash
# Install core web dependencies
pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2"

# Install additional required packages
pip install uvicorn jinja2 markupsafe python-multipart anyio click h11
```

**Alternative: Install from requirements.txt**

If you want to install all dependencies (including ML/NLP packages):

```bash
pip install -r requirements.txt
```

**Note:** The ML packages (torch, transformers, etc.) are large and may take time to install. They are only needed if you want to use the live prediction features with the trained model.

---

## 🌐 Running the Web Application

### Method 1: Using Python Module (Recommended)

```bash
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

### Method 2: Using Start-Process (Windows - Runs in Background)

```powershell
Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","webapp.main:app","--host","0.0.0.0","--port","8000" -WorkingDirectory "D:\project\Ramy" -WindowStyle Minimized
```

**Replace** `D:\project\Ramy` with your actual project path.

### Method 3: Direct Uvicorn Command

```bash
uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

---

## 🔗 Accessing the Application

Once the server is running, you can access:

- **Main Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health
- **Alternative API Docs**: http://localhost:8000/redoc

---

## 📊 Application Features

The web application includes:

### Frontend (React-based Dashboard)
- **Overview Page**: Sentiment distribution, recent reviews, product statistics
- **Sentiment Explorer**: Filter and search reviews by sentiment, product, wilaya
- **Geographic Insights**: Sentiment analysis by Algerian wilaya
- **Aspect Analysis**: Detailed aspect-based sentiment breakdown
- **Live Analyzer**: Real-time sentiment prediction (requires trained model)

### Backend (FastAPI REST API)
- `/api/health` - Health check endpoint
- `/api/overview` - Dashboard overview statistics
- `/api/trends` - Sentiment trends over time
- `/api/geo` - Geographic sentiment analysis
- `/api/aspects` - Aspect-based sentiment analysis
- `/api/reviews` - Paginated reviews with filters
- `/api/model/predict` - Live sentiment prediction (requires model)
- `/api/model/status` - Model availability status
- `/api/export/reviews.csv` - Export filtered reviews

---

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2"
```

### Issue: "ModuleNotFoundError: No module named 'markupsafe'"

**Solution:**
```bash
pip install markupsafe
```

### Issue: "TypeError: Router.__init__() got an unexpected keyword argument"

**Solution:** This is a version compatibility issue. Make sure you have the correct versions:
```bash
pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" --force-reinstall
```

### Issue: Port 8000 is already in use

**Solution:** Either stop the existing process or use a different port:
```bash
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8001
```

### Issue: Model prediction endpoints return errors

**Solution:** The ML model files are not included in the repository due to size. The dashboard and data exploration features work without the model. To use prediction features:

1. Train the model using the notebook: `notebooks/h100-finetune-sentiment-fixed-2.ipynb`
2. Place the model in: `models/runtime/ramy_h100_finetuned_model/`
3. Or set environment variable: `FINETUNED_MODEL_PATH=/path/to/model`

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Optional: Custom model path
FINETUNED_MODEL_PATH=/path/to/your/model

# Optional: Custom data path
REVIEW_DATA_PATH=/path/to/your/data.csv
```

### Default Paths

- **Data**: `data/augmented/Ramy_data_augmented_target_1500.csv`
- **Model**: `models/runtime/ramy_h100_finetuned_model/`

---

## 📦 Minimal Installation (Dashboard Only)

If you only want to run the dashboard without ML features:

```bash
# Install only web dependencies
pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" uvicorn jinja2 markupsafe python-multipart

# Install data processing
pip install pandas numpy

# Run the server
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

---

## 🛑 Stopping the Server

### If running in terminal:
Press `CTRL+C`

### If running in background (Windows):
```powershell
# Find the process
Get-Process python | Where-Object {$_.MainWindowTitle -like "*uvicorn*"}

# Stop it
Stop-Process -Name python -Force
```

### If running in background (Linux/macOS):
```bash
# Find the process
ps aux | grep uvicorn

# Stop it (replace PID with actual process ID)
kill <PID>
```

---

## 📝 Development Mode

For development with auto-reload on code changes:

```bash
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🎯 Production Deployment

For production deployment, consider:

1. **Use Gunicorn with Uvicorn workers:**
```bash
pip install gunicorn
gunicorn webapp.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. **Set up reverse proxy (Nginx/Apache)**

3. **Use environment variables for configuration**

4. **Enable HTTPS/SSL**

5. **Set up proper logging and monitoring**

---

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Uvicorn Documentation**: https://www.uvicorn.org/
- **Project README**: See `README.md` for full project documentation

---

## 🆘 Support

If you encounter issues:

1. Check that all dependencies are installed correctly
2. Verify Python version (3.8+)
3. Ensure the data file exists at the expected path
4. Check the console output for specific error messages
5. Review the API documentation at http://localhost:8000/docs

---

## ✅ Verification Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed (fastapi, uvicorn, etc.)
- [ ] Server starts without errors
- [ ] Can access http://localhost:8000
- [ ] Dashboard loads in browser
- [ ] API health check returns 200 OK
- [ ] Data displays correctly in dashboard

---

**Last Updated**: April 2026
**Version**: 3.0.0
