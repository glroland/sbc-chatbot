import subprocess
import kfp
import kfp.client
from kfp import dsl, components
from kfp.dsl import InputPath, Output, Artifact, Model
from kfp import compiler

process_document_pipeline = components.load_component_from_file('process-document-pipeline.yaml')

def recreate_vdb():
    pass


@dsl.pipeline(name="SBC Document List Pipeline")
def process_all_files_pipeline(url: str):

    import requests

    print (f"URL: {url}")
#    response = requests.get(url)
    response = requests.get("https://raw.githubusercontent.com/glroland/sbc-chatbot/refs/heads/main/samples/SOURCES.txt")
    lines = response.text.splitlines()

    files = []
    for line in lines:
        line = line.strip()
        if len(line) > 0:
            files.append(line)
            print(line)

    with dsl.ParallelFor(files) as file:
        process_document_pipeline(url=file)


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
    process_all_files_pipeline,
    experiment_name="Process Document Experiment v1",
    arguments={
        "url": "https://raw.githubusercontent.com/glroland/sbc-chatbot/refs/heads/main/samples/SOURCES.txt"
    }
)

# Compile Pipeline
print ("Compiling Pipeline")
compiler.Compiler().compile(process_document_pipeline, 'process-all-files-pipeline.yaml')
