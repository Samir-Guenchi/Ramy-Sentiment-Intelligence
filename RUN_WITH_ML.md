# 🚀 Running Ramy Web App with ML/XAI Features

## ✅ ML Dependencies Configured

The following have been set up:
- ✅ PyTorch 2.9.1+cpu (from global Python 3.12)
- ✅ Transformers 4.57.3
- ✅ Model files present in `models/runtime/ramy_h100_finetuned_model/`
- ✅ Python path configured to access ML libraries

## 🎯 How to Run with ML Features Enabled

### Method 1: Direct Command (Recommended)

Open a terminal in the project directory and run:

```bash
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

This will:
- Load the fine-tuned sentiment model
- Enable live predictions
- Enable XAI (explainable AI) features
- Provide full API functionality

### Method 2: Using the Batch File

Double-click: `start_server_with_ml.bat`

Or run from command line:
```cmd
start_server_with_ml.bat
```

### Method 3: PowerShell

```powershell
cd D:\project\Ramy
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

## 🔍 Verify ML Features are Working

After starting the server, check the model status:

```bash
curl http://localhost:8000/api/model/status
```

Expected response when working:
```json
{
  "ready": true,
  "model_dir": "D:\\project\\Ramy\\models\\runtime\\ramy_h100_finetuned_model",
  "error": "",
  "xai_ready": true,
  "xai_error": ""
}
```

## 🧪 Test Live Prediction

```bash
curl -X POST http://localhost:8000/api/model/predict \
  -H "Content-Type: application/json" \
  -d '{"comments": ["ramy tres bon"], "include_xai": true}'
```

## 📊 Features Enabled with ML

When ML is working, you get:

1. **Live Sentiment Prediction**
   - Real-time classification of Arabic/Darija/French text
   - 5 classes: positive, negative, neutral, improvement, question

2. **XAI (Explainable AI)**
   - Token-level attribution scores
   - Attention rollout visualization
   - Gradient × Attention analysis
   - Word importance highlighting

3. **Batch Processing**
   - Process up to 1000 comments at once
   - Automatic calibration rules
   - Confidence scores for each prediction

4. **Model Information**
   - Model status endpoint
   - Performance metrics
   - Configuration details

## 🐛 Troubleshooting

### Issue: "No module named 'torch'"

**Cause**: The server process doesn't have access to PyTorch.

**Solution**: Run the server directly in your current terminal (not as a background process):
```bash
python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

### Issue: Model loads but XAI doesn't work

**Cause**: XAI requires additional computation.

**Solution**: This is normal. XAI is enabled automatically when you request predictions with `include_xai: true`.

### Issue: Predictions are slow

**Cause**: Running on CPU without GPU acceleration.

**Solution**: This is expected. CPU inference takes 2-5 seconds per batch. For faster predictions, use a GPU-enabled environment.

## 📝 Technical Details

### Python Environment Setup

The project uses Python 3.14 venv with access to Python 3.12 global packages via `.pth` file:

```
.venv/lib/python3.14/site-packages/python312_packages.pth
```

This allows the venv to access PyTorch and other ML libraries installed globally.

### Model Architecture

- Base: AraBERT v2 (`aubmindlab/bert-base-arabertv02`)
- Fine-tuned on: Ramy customer reviews (Darija/Arabic/French)
- Classes: 5 (positive, negative, neutral, improvement, question)
- Max sequence length: 256 tokens

### XAI Methods

1. **Attention Rollout**: Tracks attention flow through all 12 BERT layers
2. **Gradient × Attention**: Class-specific token importance
3. **Combined Attribution**: Weighted average of both methods

## 🌐 Access Points

- Dashboard: http://localhost:8000
- Live Analyzer: http://localhost:8000 (navigate to "Live Analyzer" tab)
- API Docs: http://localhost:8000/docs
- Model Status: http://localhost:8000/api/model/status

## ⚡ Performance Notes

- First prediction: ~10-15 seconds (model loading)
- Subsequent predictions: ~2-5 seconds per batch
- XAI adds ~1-2 seconds per prediction
- Batch processing is more efficient than individual predictions

## 🎓 Using the Live Analyzer

1. Navigate to http://localhost:8000
2. Click on "Live Analyzer" tab
3. Enter Arabic/Darija/French text
4. Enable "Include XAI" for explanations
5. Click "Analyze"
6. View predictions with confidence scores and token attributions

---

**Status**: ✅ ML Features Ready
**Last Updated**: April 16, 2026
