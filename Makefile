PYTHON_VER=python3.10

all: help

help:
	-@echo "PYTHON_VER: ${PYTHON_VER}"
	-@echo
	-@echo "make setup_dev     #build development env (use this if you are the poor developer)"
	-@echo "make setup         #setup production env"

setup_dev:
	-${PYTHON_VER} -m venv .venv
	make download_wheel
	.venv/bin/pip install -r requirements.txt --no-index --find-links wheelhouse

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt --no-index --find-links wheelhouse
	chmod +x ./diag_cli
	./diag_cli list

download_wheel:
	mkdir -p wheelhouse
	.venv/bin/pip  download -r requirements.txt -d wheelhouse

setup_online:
	.venv/bin/pip install -r requirements.txt
	chmod +x ./diag_cli

release:
	.venv/bin/pip  freeze > requirements.txt
	mkdir -p wheelhouse
	.venv/bin/pip  download -r requirements.txt -d wheelhouse

clean:
	-rm -rf venv
	-rm -rf wheelhouse
	-find ./ -type d -name __pycache__ -exec rm -rf {} \;
	-find ./ -type d -name .pytest_cache -exec rm -rf {} \;