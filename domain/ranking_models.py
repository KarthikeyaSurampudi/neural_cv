# Ranking models

# domain/ranking_models.py

from typing import List
from pydantic import BaseModel


class RankedCandidate(BaseModel):
    rank: int
    name: str
    justification: str


class RankingResponse(BaseModel):
    ranking: List[RankedCandidate]