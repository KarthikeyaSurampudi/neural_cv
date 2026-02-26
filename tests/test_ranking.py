# Ranking tests


from domain.ranking_models import RankedCandidate


def test_ranking_model():

    candidate = RankedCandidate(
        rank=1,
        name="Alice",
        justification="Strong skill match"
    )

    assert candidate.rank == 1
    assert candidate.name == "Alice"