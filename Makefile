MODULE_NAME ?= secma_core
PACKAGE_NAME ?= security-machine-core
CONFIG_FILE ?= secma_core/server/default-config.yaml
ifeq ($(OS),Windows_NT)
    detected_OS := Windows
else
    detected_OS := $(shell uname)
endif
ifeq ($(OS),Windows_NT)
	RMRF = rmdir /s /q
else
	RMRF = rm -rf
endif

export SECURITY_MACHINE_CONFIG=$(CONFIG_FILE)
export SECURITY_MACHINE_MANAGEMENT__TOKEN_SECRET="123456"
export SECURITY_MACHINE_MANAGEMENT__SUPER_PASSWORD="123456"


init:
	python -m pip install --upgrade pip
	python -m pip install -e .[dev]
	python -m pip install -e .[server]


run:
	python \
		-m uvicorn $(MODULE_NAME).server.main:app \
		--reload \
		--port 8989


all: lint test


sdist:
	$(RMRF) dist || echo "dist not found, skipping"
	$(RMRF) build || echo "build not found, skipping"
	$(RMRF) $(MODULE_NAME).egg-info || echo "egg-info not found, skipping"
	python -m build
	python -m twine check dist/*


lint:
	@python -m isort --check $(MODULE_NAME)  ||  echo "isort:   FAILED!"
	@python -m black --check --line-length=79 --quiet $(MODULE_NAME) || echo "black:   FAILED!"
	@python -m flake8 $(MODULE_NAME)  || echo "flake8:  FAILED!"


delint:
	python -m isort $(MODULE_NAME)
	python -m black --line-length=79 $(MODULE_NAME)


typecheck:
	python -m mypy $(MODULE_NAME)


test: lint typecheck
	python -m pytest \
		--cov-report term \
		--cov-report html \
		--cov-config=.coveragerc \
		--cov=$(MODULE_NAME) $(MODULE_NAME)/
