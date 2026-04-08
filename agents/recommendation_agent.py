def recommendation_agent(df):
    def recommend(row):
        if row["churn_score"] > 0.7:
            return "Offer discount"
        elif row["segment"] == 0:
            return "Promote premium items"
        else:
            return "Engage with new content"

    df["recommendation"] = df.apply(recommend, axis=1)
    return df