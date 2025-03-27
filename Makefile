PDF_FILES := $(wildcard samples/*.pdf)
OUTPUT_FILES := $(wildcard target/*)

all: ingest

install:
	pip install -r requirements.txt

lint:
	pylint src

clean:
	rm -rf target
	mkdir -p target

ingest: clean recreate_vdb convert store

convert:
	@for file in $(PDF_FILES); do \
		echo "Converting to parsable document: $$file"; \
		python src/convert.py $$file target; \
		echo; \
	done

recreate_vdb:
	python src/recreate_vector_db.py

store:
	@for file in $(OUTPUT_FILES); do \
		echo "Chunking and storing document: $$file"; \
		pwd; \
		python src/chunk_and_store.py $$file; \
		echo; \
	done

chat:
	streamlit run src/chatbot.py
