TAG=$(shell awk '/^[0-9]/ {print $$1; exit }' CHANGELOG.rst)

all: build

venv_test:
ifndef VIRTUAL_ENV
	$(error Please activate a virtualenv)
endif

install_deps:
	@pip install -U pip
	@pip install build pytest nox

build: venv_test
	@python -m build

test:
	@nox

# generate the docs
docs: venv_test build
	@pip install sphinx sphinx_rtd_theme
	@sphinx-build -j auto docs build/sphinx/html

