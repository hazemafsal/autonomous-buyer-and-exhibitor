import os
import gc

import pandas as pd

from dotenv import load_dotenv

from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

from workflow.graph import build_graph

from rag.vectorstore import (
    get_vectorstore,
    retrieve_knowledge
)


load_dotenv()


# ==========================================================
# CONFIGURATION
# ==========================================================

EXHIBITOR_FILE = "data/exhibitors.csv"

BUYER_FILE = "data/buyers.csv"


# ==========================================================
# LOAD DATA
# ==========================================================

_exhibitors = None
_buyers = None


def load_data():

    global _exhibitors
    global _buyers

    if _exhibitors is None:

        _exhibitors = pd.read_csv(
            EXHIBITOR_FILE
        )

    if _buyers is None:

        _buyers = pd.read_csv(
            BUYER_FILE
        )

    return _exhibitors, _buyers


# ==========================================================
# GEMINI
# ==========================================================

_llm = None


def get_llm():

    global _llm

    if _llm is None:

        api_key = os.getenv(
            "GOOGLE_API_KEY"
        )

        if not api_key:

            raise ValueError(
                "GOOGLE_API_KEY is missing."
            )

        _llm = ChatGoogleGenerativeAI(

            model="gemini-2.5-flash",

            google_api_key=api_key,

            temperature=0.2,

            max_output_tokens=1000
        )

    return _llm


# ==========================================================
# CHROMADB
# ==========================================================

_vectorstore = None


def initialize_rag():

    global _vectorstore

    if _vectorstore is None:

        _vectorstore = get_vectorstore()

    return _vectorstore


# ==========================================================
# LANGGRAPH
# ==========================================================

_graph = None


def get_graph():

    global _graph

    if _graph is None:

        _graph = build_graph()

    return _graph


# ==========================================================
# STARTUP
# ==========================================================

def initialize_services():

    load_data()

    get_llm()

    initialize_rag()

    get_graph()


# ==========================================================
# GET BUYERS
# ==========================================================

def get_buyers():

    _, buyers = load_data()

    return buyers.to_dict(
        orient="records"
    )


# ==========================================================
# GET EXHIBITORS
# ==========================================================

def get_exhibitors():

    exhibitors, _ = load_data()

    return exhibitors.to_dict(
        orient="records"
    )


# ==========================================================
# RAG SEARCH
# ==========================================================

def search_rag(query):

    initialize_rag()

    return retrieve_knowledge(
        query
    )


# ==========================================================
# MATCH BUYER
# ==========================================================

def match_buyer(

    buyer_id,

    minimum_score=60,

    top_matches=5

):

    exhibitors, buyers = load_data()

    llm = get_llm()

    graph = get_graph()


    # ------------------------------------------------------
    # FIND BUYER
    # ------------------------------------------------------

    buyer_rows = buyers[
        buyers["id"] == buyer_id
    ]


    if buyer_rows.empty:

        raise ValueError(
            f"Buyer {buyer_id} not found."
        )


    buyer = buyer_rows.iloc[
        0
    ].to_dict()


    # ------------------------------------------------------
    # RAG QUERY
    # ------------------------------------------------------

    rag_query = f"""

    Buyer:
    {buyer["company"]}

    Industry:
    {buyer["industry"]}

    Requirements:
    {buyer["requirements"]}

    Budget:
    {buyer["budget"]}

    Location:
    {buyer["target_location"]}

    """


    knowledge = search_rag(
        rag_query
    )


    results = []


    # ------------------------------------------------------
    # PROCESS EXHIBITORS
    # ------------------------------------------------------

    for _, row in exhibitors.iterrows():

        exhibitor = row.to_dict()


        try:

            state = {

                "llm":
                llm,

                "buyer":
                buyer,

                "exhibitor":
                exhibitor,

                "knowledge":
                knowledge
            }


            result = graph.invoke(
                state
            )


            score = int(
                result.get(
                    "score",
                    0
                )
            )


            if score >= minimum_score:

                results.append({

                    "buyer":
                    buyer["company"],

                    "exhibitor":
                    exhibitor["company"],

                    "industry":
                    exhibitor["industry"],

                    "score":
                    score,

                    "priority":
                    result.get(
                        "priority",
                        "LOW"
                    ),

                    "match":
                    result.get(
                        "match_result",
                        ""
                    ),

                    "recommendation":
                    result.get(
                        "recommendation",
                        ""
                    )
                })


        except Exception as e:

            print(
                f"Error processing "
                f"{exhibitor['company']}: {e}"
            )


    # ------------------------------------------------------
    # SORT
    # ------------------------------------------------------

    results.sort(

        key=lambda x:
        x["score"],

        reverse=True
    )


    results = results[
        :top_matches
    ]


    gc.collect()


    return {

        "buyer":
        buyer["company"],

        "matches":
        results,

        "total_matches":
        len(results)
    }