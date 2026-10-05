import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

from langchain_chroma import Chroma

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)

from langchain_core.documents import Document

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)


# ==========================================================
# ENVIRONMENT
# ==========================================================

load_dotenv()


# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


CHROMA_DIR = os.getenv(
    "CHROMA_DIR",
    str(PROJECT_ROOT / "chroma_db")
)


KNOWLEDGE_FILE = os.getenv(
    "KNOWLEDGE_FILE",
    str(
        PROJECT_ROOT
        / "data"
        / "knowledge"
        / "exhibition_knowledge.txt"
    )
)


COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "exhibitor_buyer_knowledge"
)


# ==========================================================
# EMBEDDINGS
# ==========================================================

def get_embeddings():

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:

        raise ValueError(
            "GOOGLE_API_KEY is missing."
        )

    return GoogleGenerativeAIEmbeddings(

        model="gemini-embedding-001",

        google_api_key=api_key
    )


# ==========================================================
# LOAD KNOWLEDGE
# ==========================================================

def load_knowledge():

    file_path = Path(KNOWLEDGE_FILE)

    print()
    print("=" * 60)
    print("RAG KNOWLEDGE FILE")
    print("=" * 60)

    print("Path:")
    print(file_path)

    print("Exists:")
    print(file_path.exists())

    if not file_path.exists():

        raise FileNotFoundError(
            f"Knowledge file not found:\n{file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        text = file.read()

    print("Characters loaded:")
    print(len(text))

    print("=" * 60)
    print()

    return text


# ==========================================================
# CREATE DOCUMENTS
# ==========================================================

def create_documents():

    text = load_knowledge()

    document = Document(

        page_content=text,

        metadata={
            "source": str(KNOWLEDGE_FILE)
        }
    )

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=800,

        chunk_overlap=100
    )

    documents = splitter.split_documents(
        [document]
    )

    print(
        f"Created {len(documents)} knowledge chunks."
    )

    return documents


# ==========================================================
# CREATE VECTOR DATABASE
# ==========================================================

def get_vectorstore():

    embeddings = get_embeddings()

    print()
    print("=" * 60)
    print("CHROMADB")
    print("=" * 60)

    print("Database:")
    print(CHROMA_DIR)

    print("Collection:")
    print(COLLECTION_NAME)

    vectorstore = Chroma(

        collection_name=COLLECTION_NAME,

        embedding_function=embeddings,

        persist_directory=CHROMA_DIR
    )

    try:

        count = vectorstore._collection.count()

    except Exception:

        count = 0

    print("Existing documents:")
    print(count)

    # ------------------------------------------------------
    # INITIALIZE DATABASE
    # ------------------------------------------------------

    if count == 0:

        print()
        print("ChromaDB is empty.")
        print("Loading exhibition knowledge...")

        documents = create_documents()

        vectorstore.add_documents(
            documents
        )

        print(
            f"Added {len(documents)} documents to ChromaDB."
        )

    else:

        print(
            "Existing ChromaDB found."
        )

        print(
            "Using existing knowledge."
        )

    print("=" * 60)
    print()

    return vectorstore


# ==========================================================
# FORCE REBUILD
# ==========================================================

def rebuild_vectorstore():

    print()
    print("=" * 60)
    print("REBUILDING CHROMADB")
    print("=" * 60)

    print(
        "Deleting old ChromaDB..."
    )

    chroma_path = Path(CHROMA_DIR)

    if chroma_path.exists():

        shutil.rmtree(
            chroma_path
        )

        print(
            "Old ChromaDB deleted."
        )

    else:

        print(
            "No existing ChromaDB found."
        )

    print(
        "Creating new ChromaDB..."
    )

    vectorstore = get_vectorstore()

    print(
        "ChromaDB rebuild completed."
    )

    print("=" * 60)
    print()

    return vectorstore


# ==========================================================
# RETRIEVER
# ==========================================================

def get_retriever():

    vectorstore = get_vectorstore()

    return vectorstore.as_retriever(

        search_kwargs={
            "k": 4
        }
    )


# ==========================================================
# RAG SEARCH
# ==========================================================

def retrieve_knowledge(query):

    retriever = get_retriever()

    documents = retriever.invoke(query)

    if not documents:

        return "No relevant knowledge found."

    context_parts = []

    for doc in documents:

        if doc.page_content:

            context_parts.append(
                doc.page_content
            )

    if not context_parts:

        return "No relevant knowledge found."

    return "\n\n".join(
        context_parts
    )