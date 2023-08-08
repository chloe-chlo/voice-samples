all: create_tagged_resources

create_tagged_resources:
	python scripts/create-tagged-resources.py --raw-files-directory=raw --output-directory=tagged