#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import logging
from llama_index.core import Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI

load_dotenv()

class Config:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    ALLOWED_ORIGIN: str = os.getenv("ALLOWED_ORIGIN", "*")
    INFERENCE_MODEL: str = "gemini-3.1-flash-lite"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    PERSIST_DIR: str = "./storage"

    def setup(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        logger.info(f"Using embedding model: {self.EMBEDDING_MODEL}")
        Settings.embed_model = GoogleGenAIEmbedding(
            model_name=config.EMBEDDING_MODEL,
            api_key=self.GOOGLE_API_KEY,
            embed_batch_size=100
        )

        logger.info(f"Using inference model: {self.INFERENCE_MODEL}")
        Settings.llm = GoogleGenAI(
            model=f"models/{self.INFERENCE_MODEL}",
            api_key=self.GOOGLE_API_KEY
        )

    def validate(self):
        required = ("GOOGLE_API_KEY", "INFERENCE_MODEL", "EMBEDDING_MODEL")
        missing = [k for k in required if not getattr(self, k)]
        if missing:
            raise ValueError(f"Missing require env vars: {missing}")


config = Config()
config.validate()
