import logging
import json
import yaml
import logging
from pathlib import Path
import click
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling_core.types.doc import ImageRefMode
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

logger = logging.getLogger(__name__)

# Setup Logging
logging.basicConfig(level=logging.DEBUG,
    handlers=[
        # no need from cli - logging.FileHandler("convert.log"),
        logging.StreamHandler()
    ])

@click.command()
@click.argument('input_file')
@click.argument('output_dir')
def cli_main(input_file, output_dir):

    doc_converter = (
        DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.IMAGE,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.PPTX,
                InputFormat.ASCIIDOC,
                InputFormat.CSV,
                InputFormat.MD,
            ],  # whitelist formats, non-matching files are ignored.
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=StandardPdfPipeline, backend=PyPdfiumDocumentBackend
                ),
                InputFormat.DOCX: WordFormatOption(
                    pipeline_cls=SimplePipeline  # , backend=MsWordDocumentBackend
                ),
            },
        )
    )

    res = doc_converter.convert(input_file)

    out_path = Path(output_dir)
    print(
        f"Document {res.input.file.name} converted."
        f"\nSaved markdown output to: {str(out_path)}"
    )
    logger.debug(res.document._export_to_indented_text(max_text_len=16))
    # Export Docling document format to markdowndoc:
    with (out_path / f"{res.input.file.stem}.md").open("w") as fp:
        fp.write(res.document.export_to_markdown(image_mode = ImageRefMode.PLACEHOLDER))

    with (out_path / f"{res.input.file.stem}.json").open("w") as fp:
        fp.write(json.dumps(res.document.export_to_dict(), indent=4))

    with (out_path / f"{res.input.file.stem}.yaml").open("w") as fp:
        fp.write(yaml.safe_dump(res.document.export_to_dict()))


if __name__ == '__main__':
    cli_main(None, None)
