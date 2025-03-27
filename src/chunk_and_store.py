import logging
import click
import json
import os
from pprint import pprint
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

VDB_DB_NAME = "sbcchatbot"
VDB_COLLECTION_MD = "sbc"
EMBEDDINGS_MODEL = "sentence-transformers/all-mpnet-base-v2"

# Setup Logging
logging.basicConfig(level=logging.DEBUG,
    handlers=[
        # no need from cli - logging.FileHandler("chunk_and_store.log"),
        logging.StreamHandler()
    ])

def import_yaml(vdb_client, model, file_key, data):
    pass

def import_json(vdb_client, model, file_key, data):
    document = json.loads(data)

    #print(yaml.dump(data, indent=2, sort_keys=False))
#    pprint(document)
#    print(len(document)) 

    document_tables = document["tables"]
    iq_table = document_tables[0]
    cme_table = document_tables[1]
    cme_table_grid = cme_table["data"]["grid"]

#    pprint (cme_table)
    for row in cme_table_grid:
        for cell in row:
            pprint (cell["text"])

        print("")

#    for text in document["texts"]:
#        print(text)
#        if text["text"].startswith("The Summary of Benefits and Coverage"):
#            print(text)
#            print("")



def import_md(vdb_client, model, file_key, data):
    # encode data
    logger.info("Creating embeding for MD content....")
    embedding = model.encode([data])
    logger.debug("Done")

    # insert into vecotor database
    logger.info("Storing record into vector db....")
    row = {
        "file": file_key,
        "sbc": embedding.tolist()
    }
    vdb_client.insert(collection_name=VDB_COLLECTION_MD, records=[row])
    logger.debug(f"Inserted row into collection")


@click.command()
@click.argument('input_file')
def cli_main(input_file):
    """ CLI Utility that loads a docling document in json format and stores as
        chunks document in a vector database.
        
        input_file - docling document in json format
    """
    logger.info(f"Processing Input File: {input_file}")

    # connect to vector store
    logger.info("Connecting to Vector Database Service...")
    vdb_client = MilvusClient(
        uri="http://db:19530",
        token="root:Milvus"
    )

    # connect to vector database
    logger.info("Connecting to Vector DB...")
    vdb_client.using_database(VDB_DB_NAME)
    logger.debug("Connected to Vector DB...")

    # load input file
    input_file_abs = os.path.abspath(input_file)
    logger.info(f"Input File: {input_file_abs}")
    with open(input_file_abs, 'r') as f:
        input_file_contents = f.read()

    # calculate file key
    filename = os.path.basename(input_file_abs)
    file_key = os.path.splitext(filename)[0]
    logger.info(f"File Key: {file_key}")

    # download embeddings model
    logger.info("Downloading embeddings model...")
    model = SentenceTransformer(EMBEDDINGS_MODEL)
    logger.info("Downloaded.")

    # process input file
    if input_file_abs.lower().endswith(".yaml"):
         logger.info("Importing file as YAML")
         import_yaml(vdb_client, model, file_key, input_file_contents)
    elif input_file_abs.lower().endswith(".json"):
         logger.info("Importing file as JSON")
         import_json(vdb_client, model, file_key, input_file_contents)
    elif input_file_abs.lower().endswith(".md"):
         logger.info("Importing file as Markdown")
         import_md(vdb_client, model, file_key, input_file_contents)
    else:
         logger.error(f"Unsupported file type: {input_file_abs}")
         raise ValueError(f"Unsupported file type: {input_file_abs}")

    # close database connection
    vdb_client.close()

    # all done
    logger.info("File processed!")

if __name__ == '__main__':
    cli_main(None)
