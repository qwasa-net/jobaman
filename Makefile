# base dirs
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
HOME_DIR := $(dir $(MAKEFILE_PATH))

# python stuff
VENV = $(HOME_DIR)/.venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# project code
SRC_DIRS = "$(HOME_DIR)/jobaman" "$(HOME_DIR)/tests"

#
.DEFAULT: tea
tea: venv install install-dev format lint unittests

#
venv:
	[ -d $(VENV) ] || python3 -m venv $(VENV)
	$(PYTHON) --version

install:
	$(PIP) install --upgrade pip wheel setuptools
	$(PIP) install -r "$(HOME_DIR)/requirements.txt"

install-dev:
	-$(PIP) install -r "$(HOME_DIR)/requirements-dev.txt"

clean:
	for dir in $(SRC_DIRS); do \
		find $$dir -type f -regextype posix-extended -iregex '.*\.py[cod]$$' -print -delete; \
		find $$dir -type d -iname "__pycache__" -print -delete; \
	done

clean-venv:
	[ -d $(VENV) ] && rm -rfv "$(VENV)"

#
format:
	$(PYTHON) -m black $(SRC_DIRS)
	$(PYTHON) -m isort $(SRC_DIRS)

lint:
	$(PYTHON) -m ruff check $(SRC_DIRS)

#
unittests:
	$(PYTHON) -m unittest discover -s tests


#
run-api:
	$(PYTHON) -m jobaman.main --ini-path jobaman.ini --debug

