import requests
import streamlit as st


# ==========================================================
# CONFIGURATION
# ==========================================================

API_URL = "http://127.0.0.1:8000"


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="AI Exhibitor-Buyer Matchmaking",
    page_icon="🤖",
    layout="wide"
)


# ==========================================================
# TITLE
# ==========================================================

st.title(
    "🤖 Autonomous Exhibitor-to-Buyer Matchmaking"
)

st.caption(
    "Gemini + RAG + ChromaDB + FastAPI + Streamlit"
)


# ==========================================================
# API GET HELPER
# ==========================================================

def api_get(endpoint):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:

        st.error(
            "❌ Cannot connect to FastAPI. "
            "Make sure the backend is running on port 8000."
        )

        return None

    except requests.exceptions.HTTPError:

        try:

            detail = response.json().get(
                "detail",
                "Unknown API error."
            )

        except Exception:

            detail = response.text

        st.error(
            f"❌ API Error: {detail}"
        )

        return None

    except Exception as e:

        st.error(
            f"❌ Request Error: {e}"
        )

        return None


# ==========================================================
# API POST HELPER
# ==========================================================

def api_post(endpoint, payload):

    try:

        response = requests.post(
            f"{API_URL}{endpoint}",
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:

        st.error(
            "❌ Cannot connect to FastAPI. "
            "Start the backend first."
        )

        return None

    except requests.exceptions.HTTPError as e:

        try:

            detail = response.json().get(
                "detail",
                str(e)
            )

        except Exception:

            detail = response.text

        st.error(
            f"❌ API Error: {detail}"
        )

        return None

    except Exception as e:

        st.error(
            f"❌ Request Error: {e}"
        )

        return None


# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.title(
    "⚙️ System Controls"
)


# ----------------------------------------------------------
# CHECK API
# ----------------------------------------------------------

if st.sidebar.button(
    "🔄 Check API"
):

    health = api_get(
        "/health"
    )

    if health:

        st.sidebar.success(
            "🟢 FastAPI is online"
        )


# ----------------------------------------------------------
# CHROMADB STATUS
# ----------------------------------------------------------

if st.sidebar.button(
    "🗄️ ChromaDB Status"
):

    status = api_get(
        "/api/rag/status"
    )

    if status:

        st.sidebar.success(
            "🟢 ChromaDB connected"
        )

        st.sidebar.write(
            f"Documents: "
            f"{status.get('documents', 0)}"
        )

        st.sidebar.write(
            f"Collection: "
            f"{status.get('collection', 'Unknown')}"
        )


# ==========================================================
# TABS
# ==========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "🔎 RAG Search",
        "👤 Buyer Intelligence",
        "📊 System Status"
    ]
)


# ==========================================================
# TAB 1 — RAG SEARCH
# ==========================================================

with tab1:

    st.header(
        "📚 Exhibition Knowledge Search"
    )

    st.write(
        "Search the exhibition knowledge "
        "stored in ChromaDB using RAG."
    )

    query = st.text_area(

        "Enter your search query",

        placeholder=(
            "Example: "
            "Finance enterprise AI analytics "
            "secure infrastructure Dubai"
        ),

        height=120
    )

    if st.button(
        "🔍 Search Knowledge",
        type="primary",
        key="rag_search_button"
    ):

        if not query.strip():

            st.warning(
                "⚠️ Please enter a search query."
            )

        else:

            with st.spinner(
                "🔎 Searching ChromaDB..."
            ):

                result = api_post(

                    "/api/rag/search",

                    {
                        "query": query.strip()
                    }
                )

            # ------------------------------------------------
            # RESULT CHECK
            # ------------------------------------------------

            if result is None:

                st.error(
                    "❌ RAG request failed."
                )

            else:

                success = result.get(
                    "success",
                    False
                )

                knowledge = result.get(
                    "knowledge"
                )

                # Convert None safely
                if knowledge is None:

                    knowledge = ""

                knowledge = str(
                    knowledge
                ).strip()

                # ------------------------------------------------
                # SUCCESS + KNOWLEDGE
                # ------------------------------------------------

                if success and knowledge:

                    st.success(
                        "✅ Knowledge retrieved successfully."
                    )

                    st.subheader(
                        "📖 Retrieved Knowledge"
                    )

                    st.markdown(
                        knowledge
                    )

                    # --------------------------------------------
                    # DEBUG INFORMATION
                    # --------------------------------------------

                    with st.expander(
                        "🔧 RAG Response Details"
                    ):

                        st.write(
                            "Query:"
                        )

                        st.code(
                            result.get(
                                "query",
                                query
                            )
                        )

                        st.write(
                            "Knowledge characters:"
                        )

                        st.write(
                            len(knowledge)
                        )

                # ------------------------------------------------
                # NO KNOWLEDGE
                # ------------------------------------------------

                elif success and not knowledge:

                    st.warning(
                        "⚠️ ChromaDB returned no "
                        "knowledge for this query."
                    )

                    st.info(
                        "Check the ChromaDB document count "
                        "and rebuild the vector database if "
                        "the knowledge file was recently changed."
                    )

                    with st.expander(
                        "🔧 API Response"
                    ):

                        st.json(
                            result
                        )

                # ------------------------------------------------
                # API FAILURE
                # ------------------------------------------------

                else:

                    st.error(
                        "❌ RAG search failed."
                    )

                    with st.expander(
                        "🔧 API Response"
                    ):

                        st.json(
                            result
                        )


