import json
import tempfile
import unittest
from pathlib import Path

from ingestion import (
    Document,
    chunk_document,
    chunk_documents,
    load_documents,
    normalize_text,
    save_chunks,
    split_words,
)


class IngestionTests(unittest.TestCase):
    def test_normalize_text_removes_extra_spaces_and_blank_lines(self):
        raw_text = "  first\t\tline\r\n\r\n\r\nsecond   line  "

        normalized = normalize_text(raw_text)

        self.assertEqual(normalized, "first line\n\nsecond line")

    def test_split_words_returns_non_whitespace_tokens(self):
        self.assertEqual(split_words("one  two\nthree\tfour"), ["one", "two", "three", "four"])

    def test_load_documents_reads_txt_files_and_skips_empty_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            documents_dir = Path(temp_dir)
            (documents_dir / "b.txt").write_text("Second document", encoding="utf-8")
            (documents_dir / "a.txt").write_text(" First   document ", encoding="utf-8")
            (documents_dir / "empty.txt").write_text("   ", encoding="utf-8")
            (documents_dir / "ignore.md").write_text("Not loaded", encoding="utf-8")

            documents = load_documents(documents_dir)

        self.assertEqual(len(documents), 2)
        self.assertEqual([doc.source_name for doc in documents], ["a.txt", "b.txt"])
        self.assertEqual(documents[0].source_id, "doc_001")
        self.assertEqual(documents[0].text, "First document")

    def test_load_documents_raises_when_folder_is_missing(self):
        with self.assertRaises(FileNotFoundError):
            load_documents("folder_that_does_not_exist")

    def test_chunk_document_uses_word_size_and_overlap(self):
        document = Document(
            source_id="doc_001",
            source_name="sample.txt",
            path="documents/sample.txt",
            text=" ".join(f"word{i}" for i in range(1, 11)),
        )

        chunks = chunk_document(document, chunk_size_words=4, overlap_words=1)

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].text, "word1 word2 word3 word4")
        self.assertEqual(chunks[1].text, "word4 word5 word6 word7")
        self.assertEqual(chunks[2].text, "word7 word8 word9 word10")
        self.assertEqual(chunks[1].start_word, 3)
        self.assertEqual(chunks[1].end_word, 7)
        self.assertEqual(chunks[2].chunk_id, "doc_001_chunk_002")

    def test_chunk_document_keeps_short_document_as_one_chunk(self):
        document = Document(
            source_id="doc_002",
            source_name="short.txt",
            path="documents/short.txt",
            text="short document",
        )

        chunks = chunk_document(document, chunk_size_words=350, overlap_words=100)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "short document")
        self.assertEqual(chunks[0].start_word, 0)
        self.assertEqual(chunks[0].end_word, 2)

    def test_chunk_document_rejects_invalid_sizes(self):
        document = Document("doc_001", "sample.txt", "documents/sample.txt", "one two three")

        with self.assertRaises(ValueError):
            chunk_document(document, chunk_size_words=0, overlap_words=0)
        with self.assertRaises(ValueError):
            chunk_document(document, chunk_size_words=3, overlap_words=-1)
        with self.assertRaises(ValueError):
            chunk_document(document, chunk_size_words=3, overlap_words=3)

    def test_chunk_documents_combines_chunks_from_all_documents(self):
        documents = [
            Document("doc_001", "one.txt", "documents/one.txt", "one two three"),
            Document("doc_002", "two.txt", "documents/two.txt", "four five six"),
        ]

        chunks = chunk_documents(documents, chunk_size_words=2, overlap_words=0)

        self.assertEqual(len(chunks), 4)
        self.assertEqual([chunk.source_name for chunk in chunks], ["one.txt", "one.txt", "two.txt", "two.txt"])

    def test_save_chunks_writes_expected_json_metadata(self):
        document = Document("doc_001", "sample.txt", "documents/sample.txt", "one two three four")
        chunks = chunk_document(document, chunk_size_words=2, overlap_words=0)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "chunks.json"
            save_chunks(chunks, output_path, chunk_size_words=2, overlap_words=0)
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["chunk_count"], 2)
        self.assertEqual(saved["chunk_size_words"], 2)
        self.assertEqual(saved["overlap_words"], 0)
        self.assertEqual(saved["chunks"][0]["source_name"], "sample.txt")
        self.assertEqual(saved["chunks"][0]["text"], "one two")


if __name__ == "__main__":
    unittest.main()
