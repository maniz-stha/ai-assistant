import os
import logging
from llama_index.core import (
    StorageContext,
    load_index_from_storage,
)
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core.memory import ChatMemoryBuffer
from collections import OrderedDict
from config import config
from prompt_templates import system_prompt, chat_prompt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        config.setup()
        self.index = self.load_index()
        # OrderedDict to maintain session order for LRU eviction of memory buffers
        self.chat_memories = OrderedDict()
        self.MAX_SESSIONS = 50 # Prevent memory exhaustion by limiting active sessions

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

    def get_chat_engine(self, session_id):
        if not self.index:
            return None
        
        # Check if chat memory for this session already exists
        if session_id in self.chat_memories:
            # Move to end to mark it as the most recently used
            self.chat_memories.move_to_end(session_id)
            memory = self.chat_memories[session_id]
        else:
            # Evict oldest session if we are at capacity
            if len(self.chat_memories) >= self.MAX_SESSIONS:
                oldest_session, _ = self.chat_memories.popitem(last=False)
                logger.info(f"Evicted oldest session memory: {oldest_session}")

            # Create new chat memory for new session
            memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
            
            # Store memory for future use in the same session
            self.chat_memories[session_id] = memory
        
        # Construct chat engine on the fly using the cached memory
        chat_engine = self.index.as_chat_engine(
            chat_mode="context",
            memory=memory,
            system_prompt=system_prompt.template,
            context_template=chat_prompt
        )
        return chat_engine

    def query(self, user_query, session_id="default"):
        chat_engine = self.get_chat_engine(session_id)
        if not chat_engine:
            return "Error: Could not initialize chat engine. Please check if the index exists."
        
        response = chat_engine.chat(user_query)
        return str(response)

if __name__ == "__main__":
    retriever = Retriever()
    if retriever.index:
        # Test session persistence
        print(f"\n--- Turn 1 ---")
        response1 = retriever.query("What are his primary technical skills?", session_id="test-123")
        print(f"Response 1: {response1}")
        
        print(f"\n--- Turn 2 (with memory) ---")
        response2 = retriever.query("Can you tell me more about his Python experience?", session_id="test-123")
        print(f"Response 2: {response2}")
