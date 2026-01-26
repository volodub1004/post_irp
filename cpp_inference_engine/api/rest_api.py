# Note: CoPilot was used to help debug Optional returns from REST API and
# inclusion of built pybind .so

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build" / "cpp"))
import email_predictor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Base paths
ROOT = Path(__file__).resolve().parents[1]  # -> /app
DATA_DIR = ROOT / "cpp" / "data"
MODEL_DIR = ROOT / "cpp" / "model"

# Model paths
CATBOOST_STD_MODEL_PATH = str(MODEL_DIR / "std_catboost_model.cbm")
CATBOOST_COMP_MODEL_PATH = str(MODEL_DIR / "comp_catboost_model.cbm")
STD_TEMPLATES_PATH = str(DATA_DIR / "std_candidate_templates.msgpack")
COMP_TEMPLATES_PATH = str(DATA_DIR / "complex_candidate_templates.msgpack")
FIRM_MAP_PATH = str(DATA_DIR / "firm_template_map.msgpack")

# API KEYS
HUNTER_IO = ""

# Initialize CatBoost Engine
cat_std = email_predictor.CatBoostTemplatePredictor(CATBOOST_STD_MODEL_PATH)
cat_comp = email_predictor.CatBoostTemplatePredictor(CATBOOST_COMP_MODEL_PATH)
cat_engine = email_predictor.CatBoostEmailPredictionEngine(
    cat_std,
    cat_comp,
    STD_TEMPLATES_PATH,
    COMP_TEMPLATES_PATH,
    FIRM_MAP_PATH,
)
cat_engine_verfied = email_predictor.CatBoostEmailPredictionEngine(
    cat_std,
    cat_comp,
    STD_TEMPLATES_PATH,
    COMP_TEMPLATES_PATH,
    FIRM_MAP_PATH,
    hunter_api_key=HUNTER_IO,
)

# FastAPI App
app = FastAPI(
    title="Investor Email Prediction API",
    version="1.0",
    description="Predict investor email addresses using CatBoost models",
)


# Pydantic Models
class PredictionRequest(BaseModel):
    name: str
    firm: str
    domain: Optional[str] = None
    top_k: Optional[int] = 3


class PredictionResponseItem(BaseModel):
    email: str
    score: float
    verification_status: Optional[str] = None
    verification_score: Optional[int] = None


# Routes
@app.get("/")
def root():
    return {"message": "Investor Email Prediction API is running."}


@app.post("/predict/catboost", response_model=List[PredictionResponseItem])
def predict_catboost(req: PredictionRequest):
    try:
        results = cat_engine.predict(
            req.name, req.firm, top_k=req.top_k, domain=req.domain
        )
        return [PredictionResponseItem(email=r.email, score=0) for r in results[:3]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/catboost_verified", response_model=List[PredictionResponseItem])
def predict_catboost_verify(req: PredictionRequest):
    try:
        results = cat_engine_verfied.predict(
            req.name, req.firm, top_k=req.top_k, domain=req.domain
        )

        out: List[PredictionResponseItem] = []
        for r in results[:3]:
            vr = getattr(r, "verification_result", None)  # VerificationResult | None
            out.append(
                PredictionResponseItem(
                    email=r.email,
                    score=vr.score if vr else 0.0,
                )
            )
        out.sort(key=lambda x: x.score, reverse=True)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
