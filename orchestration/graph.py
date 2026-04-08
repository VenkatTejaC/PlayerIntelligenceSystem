from langgraph.graph import StateGraph

from agents.segmentation_agent import segmentation_agent
from agents.churn_agent import churn_agent
from agents.recommendation_agent import recommendation_agent

def segmentation_node(state):
    return {"data": segmentation_agent(state["data"])}

def churn_node(state):
    return {"data": churn_agent(state["data"])}

def recommendation_node(state):
    return {"data": recommendation_agent(state["data"])}

def final_node(state):
    return {"result": state["data"]}

def build_graph():
    graph = StateGraph(dict)

    graph.add_node("segmentation", segmentation_node)
    graph.add_node("churn", churn_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("final", final_node)

    graph.set_entry_point("segmentation")

    graph.add_edge("segmentation", "churn")
    graph.add_edge("churn", "recommendation")
    graph.add_edge("recommendation", "final")

    return graph.compile()
