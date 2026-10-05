from pydantic import BaseModel
from typing import Optional


class BuyerRequest(BaseModel):

    buyer_id: str

    minimum_score: int = 60

    top_matches: int = 5


class MatchResult(BaseModel):

    buyer: str

    exhibitor: str

    industry: str

    score: int

    priority: str

    match: str

    recommendation: str


class MatchResponse(BaseModel):

    buyer: str

    matches: list[MatchResult]

    total_matches: int


class RAGRequest(BaseModel):

    query: str


class RAGResponse(BaseModel):

    query: str

    knowledge: str