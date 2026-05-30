import os
import logging
from llama_index.core import (
    StorageContext,
    load_index_from_storage,
)
from llama_index.vector_stores.faiss import FaissVectorStore
from config import config
from prompt_templates import system_prompt, chat_prompt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        config.setup()
        self.index = self.load_index()

    def load_index(self):
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
                logger.error(f"Failed to load index: {e}")
                return None
        else:
            logger.error(f"Storage directory {persist_dir} is empty or does not exist. Please run ingestion.py first.")
            return None

    def get_chat_engine(self):
        if not self.index:
            return None
        
        # Use ContextChatEngine for RAG
        # system_prompt: persona description
        # context_template: how to format context + query (must be a PromptTemplate object)
        chat_engine = self.index.as_chat_engine(
            chat_mode="context",
            system_prompt=system_prompt.template,
            context_template=chat_prompt
        )
        
        return chat_engine

    def query(self, user_query):
        chat_engine = self.get_chat_engine()
        if not chat_engine:
            return "Error: Could not initialize chat engine. Please check if the index exists."
        
        response = chat_engine.chat(user_query)
        return response

if __name__ == "__main__":
    retriever = Retriever()
    if retriever.index:
        response = retriever.query("What are his primary technical skills?")
        print(f"\nResponse: {response}")
