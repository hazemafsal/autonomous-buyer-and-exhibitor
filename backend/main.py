from contextlib import asynccontextmanager
from pathlib import Path
import csv
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag.vectorstore import (
    get_vectorstore,
    retrieve_knowledge
)


# ==========================================================
# PROJECT PATH
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

BUYERS_FILE = DATA_DIR / "buyers.csv"

EXHIBITORS_FILE = DATA_DIR / "exhibitors.csv"


# ==========================================================
# REQUEST MODELS
# ==========================================================

class RAGSearchRequest(BaseModel):

    query: str


class BuyerAnalysisRequest(BaseModel):

    buyer_id: str


class MatchRequest(BaseModel):

    buyer_id: str

    minimum_score: float = 60

    top_matches: int = 5


# ==========================================================
# CSV HELPER
# ==========================================================

def load_csv(file_path: Path):

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    records = []

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            cleaned = {}

            for key, value in row.items():

                if key is None:
                    continue

                clean_key = key.strip()

                clean_value = (
                    value.strip()
                    if value
                    else ""
                )

                cleaned[clean_key] = clean_value

            records.append(cleaned)

    return records


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================================
# BUYER MATCHING
# ==========================================================

def calculate_match_score(
    buyer,
    exhibitor
):

    score = 0

    buyer_industry = normalize_text(
        buyer.get("industry", "")
    )

    exhibitor_industry = normalize_text(
        exhibitor.get("industry", "")
    )

    buyer_requirements = normalize_text(
        buyer.get("requirements", "")
    )

    exhibitor_products = normalize_text(
        exhibitor.get("products", "")
    )

    buyer_location = normalize_text(
        buyer.get("target_location", "")
    )

    exhibitor_location = normalize_text(
        exhibitor.get("target_location", "")
    )

    buyer_urgency = normalize_text(
        buyer.get("urgency", "")
    )

    exhibitor_urgency = normalize_text(
        exhibitor.get("urgency", "")
    )

    # ------------------------------------------------------
    # INDUSTRY MATCH
    # ------------------------------------------------------

    buyer_industries = set(
        buyer_industry.split()
    )

    exhibitor_industries = set(
        exhibitor_industry.split()
    )

    industry_overlap = (
        buyer_industries
        & exhibitor_industries
    )

    if industry_overlap:

        score += 30

    # ------------------------------------------------------
    # REQUIREMENT / PRODUCT MATCH
    # ------------------------------------------------------

    requirement_words = set(
        buyer_requirements.split()
    )

    product_words = set(
        exhibitor_products.split()
    )

    common_words = (
        requirement_words
        & product_words
    )

    if requirement_words:

        product_match_ratio = (
            len(common_words)
            / len(requirement_words)
        )

        score += min(
            35,
            product_match_ratio * 35
        )

    # ------------------------------------------------------
    # LOCATION MATCH
    # ------------------------------------------------------

    if (
        buyer_location
        and exhibitor_location
    ):

        if (
            buyer_location
            in exhibitor_location
            or
            exhibitor_location
            in buyer_location
        ):

            score += 20

    # ------------------------------------------------------
    # URGENCY MATCH
    # ------------------------------------------------------

    if (
        buyer_urgency
        and exhibitor_urgency
        and buyer_urgency == exhibitor_urgency
    ):

        score += 15

    return round(
        min(score, 100),
        2
    )


# ==========================================================
# MATCH PRIORITY
# ==========================================================

def get_priority(score):

    if score >= 85:

        return "Very High"

    if score >= 75:

        return "High"

    if score >= 60:

        return "Medium"

    return "Low"


# ==========================================================
# RECOMMENDATION
# ==========================================================

def generate_recommendation(
    buyer,
    exhibitor,
    score
):

    buyer_company = buyer.get(
        "company",
        "Buyer"
    )

    exhibitor_company = exhibitor.get(
        "company",
        "Exhibitor"
    )

    products = exhibitor.get(
        "products",
        ""
    )

    location = exhibitor.get(
        "target_location",
        ""
    )

    urgency = buyer.get(
        "urgency",
        "Medium"
    )

    if score >= 85:

        recommendation = (
            f"{exhibitor_company} is an excellent "
            f"match for {buyer_company}. "
            f"The exhibitor provides {products}. "
            f"The location is {location}. "
            f"This should be treated as a "
            f"high-priority business meeting."
        )

    elif score >= 75:

        recommendation = (
            f"{exhibitor_company} is a strong "
            f"potential match for {buyer_company}. "
            f"The exhibitor's offerings include "
            f"{products}. "
            f"Consider scheduling a meeting."
        )

    elif score >= 60:

        recommendation = (
            f"{exhibitor_company} has a reasonable "
            f"match with {buyer_company}. "
            f"Further qualification is recommended "
            f"before arranging a meeting."
        )

    else:

        recommendation = (
            f"{exhibitor_company} has limited "
            f"alignment with {buyer_company}. "
            f"Consider other exhibitors first."
        )

    if urgency.lower() == "high":

        recommendation += (
            " The buyer has high urgency, "
            "so prioritize this opportunity."
        )

    return recommendation


