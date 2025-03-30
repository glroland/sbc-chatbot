import logging
import click
import json
import os
from pprint import pprint
import numpy as np
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

VDB_DB_NAME = "sbcchatbot"
VDB_COLLECTION_MD = "sbcmd"
VDB_COLLECTION_PHRASES = "sbcphrases"
EMBEDDINGS_MODEL = "sentence-transformers/all-mpnet-base-v2"

# Setup Logging
logging.basicConfig(level=logging.DEBUG,
    handlers=[
        # no need from cli - logging.FileHandler("chunk_and_store.log"),
        logging.StreamHandler()
    ])

def encode_text(model, data):
    # encode data
    logger.info("Creating embeding for content....")
    embedding = model.encode([data])
    embedding_vector = embedding.astype(np.float32).tolist()
    logger.debug("Done")

    return embedding_vector[0]

def import_yaml(vdb_client, model, file_key, data):
    pass

def is_table_of_type(table, string_array):
    if "data" in table and "grid" in table["data"] and len(table["data"]["grid"]) > 0:
        table_grid = table["data"]["grid"]
        node1 = table_grid[0]
        if len(node1) > 0:
            node2 = table_grid[0][0]
            if "text" in node2:
                table_type = node2["text"]
                for s in string_array:
                    if not s in table_type:
                        return False

    return True

def docling_tables_to_string_table(list_of_tables):
    string_table = []
    string_result = ""

    for table in list_of_tables:
        if "data" in table and "grid" in table["data"] and len(table["data"]["grid"]) > 0:
            table_grid = table["data"]["grid"]

            for row in table_grid:
                r_array = []
                for cell in row:
                    r_array.append(cell["text"])
                    string_result += cell["text"] + " | "
                string_table.append(r_array)
                string_result += "\n"

    return string_table, string_result

def import_json(vdb_client, model, file_key, data):
    document = json.loads(data)

    document_tables = document["tables"]

    # extract common medical event data
    cme_tables = []
    for table in document_tables:
        if is_table_of_type(table, ["Common", "Medical", "Event"]):
            cme_tables.append(table)
    cme_t, cme_s = docling_tables_to_string_table(cme_tables)

    # insert into vector database
    logger.info("Creating embeding for Common Medical Event content and storing in Vector DB....")
    phrase_type = "Common Medical Event"
    data = []
    for cme_row in cme_t:
        text = ""
        for c in cme_row:
            text += c + " | "
        row = {
            "phrase_key": file_key + "_" + phrase_type + "_" + cme_row[0],
            "file": file_key,
            "phrase_type": phrase_type,
            "vector": encode_text(model, text),
            "text": text
        }
        data.append(row)
    vdb_client.insert(collection_name=VDB_COLLECTION_PHRASES, data=data)
    logger.debug(f"Inserted CMEs into collection")

    # extract common medical event data
    iq_tables = []
    for table in document_tables:
        if is_table_of_type(table, ["Important", "Questions"]):
            iq_tables.append(table)
    iq_t, iq_s = docling_tables_to_string_table(iq_tables)

    # insert into vector database
    logger.info("Creating embeding for Important Questions content and storing in Vector DB....")
    phrase_type = "Important Questions"
    data = []
    for iq_row in iq_t:
        text = ""
        for c in iq_row:
            text += c + " | "
        row = {
            "phrase_key": file_key + "_" + phrase_type + "_" + iq_row[0],
            "file": file_key,
            "phrase_type": phrase_type,
            "vector": encode_text(model, text),
            "text": text
        }
        data.append(row)
    vdb_client.insert(collection_name=VDB_COLLECTION_PHRASES, data=data)
    logger.debug(f"Inserted IQs into collection")


def import_md(vdb_client, model, file_key, data):
    # insert into vecotor database
    logger.info("Creating embeding for MD content and storing in Vector DB....")
    row = {
        "file": file_key,
        "vector": encode_text(model, data),
        "text": data
    }
    vdb_client.insert(collection_name=VDB_COLLECTION_MD, data=[row])
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
        token="root:Milvus", 
        db_name=VDB_DB_NAME
    )

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
