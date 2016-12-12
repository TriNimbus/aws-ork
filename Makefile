DIST ?= $(shell ls -r1 dist/aws_ork-*.whl | head -1)

.PHONY: build upload doc

build:
	tox

doc:
	pandoc --from=markdown --to=rst --output=README.rst README.md

upload:
	twine upload $(DIST)
