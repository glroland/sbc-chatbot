import subprocess
import kfp
import kfp.client
from kfp import dsl, components
from kfp.dsl import Input, Output, Artifact
from kfp import compiler


@dsl.component(packages_to_install=['requests'])
def download_document(url: str, pdf: Output[Artifact]):
    print (f"Downloading Document: {url}")

    import requests

    response = requests.get(url, stream=True)
    response.raw.decode_content = True

    output_file = pdf.path
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024): 
            f.write(chunk)

    print ("Download complete")


@dsl.component(packages_to_install=['docling'])
def convert_pdf_to_document(pdf: Input[Artifact],
                            output_md: Output[Artifact],
                            output_json: Output[Artifact],
                            output_yaml: Output[Artifact]):
    print (f"Converting document: {pdf.path}")

    import json
    import yaml
    from pathlib import Path
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
    from docling.datamodel.pipeline_options import PdfPipelineOptions


    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False

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
                    pipeline_cls=StandardPdfPipeline, backend=PyPdfiumDocumentBackend, pipeline_options=pipeline_options,
                ),
                InputFormat.DOCX: WordFormatOption(
                    pipeline_cls=SimplePipeline  # , backend=MsWordDocumentBackend
                ),
            },
        )
    )

    res = doc_converter.convert(pdf.path)

    print(f"Document {res.input.file.name} converted.")
    print(res.document._export_to_indented_text(max_text_len=16))

    # Export Docling document format to markdowndoc:
    with open(output_md.path, "w") as fp:
        fp.write(res.document.export_to_markdown(image_mode = ImageRefMode.PLACEHOLDER))

    with open(output_json.path, "w") as fp:
        fp.write(json.dumps(res.document.export_to_dict(), indent=4))

    with open(output_yaml.path, "w") as fp:
        fp.write(yaml.safe_dump(res.document.export_to_dict()))


@dsl.component
def store_document_in_vector_db():
    pass


@dsl.pipeline(name="Process Document Pipeline")
def process_document_pipeline(url: str):

    download_task = download_document(url=url)
    download_task.set_caching_options(True)

    convert_task = convert_pdf_to_document(pdf=download_task.outputs['pdf'])
    convert_task.set_caching_options(True)
    convert_task.after(download_task)

    store_task = store_document_in_vector_db()
    store_task.set_caching_options(False)
    store_task.after(convert_task)


# Get OpenShift Token
token = subprocess.check_output("oc whoami -t", shell=True, text=True).strip()

# Connect to the pipeline server
print ("Connecting to pipeline server")
kfp_client = kfp.Client(host="https://ds-pipeline-dspa-baseball.apps.ocp.home.glroland.com/",
                        existing_token=token,
                        verify_ssl=False)

# Create a run for the pipeline
print ("Running Pipeline")
kfp_client.create_run_from_pipeline_func(
    process_document_pipeline,
    experiment_name="Download and Process Document Pipeline v1",
    arguments={
        "url": "https://www.cms.gov/CCIIO/Resources/Regulations-and-Guidance/Downloads/SBC-Sample-Completed.pdf",
    }
)

# Compile Pipeline
print ("Compiling Pipeline")
compiler.Compiler().compile(process_document_pipeline, 'process-document-pipeline.yaml')
