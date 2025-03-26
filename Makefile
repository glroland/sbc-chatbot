FILES := $(wildcard samples/*.pdf)

install:
	pip install -r requirements.txt

clean:
	rm -rf target
	mkdir -p target

ingest: clean convert

convert:
	@for file in $(FILES); do \
		echo "Processing $$file"; \
		docling --from pdf --to json --to md --output target --image-export-mode placeholder $$file; \
		echo; \
	done
