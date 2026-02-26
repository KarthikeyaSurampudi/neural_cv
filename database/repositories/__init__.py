# database/repositories/__init__.py

from .user_repo import (
    create_user,
    get_user_by_username,
    get_user_by_id,
    list_users,
    delete_user,
    update_password,
)

from .analysis_repo import (
    create_analysis,
    get_analyses_by_user,
    delete_analysis,
)

from .candidate_repo import (
    add_candidate,
    get_candidates_by_analysis,
)

from .score_repo import (
    update_candidate_scores,
    update_candidate_rank,
)

__all__ = [
    # User
    "create_user",
    "get_user_by_username",
    "get_user_by_id",
    "list_users",
    "delete_user",
    "update_password",
    # Analysis
    "create_analysis",
    "get_analyses_by_user",
    "delete_analysis",
    # Candidate
    "add_candidate",
    "get_candidates_by_analysis",
    # Scores
    "update_candidate_scores",
    "update_candidate_rank",
]