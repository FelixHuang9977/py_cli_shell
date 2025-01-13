PYTHON_VER=python3.10

#check env
#apt-get install python-dev
#sudo apt install --download-only python-dev -o Dir::Cache::archives=./

all:
	@if [ ! -d .venv ]; then echo "ENV isn't configured!!!"; make help; fi
	@if [ -d .venv ]; then echo "[CHECK] venv: ready"; echo "Usages:"; echo "  ./diag_cli"; fi

check:
	@echo
	@echo "Installed CLI command:"
	@.venv/bin/python ./cli_shell.py -c info | sed 's/^/  /g'
	@echo
	@echo "Installed test cases:"
	@.venv/bin/python ./diag_test.py list | sed 's/^/  /g'
		
help:
	-@echo "PYTHON_VER: ${PYTHON_VER}"
	-@echo
	-@echo "make setup_dev     #build development env (use this if you are the poor developer)"
	-@echo "make setup         #setup production env"
	-@echo "make check         #check env/installed commands/testcases"
	-@echo "make logclear      #clean logs"

setup_dev:
	-${PYTHON_VER} -m venv .venv
	make download_wheel
	.venv/bin/pip install -r requirements.txt --no-index --find-links wheelhouse

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt --no-index --find-links wheelhouse
	chmod +x ./diag_cli
	./diag_cli list

logclear:
	-@echo "clear logs"
	-find ./logs/ -type f -name "*.log" -exec rm -rf {} \;
	-find ./logs/ -type f -name "*.txt" -exec rm -rf {} \;

clear: logclear

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
	-@echo "clean all env, packages, logs in 3 secs.....ctrl-c to abort"
	-@sleep 3
	-rm -rf venv
	-rm -rf wheelhouse
	-find ./ -type d -name __pycache__ -exec rm -rf {} \;
	-find ./ -type d -name .pytest_cache -exec rm -rf {} \;
	make logclear