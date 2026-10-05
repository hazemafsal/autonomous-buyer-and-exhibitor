from langchain_core.prompts import ChatPromptTemplate


def analyze_exhibitor(
    llm,
    exhibitor,
    knowledge
):

    prompt = ChatPromptTemplate.from_messages([

        (
            "system",
            """
You are the Exhibitor Intelligence Agent.

Analyze the exhibitor.

Determine:

1. Main products
2. Target buyers
3. Industry relevance
4. Ideal customer
5. Geographic market
6. Business opportunities

Use the exhibition knowledge.

EXHIBITION KNOWLEDGE:

{knowledge}
"""
        ),

        (
            "human",
            """
EXHIBITOR:

Company: {company}

Industry: {industry}

Products: {products}

Target Market: {target_market}

Location: {location}

Price Range: {price_range}
"""
        )

    ])

    chain = prompt | llm

    response = chain.invoke({

        "knowledge": knowledge,

        "company":
        exhibitor["company"],

        "industry":
        exhibitor["industry"],

        "products":
        exhibitor["products"],

        "target_market":
        exhibitor["target_market"],

        "location":
        exhibitor["location"],

        "price_range":
        exhibitor["price_range"]
    })

    return response.content