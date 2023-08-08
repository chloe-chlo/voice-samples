all: create_tagged_resources

run_script:
	python scripts/create-tagged-resources.py --raw-files-directory=raw --output-directory=tagged