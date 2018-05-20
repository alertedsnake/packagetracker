TAG=$(shell head CHANGELOG.rst | grep -e '^[0-9]' | head -n 1)

all: build

venv_test:
ifndef VIRTUAL_ENV
	$(error Please activate a virtualenv)
endif

build: venv_test
	@python ./setup.py build

# generate the docs
docs: venv_test build
	@pip install sphinx sphinx_rtd_theme
	@python ./setup.py build_sphinx