# ==========================================================
# STARTUP
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print()
    print("=" * 70)
    print(
        "AUTONOMOUS EXHIBITOR-BUYER "
        "MATCHMAKING API"
    )
    print("=" * 70)

    print()
    print("Project root:")
    print(PROJECT_ROOT)

    print()
    print("Buyers file:")
    print(BUYERS_FILE)

    print()
    print("Exhibitors file:")
    print(EXHIBITORS_FILE)

    # ------------------------------------------------------
    # ChromaDB
    # ------------------------------------------------------

    try:

        print()
        print("Initializing ChromaDB...")

        get_vectorstore()

        print(
            "ChromaDB initialized successfully."
        )

    except Exception as e:

        print()
        print(
            "ChromaDB initialization error:"
        )

        print(str(e))

    # ------------------------------------------------------
    # Data validation
    # ------------------------------------------------------

    print()

    if BUYERS_FILE.exists():

        print(
            "✓ buyers.csv found"
        )

    else:

        print(
            "✗ buyers.csv NOT found"
        )

    if EXHIBITORS_FILE.exists():

        print(
            "✓ exhibitors.csv found"
        )

    else:

        print(
            "✗ exhibitors.csv NOT found"
        )

    print()
    print("=" * 70)
    print()

    yield

    print(
        "FastAPI shutting down."
    )


# ==========================================================
# FASTAPI
# ==========================================================

app = FastAPI(

    title=(
        "Autonomous "
        "Exhibitor-Buyer Matchmaking"
    ),

    description=(
        "AI-powered exhibitor and buyer "
        "matchmaking using Gemini, RAG, "
        "ChromaDB, LangGraph and FastAPI."
    ),

    version="1.0.0",

    lifespan=lifespan
)


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ==========================================================
# ROOT
# ==========================================================

@app.get("/")
def root():

    return {

        "status": "online",

        "application": (
            "Autonomous "
            "Exhibitor-Buyer Matchmaking"
        ),

        "services": [

            "FastAPI",

            "Gemini",

            "RAG",

            "ChromaDB",

            "Matchmaking",

            "Streamlit"
        ]
    }


# ==========================================================
# HEALTH
# ==========================================================

@app.get("/health")
def health():

    return {

        "status": "healthy"
    }


# ==========================================================
# BUYERS
# ==========================================================

