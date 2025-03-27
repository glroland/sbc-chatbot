PDF_FILES := $(wildcard samples/*.pdf)
JSON_FILES := $(wildcard target/*.json)

all: ingest

install:
	pip install -r requirements.txt

clean:
	rm -rf target
	mkdir -p target


ingest: clean convert store

convert:
	@for file in $(PDF_FILES); do \
		echo "Converting to parsable document: $$file"; \
		python src/convert.py $$file target; \
		echo; \
	done

store:
	@for file in $(JSON_FILES); do \
		echo "Chunking and storing document: $$file"; \
		pwd; \
		python src/chunk_and_store.py $$file; \
		echo; \
	done