# ==========================================================
# TAB 2 — BUYER INTELLIGENCE
# ==========================================================

with tab2:

    st.header(
        "👤 Buyer Intelligence"
    )

    st.write(
        "Select a buyer and retrieve the "
        "most relevant exhibition knowledge."
    )

    buyers_response = api_get(
        "/api/buyers"
    )

    if buyers_response:

        buyers = buyers_response.get(
            "buyers",
            []
        )

        if not buyers:

            st.warning(
                "⚠️ No buyers found in buyers.csv."
            )

        else:

            buyer_options = {}

            for buyer in buyers:

                buyer_id = buyer.get(
                    "id",
                    ""
                )

                company = buyer.get(
                    "company",
                    "Unknown"
                )

                buyer_options[
                    f"{buyer_id} - {company}"
                ] = buyer

            selected_label = st.selectbox(

                "Select Buyer",

                list(
                    buyer_options.keys()
                )
            )

            selected_buyer = buyer_options[
                selected_label
            ]

            st.subheader(
                "👤 Buyer Profile"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Company:** "
                    f"{selected_buyer.get('company', '')}"
                )

                st.write(
                    f"**Industry:** "
                    f"{selected_buyer.get('industry', '')}"
                )

                st.write(
                    f"**Budget:** "
                    f"{selected_buyer.get('budget', '')}"
                )

            with col2:

                st.write(
                    f"**Location:** "
                    f"{selected_buyer.get('target_location', '')}"
                )

                st.write(
                    f"**Urgency:** "
                    f"{selected_buyer.get('urgency', '')}"
                )

            st.write(
                f"**Requirements:** "
                f"{selected_buyer.get('requirements', '')}"
            )

            st.divider()

            if st.button(
                "🧠 Analyze Buyer",
                type="primary",
                key="analyze_buyer_button"
            ):

                buyer_id = selected_buyer.get(
                    "id"
                )

                with st.spinner(
                    "🧠 Running buyer intelligence..."
                ):

                    result = api_post(

                        "/api/analyze",

                        {
                            "buyer_id": buyer_id
                        }
                    )

                if result:

                    knowledge = result.get(
                        "knowledge"
                    )

                    if knowledge is None:

                        knowledge = ""

                    knowledge = str(
                        knowledge
                    ).strip()

                    if knowledge:

                        st.success(
                            "✅ Buyer analysis completed."
                        )

                        st.subheader(
                            "📚 Relevant Exhibition Knowledge"
                        )

                        st.markdown(
                            knowledge
                        )

                    else:

                        st.warning(
                            "Buyer analysis completed, "
                            "but no relevant knowledge was found."
                        )

                        with st.expander(
                            "API Response"
                        ):

                            st.json(
                                result
                            )


# ==========================================================
# TAB 3 — SYSTEM STATUS
# ==========================================================

with tab3:

    st.header(
        "📊 System Status"
    )

    col1, col2, col3 = st.columns(3)

    # ------------------------------------------------------
    # FASTAPI
    # ------------------------------------------------------

    with col1:

        health = api_get(
            "/health"
        )

        if health:

            st.success(
                "🟢 FastAPI Online"
            )

            st.json(
                health
            )

        else:

            st.error(
                "🔴 FastAPI Offline"
            )

    # ------------------------------------------------------
    # CHROMADB
    # ------------------------------------------------------

    with col2:

        status = api_get(
            "/api/rag/status"
        )

        if status:

            st.success(
                "🟢 ChromaDB Online"
            )

            st.metric(

                "Documents",

                status.get(
                    "documents",
                    0
                )
            )

            st.write(
                "Collection:"
            )

            st.code(
                status.get(
                    "collection",
                    "Unknown"
                )
            )

        else:

            st.error(
                "🔴 ChromaDB Error"
            )

    # ------------------------------------------------------
    # BUYERS
    # ------------------------------------------------------

    with col3:

        buyers_response = api_get(
            "/api/buyers"
        )

        if buyers_response:

            count = buyers_response.get(
                "count",
                0
            )

            st.success(
                "🟢 Buyer Database"
            )

            st.metric(
                "Buyers",
                count
            )

        else:

            st.error(
                "🔴 Buyer Database Error"
            )

    # ------------------------------------------------------
    # EXHIBITORS
    # ------------------------------------------------------

    st.divider()

    st.subheader(
        "🏢 Exhibitor Database"
    )

    exhibitors_response = api_get(
        "/api/exhibitors"
    )

    if exhibitors_response:

        exhibitor_count = exhibitors_response.get(
            "count",
            0
        )

        st.success(
            "🟢 Exhibitor Database Online"
        )

        st.metric(
            "Exhibitors",
            exhibitor_count
        )

    else:

        st.error(
            "🔴 Exhibitor Database Error"
        )


# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.caption(
    "Autonomous Exhibitor-to-Buyer Matchmaking "
    "| Gemini | RAG | ChromaDB | FastAPI"
)