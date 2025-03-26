import logging
import click
from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)

# Setup Logging
logging.basicConfig(level=logging.DEBUG,
    handlers=[
        # no need from cli - logging.FileHandler("ingest_app.log"),
        logging.StreamHandler()
    ])

@click.command()
@click.argument('input_file')
#@click.option('--save', 'db_conn_str', default=None, nargs=1,
#              help='whether or not to truncate game tables before import')
#@click.option('--truncate', default=False, is_flag=True,
#              help='whether or not to truncate game tables before import')
def cli_main(input_file):
 
    converter = DocumentConverter()
    result = converter.convert(input_file)
    print(result.document.export_to_markdown())  # output: "## Docling Technical Report[...]"



if __name__ == '__main__':
    cli_main(None, None, None, None, None)
