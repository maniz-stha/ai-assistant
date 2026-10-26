import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from llama_index.core import Document

os.environ.setdefault("GOOGLE_API_KEY", "test-key")


def write_pdf(path: Path, text: str = "") -> None:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii") if text else b""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
    ]
    body = b"%PDF-1.4\n"
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(body))
        body += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    start = len(body)
    body += b"xref\n0 6\n0000000000 65535 f \n"
    body += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    body += b"trailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n" + str(start).encode() + b"\n%%EOF\n"
    path.write_bytes(body)


class ResumePdfTests(unittest.TestCase):
    def test_model_report_is_parsed_for_multiple_pdfs(self):
        from data_source.resume_pdf import ConflictReport, conflicts_from_model

        docs = [
            Document(text="12 years", metadata={"source": "old.pdf", "page": 1}),
            Document(text="15 years", metadata={"source": "new.pdf", "page": 2}),
        ]
        class Response:
            parsed = ConflictReport.model_validate({"conflicts": [{"field": "experience", "claims": [
                {"source": "old.pdf", "value": "12 years"},
                {"source": "new.pdf", "value": "15 years"},
            ]}]})

        with patch("data_source.resume_pdf.genai.Client") as client:
            client.return_value.models.generate_content.return_value = Response()
            conflicts = conflicts_from_model(docs)
        self.assertEqual(conflicts[0].field, "experience")
        self.assertIn("PDF: old.pdf", client.return_value.models.generate_content.call_args.kwargs["contents"])
        self.assertIn("PDF: new.pdf", client.return_value.models.generate_content.call_args.kwargs["contents"])

    def test_extracts_pdf_page_with_source(self):
        from data_source.resume_pdf import documents

        with tempfile.TemporaryDirectory() as tmp:
            write_pdf(Path(tmp) / "current.pdf", "Senior Python Engineer")
            pages = documents(Path(tmp))
        self.assertEqual(len(pages), 1)
        self.assertIn("Senior Python Engineer", pages[0].text)
        self.assertEqual(pages[0].metadata, {"source": "current.pdf", "source_type": "resume", "page": 1})

    def test_rejects_missing_and_unreadable_pdfs(self):
        from data_source.resume_pdf import documents

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "No resume PDFs"):
                documents(Path(tmp))
            write_pdf(Path(tmp) / "scan.pdf")
            with self.assertRaisesRegex(ValueError, "scan.pdf"):
                documents(Path(tmp))

    def test_conflicts_stop_ingestion_with_sources(self):
        from data_source.resume_pdf import review_conflicts

        docs = [
            Document(text="12 years of experience", metadata={"source": "old.pdf", "page": 1}),
            Document(text="15 years of experience", metadata={"source": "new.pdf", "page": 1}),
        ]
        with patch("data_source.resume_pdf.conflicts_from_model", return_value=[
            {"field": "experience", "claims": [
                {"source": "old.pdf", "value": "12 years"},
                {"source": "new.pdf", "value": "15 years"},
            ]}
        ]):
            with self.assertRaisesRegex(ValueError, "old.pdf.*new.pdf"):
                review_conflicts(docs)

    def test_rejects_invalid_conflict_report(self):
        from data_source.resume_pdf import review_conflicts

        docs = [
            Document(text="one", metadata={"source": "a.pdf", "page": 1}),
            Document(text="two", metadata={"source": "b.pdf", "page": 1}),
        ]
        with patch("data_source.resume_pdf.conflicts_from_model", return_value=[
            {"field": "title", "claims": [
                {"source": "unknown.pdf", "value": "Senior"},
                {"source": "b.pdf", "value": "Junior"},
            ]}
        ]):
            with self.assertRaisesRegex(ValueError, "Invalid conflict report"):
                review_conflicts(docs)

    def test_rejects_same_source_as_a_conflict(self):
        from data_source.resume_pdf import review_conflicts

        docs = [
            Document(text="one", metadata={"source": "a.pdf", "page": 1}),
            Document(text="two", metadata={"source": "b.pdf", "page": 1}),
        ]
        with patch("data_source.resume_pdf.conflicts_from_model", return_value=[
            {"field": "title", "claims": [
                {"source": "a.pdf", "value": "Senior"},
                {"source": "a.pdf", "value": "Junior"},
            ]}
        ]):
            with self.assertRaisesRegex(ValueError, "Invalid conflict report"):
                review_conflicts(docs)
