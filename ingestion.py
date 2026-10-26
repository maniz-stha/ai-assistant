"""Build a fresh local FAISS index from active resumes and GitHub."""

import logging
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

import faiss
from llama_index.core import Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

from config import config
from data_source.github import documents as github_documents
from data_source.resume_pdf import documents as resume_documents, review_conflicts


logger = logging.getLogger(__name__)


def setup_settings():
    Settings.embed_model = GoogleGenAIEmbedding(
        model_name=config.EMBEDDING_MODEL,
        api_key=config.GOOGLE_API_KEY,
        embed_batch_size=100,
    )
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)


def get_documents():
    resumes = resume_documents()
    review_conflicts(resumes)
    github = github_documents()
    logger.info("Loaded %s resume pages and %s GitHub documents", len(resumes), len(github))
    return [*resumes, *github]


def publish_index(staged: Path, target: Path) -> None:
    """Swap a validated index into place, restoring the old one if the swap fails."""
    backup = target.with_name(f"{target.name}.previous-{uuid4().hex}")
    had_previous = target.exists()
    if had_previous:
        target.rename(backup)
    try:
        staged.rename(target)
    except Exception:
        if had_previous:
            backup.rename(target)
        raise
    if had_previous:
        try:
            shutil.rmtree(backup)
        except OSError as exc:
            logger.warning("New index published, but could not remove backup %s: %s", backup, exc)


def build_index():
    documents = get_documents()
    if not documents:
        raise ValueError("No documents to index")

    target = Path(config.PERSIST_DIR)
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=f"{target.name}.build-", dir=target.parent))
    try:
        dimension = len(Settings.embed_model.get_text_embedding("sample text"))
        vector_store = FaissVectorStore(faiss_index=faiss.IndexHNSWFlat(dimension, 32))
        storage = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(documents, storage_context=storage, show_progress=True)
        index.storage_context.persist(persist_dir=str(staged))

        # Catch incomplete or incompatible FAISS files before touching the old index.
        persisted_store = FaissVectorStore.from_persist_dir(str(staged))
        persisted_storage = StorageContext.from_defaults(vector_store=persisted_store, persist_dir=str(staged))
        load_index_from_storage(persisted_storage)

        publish_index(staged, target)
        logger.info("Index built and published to %s", target)
        return index
    finally:
        if staged.exists():
            shutil.rmtree(staged)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    setup_settings()
    build_index()
