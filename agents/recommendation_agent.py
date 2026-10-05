from langchain_core.prompts import ChatPromptTemplate


def generate_recommendation(
    llm,
    buyer,
    exhibitor,
    match_result,
    knowledge
):
    """
    Generate a practical business recommendation
    for a buyer-exhibitor meeting.
    """

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are the Final Business Recommendation Agent
for an autonomous exhibition matchmaking system.

Your task is to create an actionable recommendation
for a buyer and exhibitor meeting.

Include:

1. Why the buyer and exhibitor should meet
2. What the exhibitor should pitch
3. What the buyer should ask
4. Suggested meeting objective
5. Potential business opportunity

Use the supplied RAG knowledge.

Do not invent unsupported facts.

RAG KNOWLEDGE:

{knowledge}
"""
        ),
        (
            "human",
            """
BUYER:

{buyer}


EXHIBITOR:

{exhibitor}


MATCH RESULT:

{match_result}
"""
        )
    ])

    chain = prompt | llm

    response = chain.invoke({
        "knowledge": knowledge,
        "buyer": str(buyer),
        "exhibitor": str(exhibitor),
        "match_result": match_result
    })

    return response.content