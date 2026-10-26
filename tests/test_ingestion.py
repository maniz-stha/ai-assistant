import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("GOOGLE_API_KEY", "test-key")

from llama_index.core import Document, Settings
from llama_index.core.embeddings import MockEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

import ingestion
from retriever import Retriever


class IngestionTests(unittest.TestCase):
    def test_setup_does_not_initialize_chat_model(self):
        previous = Settings._embed_model
        previous_parser = Settings._node_parser
        try:
            with patch("ingestion.GoogleGenAI", side_effect=AssertionError("chat model initialized"), create=True):
                ingestion.setup_settings()
        finally:
            Settings._embed_model = previous
            Settings._node_parser = previous_parser

    def test_collects_pdf_and_github_documents(self):
        resume = Document(text="Resume fact", metadata={"source": "current.pdf", "page": 1})
        repo = Document(text="GitHub Repository: new-project")
        with patch("ingestion.resume_documents", return_value=[resume]), \
             patch("ingestion.review_conflicts"), \
             patch("ingestion.github_documents", return_value=[repo]):
            self.assertEqual(ingestion.get_documents(), [resume, repo])

    def test_github_failure_does_not_fall_back_to_resume_only(self):
        with patch("ingestion.resume_documents", return_value=[Document(text="Resume")]), \
             patch("ingestion.review_conflicts"), \
             patch("ingestion.github_documents", side_effect=RuntimeError("GitHub unavailable")):
            with self.assertRaisesRegex(RuntimeError, "GitHub unavailable"):
                ingestion.get_documents()

    def test_rebuilds_existing_index_and_publishes_loadable_faiss(self):
        previous = Settings._embed_model
        Settings.embed_model = MockEmbedding(embed_dim=8)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "storage"
                target.mkdir()
                (target / "old.txt").write_text("old index")
                with patch.object(ingestion.config, "PERSIST_DIR", str(target)), \
                     patch("ingestion.get_documents", return_value=[Document(text="Fresh resume and GitHub content")]):
                    ingestion.build_index()
                self.assertFalse((target / "old.txt").exists())
                self.assertIsInstance(FaissVectorStore.from_persist_dir(str(target)), FaissVectorStore)
                self.assertTrue((target / "docstore.json").exists())
        finally:
            Settings._embed_model = previous

    def test_failed_build_keeps_previous_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "storage"
            target.mkdir()
            (target / "old.txt").write_text("old index")
            with patch.object(ingestion.config, "PERSIST_DIR", str(target)), \
                 patch("ingestion.get_documents", side_effect=RuntimeError("source failed")):
                with self.assertRaisesRegex(RuntimeError, "source failed"):
                    ingestion.build_index()
            self.assertEqual((target / "old.txt").read_text(), "old index")

    def test_api_recovers_index_after_interrupted_publish(self):
        previous = Settings._embed_model
        Settings.embed_model = MockEmbedding(embed_dim=8)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "storage"
                with patch.object(ingestion.config, "PERSIST_DIR", str(target)), \
                     patch("ingestion.get_documents", return_value=[Document(text="Current resume")]):
                    ingestion.build_index()
                    backup = target.with_name("storage.previous-interrupted")
                    target.rename(backup)
                    self.assertIsNotNone(Retriever.__new__(Retriever).load_index())
                    self.assertTrue(target.exists())
                    self.assertFalse(backup.exists())
        finally:
            Settings._embed_model = previous

    def test_publish_rolls_back_if_swap_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "storage"
            stage = root / "stage"
            target.mkdir()
            stage.mkdir()
            (target / "old.txt").write_text("old index")
            (stage / "new.txt").write_text("new index")
            original = Path.rename

            def fail_stage_swap(path, destination):
                if path == stage and destination == target:
                    raise OSError("swap failed")
                return original(path, destination)

            with patch.object(Path, "rename", fail_stage_swap):
                with self.assertRaisesRegex(OSError, "swap failed"):
                    ingestion.publish_index(stage, target)
            self.assertEqual((target / "old.txt").read_text(), "old index")

    def test_backup_cleanup_failure_does_not_report_failed_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "storage"
            stage = root / "stage"
            target.mkdir()
            stage.mkdir()
            (target / "old.txt").write_text("old index")
            (stage / "new.txt").write_text("new index")
            with patch("ingestion.shutil.rmtree", side_effect=OSError("cleanup failed")):
                ingestion.publish_index(stage, target)
            self.assertEqual((target / "new.txt").read_text(), "new index")
