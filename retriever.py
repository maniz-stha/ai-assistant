import os
import logging
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.vector_stores.faiss import FaissVectorStore
from config import config

class Retriever:
    def __init__(self, query):
       self.query = query
       config.setup()

    def load_index(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
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
        else:
            logger.error("Documents has not been indexed yet.")



    def response(self):
        index = self.load_index()
        query_engine = index.as_query_engine()
        response = query_engine.query(self.query)
        return response

if __name__ == "__main__":
    retriever = Retriever("What are his primary technical skills?")
    response = retriever.response()
    print(response)
