# ingest_docs.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# --- Environment Setup ---
load_dotenv()

# --- Constants ---
DOCS_DIR = "source_documents"
CHROMA_PATH = "chroma_db"

def ingest_documents():
    """
    Loads documents from the source directory, splits them into chunks,
    and embeds them into a Chroma vector store for later retrieval.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY must be set in the .env file.")
        return

    if not os.path.exists(DOCS_DIR):
        print(f"Error: The source directory '{DOCS_DIR}' does not exist.")
        print("Please create it and add your design documents.")
        return

    print("🚀 Starting document ingestion...")

    # 1. Load all documents from the source directory
    documents = []
    for file in os.listdir(DOCS_DIR):
        file_path = os.path.join(DOCS_DIR, file)
        try:
            print(f"   -> Loading: {file}")
            loader = UnstructuredFileLoader(file_path)
            documents.extend(loader.load())
        except Exception as e:
            print(f"Warning: Could not load file {file}. Error: {e}")

    if not documents:
        print("No documents were loaded. Aborting.")
        return

    # 2. Split documents into smaller, manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Split {len(documents)} document(s) into {len(chunks)} chunks.")

    # 3. Create embeddings and persist them to the vector store
    print("🧠 Creating embeddings and building vector store... (This may take a moment)")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Create a new Chroma database from the chunks
    db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)

    print(f"✅ Ingestion complete. Vector store created at: '{CHROMA_PATH}'")

if __name__ == "__main__":
    ingest_documents()