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

    # drop all collections that happen to be in the database
    try:
        vdb_client.using_database(VDB_DB_NAME)
        logger.info("Database exists.  Purging all collections before recreating")
        for c in vdb_client.list_collections():
            logger.info(f"Dropping Collection: {c}")
            vdb_client.drop_collection(c)
    except MilvusException as e:
        logger.debug(f"Database didn't exist - unable to purge collections: {e}")

    # recreate database
    logger.info("Creating Vector DB...")
    try:
        logger.debug("Dropping Vector DB")
        vdb_client.drop_database(VDB_DB_NAME)
        logger.debug("Vector DB Dropped")
    except MilvusException as e:
        logger.debug(f"Database didn't exist - unable to drop: {e}")
    vdb_client.create_database(VDB_DB_NAME, "vectorstore")
    vdb_client.using_database(VDB_DB_NAME)
    logger.info("Vector DB Re-created")

    # create markdown collection
    logger.info("Creating core SBC collection for vectorized markdown content")
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
    logger.info("Collection created")

    # close database connection
    vdb_client.close()

    # all done
    logger.info("Recreated database!")

if __name__ == '__main__':
    cli_main()
