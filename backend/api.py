from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException

from orchestration.graph import build_graph
from utils.data_loader import get_current_data_source, load_players_data

app = FastAPI(title="Player Intelligence API", version="0.1.0")


@lru_cache(maxsize=1)
def load_players() -> pd.DataFrame:
    return load_players_data()


def analyze_players() -> pd.DataFrame:
    df = load_players().copy()
    graph = build_graph()
    result = graph.invoke({"data": df})
    return result["result"]


@app.get("/health")
def health_check() -> dict:
    players_df = load_players()
    data_source = get_current_data_source()
    return {
        "status": "ok",
        "player_count": int(len(players_df)),
        "data_source": data_source["source"],
        "data_location": data_source["location"],
    }


@app.get("/debug/data-source")
def debug_data_source() -> dict:
    load_players()
    return get_current_data_source()


@app.post("/debug/reload-data")
def reload_data_source() -> dict:
    load_players.cache_clear()
    players_df = load_players()
    data_source = get_current_data_source()
    return {
        "status": "reloaded",
        "player_count": int(len(players_df)),
        "data_source": data_source["source"],
        "data_location": data_source["location"],
    }


@app.get("/players")
def list_players() -> dict:
    players_df = load_players()
    player_ids = players_df["player_id"].astype(int).tolist()
    data_source = get_current_data_source()
    return {
        "player_ids": player_ids,
        "player_count": len(player_ids),
        "data_source": data_source["source"],
    }


@app.get("/players/{player_id}")
def get_player_analysis(player_id: int) -> dict:
    result_df = analyze_players()
    player = result_df[result_df["player_id"] == player_id]

    if player.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    player_row = player.iloc[0]
    data_source = get_current_data_source()

    return {
        "data_source": data_source["source"],
        "player": {
            "player_id": int(player_row["player_id"]),
            "sessions_per_week": int(player_row["sessions_per_week"]),
            "avg_session_time": int(player_row["avg_session_time"]),
            "spend": float(player_row["spend"]),
            "days_since_last_login": int(player_row["days_since_last_login"]),
            "churn_score": float(player_row["churn_score"]),
            "segment": int(player_row["segment"]),
            "recommendation": str(player_row["recommendation"]),
        }
    }
