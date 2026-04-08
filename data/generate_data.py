import pandas as pd
import numpy as np

np.random.seed(42)

N = 10000

df = pd.DataFrame({
    "player_id": range(N),
    "sessions_per_week": np.random.randint(1, 20, N),
    "avg_session_time": np.random.randint(5, 120, N),
    "spend": np.random.exponential(50, N),
    "days_since_last_login": np.random.randint(0, 30, N),
})

df["churn"] = (
    (df["days_since_last_login"] > 15) &
    (df["sessions_per_week"] < 5)
).astype(int)

df.to_csv("data/players.csv", index=False)
print("Data generated")