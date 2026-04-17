import opik
import pandas as pd
from orchestration.graph import build_graph
from utils.config import DATA_PATH

df = pd.read_csv(DATA_PATH)

graph = build_graph()

result = graph.invoke({"data": df})

print(result["result"])

opik.flush_tracker()