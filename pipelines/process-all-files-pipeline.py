import subprocess
import kfp
import kfp.client
from kfp import dsl, components
from kfp.dsl import InputPath, Output, Artifact, Model
from kfp import compiler

process_document_pipeline = components.load_component_from_file('process-document-pipeline.yaml')

@dsl.component(packages_to_install=['pymilvus'])
def recreate_vector_db():
    print ("Recreating database")

    from pymilvus import MilvusClient, MilvusException, DataType

    VDB_DB_NAME = "sbcchatbot"
    VDB_COLLECTION_MD = "sbcmd"
    VDB_COLLECTION_PHRASES = "sbcphrases"
    DIMENSIONS = 768
    TTL = 86400*7

    # connect to vector store
    print("Connecting to Vector Database Service...")
    vdb_client = MilvusClient(
        uri="http://db:19530",
        token="root:Milvus"
    )

    # drop all collections that happen to be in the database
    try:
        vdb_client.using_database(VDB_DB_NAME)
        print("Database exists.  Purging all collections before recreating")
        for c in vdb_client.list_collections():
            print(f"Dropping Collection: {c}")
            vdb_client.drop_collection(c)
    except MilvusException as e:
        print(f"Database didn't exist - unable to purge collections: {e}")

    # recreate database
    print("Creating Vector DB...")
    try:
        print("Dropping Vector DB")
        vdb_client.drop_database(VDB_DB_NAME)
        print("Vector DB Dropped")
    except MilvusException as e:
        print(f"Database didn't exist - unable to drop: {e}")
    vdb_client.create_database(VDB_DB_NAME, "vectorstore")
    vdb_client.using_database(VDB_DB_NAME)
    print("Vector DB Re-created")

    # create markdown collection
    print("Creating core SBC collection for vectorized markdown content")
    md_schema = vdb_client.create_schema(auto_id=False, enable_dynamic_field=True)
    md_schema.add_field(field_name="file", datatype=DataType.VARCHAR, max_length=200, is_primary=True)
    md_schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=DIMENSIONS)
    md_schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=60535)
    md_index_params = vdb_client.prepare_index_params()
    md_index_params.add_index(field_name="vector", index_type="AUTOINDEX")
    vdb_client.create_collection(collection_name=VDB_COLLECTION_MD,
                                 schema=md_schema,
                                 properties={"collection.ttl.seconds": TTL},
                                 index_params=md_index_params)
    print("Collection created")

    # create phrases collection
    print("Creating core SBC collection for vectorized document phrases content")
    phrases_schema = vdb_client.create_schema(auto_id=False, enable_dynamic_field=True)
    phrases_schema.add_field(field_name="phrase_key", datatype=DataType.VARCHAR, max_length=1000, is_primary=True)
    phrases_schema.add_field(field_name="file", datatype=DataType.VARCHAR, max_length=200)
    phrases_schema.add_field(field_name="phrase_type", datatype=DataType.VARCHAR, max_length=200)
    phrases_schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=DIMENSIONS)
    phrases_schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=60535)
    phrases_index_params = vdb_client.prepare_index_params()
    phrases_index_params.add_index(field_name="vector", index_type="AUTOINDEX")
    vdb_client.create_collection(collection_name=VDB_COLLECTION_PHRASES,
                                 schema=phrases_schema,
                                 properties={"collection.ttl.seconds": TTL},
                                 index_params=phrases_index_params)
    print("Collection created")

    # close database connection
    vdb_client.close()

    # all done
    print("Recreated database!")


@dsl.component()
def pull_sources(url: str) -> list:

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

    return files


@dsl.pipeline(name="SBC Document List Pipeline")
def process_all_files_pipeline(url: str):

    recreate_db_task = recreate_vector_db()
    recreate_db_task.set_caching_options(False)

    pull_sources_task = pull_sources(url=url)
    pull_sources_task.set_caching_options(True)
    pull_sources_task.after(recreate_db_task)

    with dsl.ParallelFor(pull_sources_task.output) as file:
        process_doc_task = process_document_pipeline(url=file)
        process_doc_task.set_caching_options(False)


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
    experiment_name="Process All Documents v1",
    arguments={
        "url": "https://raw.githubusercontent.com/glroland/sbc-chatbot/refs/heads/main/samples/SOURCES.txt"
    }
)

# Compile Pipeline
print ("Compiling Pipeline")
compiler.Compiler().compile(process_document_pipeline, 'process-all-files-pipeline.yaml')
