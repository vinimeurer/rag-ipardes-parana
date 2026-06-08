from unittest.mock import MagicMock, patch

from src.ingestion.ingestion_pipeline import (
    IngestionPipeline,
    PipelineDocumentResult,
    PipelineRunResult,
)


@patch("src.ingestion.ingestion_pipeline.ExtractionSerializer")
@patch("src.ingestion.ingestion_pipeline.DoclingPDFExtractor")
class TestPipelineRunResult:

    def test_total_property(self, mock_extractor, mock_serializer):

        result = PipelineRunResult(
            documents=[
                PipelineDocumentResult("a", True),
                PipelineDocumentResult("b", True),
                PipelineDocumentResult("c", False),
            ]
        )

        assert result.total == 3

    def test_successes_property(self, mock_extractor, mock_serializer):

        result = PipelineRunResult(
            documents=[
                PipelineDocumentResult("a", True),
                PipelineDocumentResult("b", True, skipped=True),
                PipelineDocumentResult("c", False),
            ]
        )

        assert result.successes == 1

    def test_skipped_property(self, mock_extractor, mock_serializer):

        result = PipelineRunResult(
            documents=[
                PipelineDocumentResult("a", True, skipped=True),
                PipelineDocumentResult("b", True, skipped=True),
                PipelineDocumentResult("c", False),
            ]
        )

        assert result.skipped == 2

    def test_failures_property(self, mock_extractor, mock_serializer):

        result = PipelineRunResult(
            documents=[
                PipelineDocumentResult("a", False),
                PipelineDocumentResult("b", False),
                PipelineDocumentResult("c", True, skipped=True),
            ]
        )

        assert result.failures == 2

    def test_summary(self, mock_extractor, mock_serializer):

        result = PipelineRunResult(
            documents=[
                PipelineDocumentResult("a", True),
                PipelineDocumentResult("b", True, skipped=True),
                PipelineDocumentResult("c", False),
            ]
        )

        summary = result.summary()

        assert "3 docs" in summary
        assert "1 OK" in summary
        assert "1 pulados" in summary
        assert "1 falhas" in summary


@patch("src.ingestion.ingestion_pipeline.ExtractionSerializer")
@patch("src.ingestion.ingestion_pipeline.DoclingPDFExtractor")
class TestIngestionPipeline:

    def test_pipeline_initialization(
        self,
        mock_extractor_class,
        mock_serializer_class,
    ):

        config = MagicMock()

        pipeline = IngestionPipeline(config)

        config.ensure_dirs.assert_called_once()

        assert pipeline.config == config

    def test_run_with_specific_keys(
        self,
        mock_extractor_class,
        mock_serializer_class,
    ):

        config = MagicMock()
        config.pdf_sources = {
            "doc1": "file1.pdf",
            "doc2": "file2.pdf",
        }

        pipeline = IngestionPipeline(config)

        with patch.object(
            pipeline,
            "_process_document",
            return_value=PipelineDocumentResult(
                pdf_key="doc1",
                success=True,
            ),
        ) as mock_process:

            result = pipeline.run(["doc1"])

            assert result.total == 1
            mock_process.assert_called_once_with("doc1")

    def test_run_all_documents(
        self,
        mock_extractor_class,
        mock_serializer_class,
    ):

        config = MagicMock()
        config.pdf_sources = {
            "doc1": "file1.pdf",
            "doc2": "file2.pdf",
        }

        pipeline = IngestionPipeline(config)

        with patch.object(
            pipeline,
            "_process_document",
            return_value=PipelineDocumentResult(
                pdf_key="doc",
                success=True,
            ),
        ) as mock_process:

            result = pipeline.run()

            assert result.total == 2
            assert mock_process.call_count == 2

    def test_process_document_already_extracted(
        self,
        mock_extractor_class,
        mock_serializer_class,
    ):

        config = MagicMock()

        pipeline = IngestionPipeline(config)

        pipeline.serializer.already_extracted.return_value = True

        result = pipeline._process_document("test_doc")

        assert result.success
        assert result.skipped
        assert result.pdf_key == "test_doc"

    def test_process_document_extraction_failure(
        self,
        mock_extractor_class,
        mock_serializer_class,
    ):

        config = MagicMock()

        pipeline = IngestionPipeline(config)

        pipeline.serializer.already_extracted.return_value = False

        extraction = MagicMock()
        extraction.success = False
        extraction.error = "failed"

        pipeline.extractor.extract.return_value = extraction

        result = pipeline._process_document("test_doc")

        assert not result.success
        assert result.error == "failed"

    def test_process_document_success(
        self,
        mock_extractor_class,
        mock_serializer_class,
    ):

        config = MagicMock()

        pipeline = IngestionPipeline(config)

        pipeline.serializer.already_extracted.return_value = False

        extraction = MagicMock()
        extraction.success = True
        extraction.full_text = "text"
        extraction.full_markdown = "markdown"

        pipeline.extractor.extract.return_value = extraction

        pipeline.serializer.save.return_value = {
            "text": "saved.txt"
        }

        result = pipeline._process_document("test_doc")

        assert result.success
        assert result.saved_artifacts == {
            "text": "saved.txt"
        }

        pipeline.serializer.save.assert_called_once_with(
            extraction,
            extraction.full_text,
            extraction.full_markdown,
        )