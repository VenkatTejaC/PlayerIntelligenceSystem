import pandas as pd
import pytest

from orchestration.graph import build_graph


@pytest.mark.integration
def test_graph_invoke_returns_result_key(sample_df):
    graph = build_graph()
    result = graph.invoke({"data": sample_df.copy()})
    assert "result" in result


@pytest.mark.integration
def test_graph_result_is_non_empty_dataframe(sample_df):
    graph = build_graph()
    result = graph.invoke({"data": sample_df.copy()})

    assert isinstance(result["result"], pd.DataFrame)
    assert not result["result"].empty


@pytest.mark.integration
def test_graph_result_contains_expected_enrichment_fields(sample_df):
    graph = build_graph()
    result = graph.invoke({"data": sample_df.copy()})
    output = result["result"]

    assert "segment" in output.columns
    assert "churn_score" in output.columns
    assert "recommendation" in output.columns
