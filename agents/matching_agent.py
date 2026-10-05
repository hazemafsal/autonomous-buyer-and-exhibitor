from langchain_core.prompts import ChatPromptTemplate


def calculate_match(

    llm,

    buyer,

    exhibitor,

    buyer_analysis,

    exhibitor_analysis,

    knowledge
):

    prompt = ChatPromptTemplate.from_messages([

        (
            "system",
            """
You are the Matchmaking Intelligence Agent.

You must determine how suitable an exhibitor is for a buyer.

Evaluate:

- Industry compatibility
- Product compatibility
- Business requirement compatibility
- Budget compatibility
- Geographic compatibility
- Urgency
- Business opportunity

Use the retrieved RAG knowledge.

Return exactly:

SCORE: <0-100>

PRIORITY: HIGH/MEDIUM/LOW

REASON:
<explanation>

Do not give a score higher than 100.

RAG KNOWLEDGE:

{knowledge}
"""
        ),

        (
            "human",
            """
BUYER:

{buyer}

BUYER ANALYSIS:

{buyer_analysis}


EXHIBITOR:

{exhibitor}

EXHIBITOR ANALYSIS:

{exhibitor_analysis}
"""
        )

    ])

    chain = prompt | llm

    response = chain.invoke({

        "knowledge":
        knowledge,

        "buyer":
        str(buyer),

        "buyer_analysis":
        buyer_analysis,

        "exhibitor":
        str(exhibitor),

        "exhibitor_analysis":
        exhibitor_analysis
    })

    return response.content