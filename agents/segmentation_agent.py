from sklearn.cluster import KMeans

def segmentation_agent(df):
    features = df[["sessions_per_week", "avg_session_time", "spend"]]
    model = KMeans(n_clusters=3, random_state=42)
    df["segment"] = model.fit_predict(features)
    return df