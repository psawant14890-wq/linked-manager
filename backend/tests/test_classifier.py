from app.models.message import MessageCategory
from app.services.classifier import compute_priority_score


def test_recruiter_always_outranks_general():
    recruiter_score = compute_priority_score(MessageCategory.RECRUITER, relevance_score=0.0)
    general_score = compute_priority_score(MessageCategory.GENERAL, relevance_score=1.0)
    assert recruiter_score > general_score


def test_spam_always_ranks_lowest_regardless_of_relevance():
    spam_score = compute_priority_score(MessageCategory.SPAM, relevance_score=1.0)
    general_score = compute_priority_score(MessageCategory.GENERAL, relevance_score=0.0)
    assert spam_score < general_score


def test_relevance_score_nudges_within_category():
    low = compute_priority_score(MessageCategory.COLLABORATION, relevance_score=0.0)
    high = compute_priority_score(MessageCategory.COLLABORATION, relevance_score=1.0)
    assert high > low
