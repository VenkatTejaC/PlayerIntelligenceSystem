import pytest

from agents.churn_agent import churn_agent
from agents.recommendation_agent import recommendation_agent
from agents.segmentation_agent import segmentation_agent


@pytest.mark.unit
def test_segmentation_agent_adds_segment_column(sample_df):
    result = segmentation_agent(sample_df.copy())
    assert "segment" in result.columns
    assert not result["segment"].isnull().any()


@pytest.mark.unit
def test_churn_agent_adds_churn_score_column(sample_df):
    result = churn_agent(sample_df.copy())
    assert "churn_score" in result.columns
    assert not result["churn_score"].isnull().any()


@pytest.mark.unit
def test_recommendation_agent_adds_recommendation_column(sample_df):
    enriched = segmentation_agent(sample_df.copy())
    enriched = churn_agent(enriched)
    result = recommendation_agent(enriched)

    assert "recommendation" in result.columns
    assert not result["recommendation"].isnull().any()
    assert (result["recommendation"].str.len() > 0).all()


@pytest.mark.unit
def test_agent_chain_produces_all_expected_fields(sample_df):
    result = segmentation_agent(sample_df.copy())
    result = churn_agent(result)
    result = recommendation_agent(result)

    assert "segment" in result.columns
    assert "churn_score" in result.columns
    assert "recommendation" in result.columns
