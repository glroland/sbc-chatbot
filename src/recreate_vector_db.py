import logging
import click
from pymilvus import MilvusClient, MilvusException, DataType

logger = logging.getLogger(__name__)

VDB_DB_NAME = "sbcchatbot"
VDB_COLLECTION_MD = "sbc"
DIMENSIONS = 768
TTL = 86400*7

# Setup Logging
logging.basicConfig(level=logging.DEBUG,
    handlers=[
        # no need from cli - logging.FileHandler("chunk_and_store.log"),
        logging.StreamHandler()
    ])

@click.command()
def cli_main():
    """ CLI that recreates the vector database
    """
    logger.info("Recreating Vector Database...")

    # connect to vector store
    logger.info("Connecting to Vector Database Service...")
    vdb_client = MilvusClient(
        uri="http://db:19530",
        token="root:Milvus"
    )

    # recreate database
    logger.info("Creating Vector DB...")
    try:
        logger.debug("Dropping Vector DB")
        vdb_client.drop_database(VDB_DB_NAME)
        logger.debug("Vector DB Dropped")
    except MilvusException as e:
        logger.debug(f"Database didn't exist - unable to drop: {e}")
    vdb_client.create_database(VDB_DB_NAME, "vectorstore")
    logger.info("Vector DB Re-created")

    # create markdown collection
    logger.info("Creating core SBC collection for vectorized markdown content")
    md_schema = vdb_client.create_schema(auto_id=False, enable_dynamic_field=True)
    md_schema.add_field(field_name="file", datatype=DataType.VARCHAR, max_length=200, is_primary=True)
    md_schema.add_field(field_name="sbc", datatype=DataType.FLOAT_VECTOR, dim=DIMENSIONS)
    vdb_client.create_collection(collection_name=VDB_COLLECTION_MD,
                                 schema=md_schema,
                                 properties={
        "collection.ttl.seconds": TTL
    })
    logger.info("Collection created")

    # close database connection
    vdb_client.close()

    # all done
    logger.info("Recreated database!")

if __name__ == '__main__':
    cli_main()