@app.get("/api/buyers")
def get_buyers():

    try:

        buyers = load_csv(
            BUYERS_FILE
        )

        return {

            "success": True,

            "count": len(buyers),

            "buyers": buyers
        }

    except FileNotFoundError as e:

        raise HTTPException(

            status_code=404,

            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# ==========================================================
# SINGLE BUYER
# ==========================================================

@app.get("/api/buyers/{buyer_id}")
def get_buyer(
    buyer_id: str
):

    try:

        buyers = load_csv(
            BUYERS_FILE
        )

        for buyer in buyers:

            if (
                buyer.get("id", "")
                == buyer_id
            ):

                return {

                    "success": True,

                    "buyer": buyer
                }

        raise HTTPException(

            status_code=404,

            detail=(
                f"Buyer "
                f"{buyer_id} "
                f"not found."
            )
        )

    except HTTPException:

        raise

    except FileNotFoundError as e:

        raise HTTPException(

            status_code=404,

            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# ==========================================================
# EXHIBITORS
# ==========================================================

@app.get("/api/exhibitors")
def get_exhibitors():

    try:

        exhibitors = load_csv(
            EXHIBITORS_FILE
        )

        return {

            "success": True,

            "count": len(exhibitors),

            "exhibitors": exhibitors
        }

    except FileNotFoundError as e:

        raise HTTPException(

            status_code=404,

            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# ==========================================================
# SINGLE EXHIBITOR
# ==========================================================

@app.get("/api/exhibitors/{exhibitor_id}")
def get_exhibitor(
    exhibitor_id: str
):

    try:

        exhibitors = load_csv(
            EXHIBITORS_FILE
        )

        for exhibitor in exhibitors:

            if (
                exhibitor.get("id", "")
                == exhibitor_id
            ):

                return {

                    "success": True,

                    "exhibitor": exhibitor
                }

        raise HTTPException(

            status_code=404,

            detail=(
                f"Exhibitor "
                f"{exhibitor_id} "
                f"not found."
            )
        )

    except HTTPException:

        raise

    except FileNotFoundError as e:

        raise HTTPException(

            status_code=404,

            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# ==========================================================
# MATCHMAKING
# ==========================================================

@app.post("/api/match")
def find_matches(
    request: MatchRequest
):

    try:

        buyers = load_csv(
            BUYERS_FILE
        )

        exhibitors = load_csv(
            EXHIBITORS_FILE
        )

    except FileNotFoundError as e:

        raise HTTPException(

            status_code=404,

            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )

    # ------------------------------------------------------
    # Find buyer
    # ------------------------------------------------------

    buyer = None

    for item in buyers:

        if (
            item.get("id", "")
            == request.buyer_id
        ):

            buyer = item

            break

    if buyer is None:

        raise HTTPException(

            status_code=404,

            detail=(
                f"Buyer "
                f"{request.buyer_id} "
                f"not found."
            )
        )

    # ------------------------------------------------------
    # Calculate matches
    # ------------------------------------------------------

    matches = []

    for exhibitor in exhibitors:

        score = calculate_match_score(
            buyer,
            exhibitor
        )

        if score < request.minimum_score:

            continue

        priority = get_priority(
            score
        )

        recommendation = (
            generate_recommendation(
                buyer,
                exhibitor,
                score
            )
        )

        match_text = (
            f"{buyer.get('company', '')} "
            f"matches "
            f"{exhibitor.get('company', '')} "
            f"with a score of "
            f"{score}/100."
        )

        matches.append({

            "exhibitor_id":
                exhibitor.get("id", ""),

            "exhibitor":
                exhibitor.get(
                    "company",
                    ""
                ),

            "company":
                exhibitor.get(
                    "company",
                    ""
                ),

            "industry":
                exhibitor.get(
                    "industry",
                    ""
                ),

            "products":
                exhibitor.get(
                    "products",
                    ""
                ),

            "target_location":
                exhibitor.get(
                    "target_location",
                    ""
                ),

            "score":
                score,

            "priority":
                priority,

            "match":
                match_text,

            "recommendation":
                recommendation
        })

    # ------------------------------------------------------
    # Sort
    # ------------------------------------------------------

    matches.sort(

        key=lambda x: x["score"],

        reverse=True
    )

    matches = matches[
        :request.top_matches
    ]

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {

        "success": True,

        "buyer": buyer,

        "buyer_id":
            request.buyer_id,

        "total_matches":
            len(matches),

        "minimum_score":
            request.minimum_score,

        "matches":
            matches
    }


# ==========================================================
# RAG SEARCH
# ==========================================================

@app.post("/api/rag/search")
def rag_search(
    request: RAGSearchRequest
):

    query = request.query.strip()

    if not query:

        raise HTTPException(

            status_code=400,

            detail=(
                "Query cannot be empty."
            )
        )

    try:

        print()
        print("=" * 70)
        print("RAG SEARCH")
        print("=" * 70)

        print(
            "Query:",
            query
        )

        knowledge = retrieve_knowledge(
            query
        )

        print(
            "RAG search completed."
        )

        print("=" * 70)
        print()

        return {

            "success": True,

            "query": query,

            "knowledge": knowledge
        }

    except Exception as e:

        print()
        print("RAG ERROR:")
        print(str(e))
        print()

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# ==========================================================
# CHROMADB STATUS
# ==========================================================

@app.get("/api/rag/status")
def rag_status():

    try:

        vectorstore = get_vectorstore()

        count = (
            vectorstore
            ._collection
            .count()
        )

        return {

            "success": True,

            "database": "ChromaDB",

            "collection": (
                vectorstore
                ._collection
                .name
            ),

            "documents": count
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# ==========================================================
# BUYER ANALYSIS
# ==========================================================

@app.post("/api/analyze")
def analyze_buyer(
    request: BuyerAnalysisRequest
):

    try:

        buyers = load_csv(
            BUYERS_FILE
        )

        buyer = None

        for row in buyers:

            if (
                row.get("id", "")
                == request.buyer_id
            ):

                buyer = row

                break

        if buyer is None:

            raise HTTPException(

                status_code=404,

                detail=(
                    f"Buyer "
                    f"{request.buyer_id} "
                    f"not found."
                )
            )

        query = (

            f"{buyer.get('industry', '')} "

            f"{buyer.get('requirements', '')} "

            f"{buyer.get('target_location', '')} "

            f"{buyer.get('urgency', '')}"

        )

        knowledge = retrieve_knowledge(
            query
        )

        return {

            "success": True,

            "buyer": buyer,

            "query": query,

            "knowledge": knowledge
        }

    except HTTPException:

        raise

    except FileNotFoundError as e:

        raise HTTPException(

            status_code=404,

            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# ==========================================================
# DIRECT EXECUTION
# ==========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "backend.main:app",

        host="127.0.0.1",

        port=8000,

        reload=True
    )