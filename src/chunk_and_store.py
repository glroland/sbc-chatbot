import logging
import click
import json
import os
from pprint import pprint

logger = logging.getLogger(__name__)

# Setup Logging
logging.basicConfig(level=logging.DEBUG,
    handlers=[
        # no need from cli - logging.FileHandler("chunk_and_store.log"),
        logging.StreamHandler()
    ])

@click.command()
@click.argument('input_file')
def cli_main(input_file):
    """ CLI Utility that loads a docling document in json format and stores as
        chunks document in a vector database.
        
        input_file - docling document in json format
    """
    logger.info(f"Processing Input File: {input_file}")

    # load yaml file
    input_file_abs = os.path.abspath(input_file)
    logger.info(f"Input File: {input_file_abs}")
    with open(input_file, 'rb') as f:
        document = json.load(f)

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

if __name__ == '__main__':
    cli_main(None)
