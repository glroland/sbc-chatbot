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


@dsl.component
def convert_pdf_to_document(pdf: Input[Artifact]):
    print (f"Converting document: {pdf.path}")




    pass

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
