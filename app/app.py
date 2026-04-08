import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 30


def fetch_health() -> dict:
    response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def fetch_player_ids() -> dict:
    response = requests.get(f"{API_BASE_URL}/players", timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def fetch_player_analysis(player_id: int) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/players/{player_id}",
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return payload


st.set_page_config(page_title="Player Intelligence", layout="wide")

st.title("Player Intelligence System")

try:
    health = fetch_health()
    players_payload = fetch_player_ids()
    player_ids = players_payload["player_ids"]
except requests.RequestException as exc:
    st.error(
        "Could not connect to the FastAPI backend. Start it with "
        "`uvicorn backend.api:app --reload` and refresh the page."
    )
    st.exception(exc)
    st.stop()

st.caption(
    f"Backend API: {API_BASE_URL} | Data source: {health['data_source']} | Location: {health['data_location']}"
)

player_id = st.selectbox("Select Player ID", options=player_ids, index=0)

if st.button("Analyze Player"):
    try:
        with st.spinner("Requesting analysis from backend..."):
            payload = fetch_player_analysis(int(player_id))
            player = payload["player"]
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            st.error("Player not found.")
        else:
            st.error("Backend returned an error while analyzing the player.")
        st.exception(exc)
    except requests.RequestException as exc:
        st.error("Could not reach the backend while analyzing the player.")
        st.exception(exc)
    else:
        st.subheader(f"Player {player_id} Analysis")
        st.info(f"Data source used for this request: {payload['data_source']}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Sessions/Week", player["sessions_per_week"])

        with col2:
            st.metric("Churn Risk", round(player["churn_score"], 2))

        with col3:
            st.metric("Segment", player["segment"])

        st.subheader("Recommendation")
        st.success(player["recommendation"])

        st.subheader("Raw Data")
        st.json(player)
