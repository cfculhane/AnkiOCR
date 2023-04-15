# Based off https://github.com/aresponses/aresponses/blob/master/Makefile

SHELL := /bin/bash
python_version = 3.9.16
venv_name = ankiocr

# See https://www.gnu.org/software/make/manual/make.html#index-_002eEXPORT_005fALL_005fVARIABLES
.EXPORT_ALL_VARIABLES:
DOCKER_BUILDKIT = 1
PYENV_ROOT = $(HOME)/.pyenv
PATH := $(HOME)/.local/bin:$(PYENV_ROOT)/bin:$(PATH)
NVM_DIR = $(HOME)/.nvm

install: setup_env install_packages  ## Create the virtual env, and install the affinda PRODUCTION requirements using poetry
	@echo "Install successful! ✨ 🍰 ✨"

install_packages: ## Installs all python packages needed for running the affinda project
	@eval "$(pyenv init -)" && eval "$(pyenv virtualenv-init -)" && source activate $(venv_name) && PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring poetry install --sync
	@eval "$(pyenv init -)" && eval "$(pyenv virtualenv-init -)" && source activate $(venv_name) && poetry run pre-commit install

setup_env:
	@pyenv install $(python_version) --skip-existing
	@pyenv virtualenv $(python_version) $(venv_name) || true
	@pyenv local $(venv_name) # To ensure poetry uses the correct version when using the venv
	@echo -e "\033[0;32m ✔️  Virtualenv setup  \033[0m"

test:  ## Run the tests.
	@pytest
	@echo -e "The tests pass! ✨ 🍰 ✨"

format:  ## Format code using black
	@"$$(poetry env info -p)"/bin/python -m black .

lint:  ## Run the code linter.
	@"$$(poetry env info -p)"/bin/python -m ruff .
	@echo -e "No linting errors - well done! ✨ 🍰 ✨"

mypy:  ## Runs type checking with mypy.
	@"$$(poetry env info -p)"/bin/python -m mypy && \
		echo -e "No typing errors - well done! ✨ 🍰 ✨"

help: ## Show this help message.
	@## https://gist.github.com/prwhite/8168133#gistcomment-1716694
	@echo -e "$$(grep -hE '^\S+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*##\s*/:/' -e 's/^\(.\+\):\(.*\)/\\x1b[36m\1\\x1b[m:\2/' | column -c2 -t -s :)" | sort
