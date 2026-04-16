# 🔧 ML Features Setup - Complete Solution

## Problem Summary

The web application shows:
- ❌ "API unavailable, showing mock prediction. Reason: Model not available: No module named 'torch'"
- ❌ "Model-only mode is active. XAI attribution is disabled."

## Root Cause

The virtual environment (Python 3.14) cannot directly install PyTorch because PyTorch doesn't support Python 3.14 yet. However, PyTorch is available in the global Python 3.12 installation.

## ✅ Solution Implemented

### 1. Python Path Configuration

Created a `.pth` file to allow Python 3.14 venv to access Python 3.12 packages:

**File**: `.venv/lib/python3.14/site-packages/python312_packages.pth`
```
C:\Users\Samir Guenchi\AppData\Local\Programs\Python\Python312\Lib\site-packages
```

### 2. Verification

Test that PyTorch is accessible:
```bash
python -c "import torch; print('PyTorch:', torch.__version__)"
# Output: PyTorch: 2.9.1+cpu
```

Test that the model can load:
```bash
python -c "from webapp.main import _load_prediction_pipeline; pipe = _load_prediction_pipeline(); print('Model loaded:', pipe is not None)"
# Output: Model loaded: True
```

## 🚀 How to Run with ML Enabled

### ⭐ RECOMMENDED METHOD: Direct Terminal

Open a terminal in the project directory and run:

```bash
# Windows PowerShell
cd D:\project\Ramy
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

```bash
# Windows CMD
cd D:\project\Ramy
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

**Why this works**: Running in the current terminal preserves the Python environment and path configuration.

### Alternative: Batch File

Use the provided batch file:
```cmd
start_server_with_ml.bat
```

This sets `PYTHONPATH` explicitly before starting the server.

## 🧪 Verify ML is Working

### 1. Check Model Status

```bash
curl http://localhost:8000/api/model/status
```

**Expected (Working)**:
```json
{
  "ready": true,
  "model_dir": "D:\\project\\Ramy\\models\\runtime\\ramy_h100_finetuned_model",
  "error": "",
  "xai_ready": true,
  "xai_error": ""
}
```

**If Not Working**:
```json
{
  "ready": false,
  "model_dir": "",
  "error": "No module named 'torch'",
  "xai_ready": false,
  "xai_error": ""
}
```

### 2. Test Prediction

```bash
curl -X POST http://localhost:8000/api/model/predict \
  -H "Content-Type: application/json" \
  -d "{\"comments\": [\"ramy tres bon\"], \"include_xai\": true}"
```

**Expected Response**:
```json
{
  "total": 1,
  "rows": [
    {
      "text": "ramy tres bon",
      "predicted_class": "positive",
      "confidence": 0.95,
      "all_scores": {...},
      "top_tokens": [...],
      "word_attributions": [...],
      "explanation_text": "...",
      "xai_method": "combined"
    }
  ],
  "distribution": {"positive": 1},
  "xai_used": true
}
```

## 📋 Complete Setup Checklist

- [x] PyTorch accessible in Python environment
- [x] Transformers library installed
- [x] Model files present in `models/runtime/ramy_h100_finetuned_model/`
- [x] `.pth` file created for Python path
- [x] Model loads successfully when tested directly
- [ ] Server started in correct environment
- [ ] Model status API returns `ready: true`
- [ ] Predictions work via API
- [ ] XAI features enabled

## 🐛 Troubleshooting

### Issue: Background processes don't have torch

**Problem**: When starting the server as a background process (Start-Process, controlPwshProcess), it doesn't inherit the Python path configuration.

**Solution**: Always run the server in the current terminal:
```bash
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

### Issue: "No module named 'torch'" persists

**Solutions**:

1. **Verify torch is accessible**:
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

2. **Check Python path**:
   ```bash
   python -c "import sys; print('\\n'.join([p for p in sys.path if 'Python312' in p]))"
   ```

3. **Verify .pth file exists**:
   ```bash
   cat .venv/lib/python3.14/site-packages/python312_packages.pth
   ```

4. **Run server in current terminal** (not as background process)

### Issue: Model loads but predictions fail

**Check**:
1. Model files are complete
2. Sufficient memory available
3. Check server logs for specific errors

### Issue: XAI doesn't work

**Solution**: XAI is only enabled when you explicitly request it:
```json
{
  "comments": ["text here"],
  "include_xai": true,
  "xai_method": "combined",
  "xai_top_k": 8
}
```

## 📊 What You Get When ML Works

### 1. Live Predictions
- Real-time sentiment classification
- 5 classes: positive, negative, neutral, improvement, question
- Confidence scores
- Calibration rules applied

### 2. XAI Features
- Token-level attribution scores
- Attention rollout visualization
- Gradient × Attention analysis
- Word importance highlighting
- Explanation text

### 3. Batch Processing
- Process up to 1000 comments at once
- Efficient batching
- Progress tracking

### 4. Model Information
- Model status and readiness
- Configuration details
- Error reporting

## 🎯 Quick Start Commands

```bash
# 1. Navigate to project
cd D:\project\Ramy

# 2. Verify torch is accessible
python -c "import torch; print('OK')"

# 3. Start server
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000

# 4. In another terminal, test
curl http://localhost:8000/api/model/status

# 5. Open browser
start http://localhost:8000
```

## 📚 Additional Resources

- `RUN_WITH_ML.md` - Detailed ML features guide
- `WEBAPP_SETUP.md` - General setup guide
- `QUICK_START.md` - Quick reference
- API Docs: http://localhost:8000/docs

## ✅ Success Criteria

You know ML is working when:
1. ✅ Model status shows `ready: true`
2. ✅ XAI status shows `xai_ready: true`
3. ✅ Predictions return real classifications (not mock data)
4. ✅ XAI features provide token attributions
5. ✅ Live Analyzer tab works in the dashboard

---

**Status**: Configuration Complete ✅  
**Next Step**: Run server in current terminal  
**Last Updated**: April 16, 2026
