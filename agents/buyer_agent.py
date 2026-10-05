from langchain_core.prompts import ChatPromptTemplate


def analyze_buyer(
    llm,
    buyer,
    knowledge
):

    prompt = ChatPromptTemplate.from_messages([

        (
            "system",
            """
You are the Buyer Intelligence Agent.

Analyze the buyer and determine:

1. Business requirements
2. Required products
3. Industry needs
4. Budget importance
5. Location preference
6. Urgency
7. Ideal exhibitor profile

Use the supplied exhibition knowledge.

Do not invent information.

EXHIBITION KNOWLEDGE:

{knowledge}
"""
        ),

        (
            "human",
            """
BUYER:

Company: {company}

Industry: {industry}

Requirements: {requirements}

Budget: {budget}

Location: {location}

Urgency: {urgency}
"""
        )

    ])

    chain = prompt | llm

    response = chain.invoke({

        "knowledge": knowledge,

        "company": buyer["company"],

        "industry": buyer["industry"],

        "requirements":
        buyer["requirements"],

        "budget":
        buyer["budget"],

        "location":
        buyer["target_location"],

        "urgency":
        buyer["urgency"]
    })

    return response.content