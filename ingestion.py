import os
import logging
import faiss
from llama_index.core import (
    VectorStoreIndex, 
    StorageContext, 
    load_index_from_storage, 
    Settings
)
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.faiss import FaissVectorStore

from config import config
from data_source.resume_json import documents as resume_documents
from data_source.github import documents as github_documents

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_settings():
    """Configure global settings for LlamaIndex."""
    logger.info(f"Using embedding model: {config.EMBEDDING_MODEL}")
    Settings.embed_model = GoogleGenAIEmbedding(
        model_name=config.EMBEDDING_MODEL,
        api_key=config.GOOGLE_API_KEY,
        embed_batch_size=100
    )
    
    logger.info(f"Using inference model: {config.INFERENCE_MODEL}")
    Settings.llm = GoogleGenAI(
        model=f"models/{config.INFERENCE_MODEL}",
        api_key=config.GOOGLE_API_KEY
    )

def get_documents():
    """Load documents from all sources."""
    logger.info("Loading documents from sources...")
    docs = [*resume_documents()]
    
    # Try to load GitHub documents if token is available
    if os.getenv("GITHUB_ACCESS_TOKEN"):
        try:
            gh_docs = github_documents()
            docs.extend(gh_docs)
            logger.info(f"Loaded {len(gh_docs)} documents from GitHub")
        except Exception as e:
            logger.error(f"Failed to load GitHub documents: {e}")
    else:
        logger.warning("GITHUB_ACCESS_TOKEN not found, skipping GitHub ingestion.")
    
    logger.info(f"Total documents loaded: {len(docs)}")
    return docs

def build_or_load_index():
    """Build a new index or load an existing one from disk."""
    
    # Check if storage exists and is not empty
    persist_dir = config.PERSIST_DIR
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        logger.info(f"Loading existing index from {persist_dir}...")
        try:
            vector_store = FaissVectorStore.from_persist_dir(persist_dir)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store, 
                persist_dir=persist_dir
            )
            index = load_index_from_storage(storage_context)
            logger.info("Index loaded successfully.")
            return index
        except Exception as e:
            logger.error(f"Failed to load index: {e}. Rebuilding...")

    # Build new index
    logger.info("Building a new index...")
    documents = get_documents()
    
    # Determine embedding dimension dynamically
    logger.info("Detecting embedding dimension...")
    sample_embedding = Settings.embed_model.get_text_embedding("sample text")
    embed_dim = len(sample_embedding)
    logger.info(f"Dimension detected: {embed_dim}")

    # Initialize FAISS index
    # IndexHNSWFlat is efficient for small to medium datasets
    faiss_index = faiss.IndexHNSWFlat(embed_dim, 32)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )
    
    # Persist the index
    os.makedirs(config.PERSIST_DIR, exist_ok=True)
    index.storage_context.persist(persist_dir=config.PERSIST_DIR)
    logger.info(f"Index created and persisted to {config.PERSIST_DIR}")
    return index

if __name__ == "__main__":
    setup_settings()
    index = build_or_load_index()
    
    # Optional: Test query to verify index is working
    logger.info("Running verification query...")
    query_engine = index.as_query_engine()
    response = query_engine.query("What are the primary technical skills?")
    print("\n--- Verification Query ---")
    print(f"Response: {response}")
    print("--------------------------\n")
