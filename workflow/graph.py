from typing import TypedDict, Any

from langgraph.graph import (
    StateGraph,
    END
)

from agents.buyer_agent import (
    analyze_buyer
)

from agents.exhibitor_agent import (
    analyze_exhibitor
)

from agents.matching_agent import (
    calculate_match
)

from agents.recommendation_agent import (
    generate_recommendation
)


class MatchState(TypedDict, total=False):

    llm: Any

    buyer: dict

    exhibitor: dict

    knowledge: str

    buyer_analysis: str

    exhibitor_analysis: str

    match_result: str

    score: int

    priority: str

    recommendation: str


# ==========================================================
# BUYER NODE
# ==========================================================

def buyer_node(state):

    result = analyze_buyer(

        state["llm"],

        state["buyer"],

        state["knowledge"]
    )

    return {

        "buyer_analysis":
        result
    }


# ==========================================================
# EXHIBITOR NODE
# ==========================================================

def exhibitor_node(state):

    result = analyze_exhibitor(

        state["llm"],

        state["exhibitor"],

        state["knowledge"]
    )

    return {

        "exhibitor_analysis":
        result
    }


# ==========================================================
# MATCHING NODE
# ==========================================================

def matching_node(state):

    result = calculate_match(

        state["llm"],

        state["buyer"],

        state["exhibitor"],

        state["buyer_analysis"],

        state["exhibitor_analysis"],

        state["knowledge"]
    )


    score = 0

    priority = "LOW"


    for line in result.splitlines():

        line = line.strip()

        if line.upper().startswith(
            "SCORE:"
        ):

            try:

                score = int(
                    line.split(
                        ":",
                        1
                    )[1].strip()
                )

            except:

                score = 0


        elif line.upper().startswith(
            "PRIORITY:"
        ):

            priority = (

                line.split(
                    ":",
                    1
                )[1]
                .strip()
                .upper()
            )


    score = max(
        0,
        min(
            100,
            score
        )
    )


    return {

        "match_result":
        result,

        "score":
        score,

        "priority":
        priority
    }


# ==========================================================
# RECOMMENDATION NODE
# ==========================================================

def recommendation_node(state):

    result = generate_recommendation(

        state["llm"],

        state["buyer"],

        state["exhibitor"],

        state["match_result"],

        state["knowledge"]
    )

    return {

        "recommendation":
        result
    }


# ==========================================================
# BUILD GRAPH
# ==========================================================

def build_graph():

    workflow = StateGraph(
        MatchState
    )


    workflow.add_node(
        "buyer_analysis",
        buyer_node
    )

    workflow.add_node(
        "exhibitor_analysis",
        exhibitor_node
    )

    workflow.add_node(
        "matching",
        matching_node
    )

    workflow.add_node(
        "recommendation",
        recommendation_node
    )


    workflow.set_entry_point(
        "buyer_analysis"
    )


    workflow.add_edge(

        "buyer_analysis",

        "exhibitor_analysis"
    )


    workflow.add_edge(

        "exhibitor_analysis",

        "matching"
    )


    workflow.add_edge(

        "matching",

        "recommendation"
    )


    workflow.add_edge(

        "recommendation",

        END
    )


    return workflow.compile()