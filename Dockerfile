FROM ubuntu:latest

# For debconf. Means zero interaction while installing or upgrading
# the system via apt. It accepts the default answer for all questions.
ARG DEBIAN_FRONTEND=noninteractive

# Project-specifics.
ARG INSTALL_PATH=/srv/security-machine
ARG MODULE_NAME=secma_core

# The number of processes to use.
ENV NUM_PROCESSES=4

# The port we listen to inside the container.
ENV PORT=8989

# The IP address we listen to inside the container.
ENV HOST=0.0.0.0


# Install required distribution packages.
RUN apt-get update && \
    apt-get install -y locales && \
    locale-gen en_US.UTF-8
ENV LOCALE en_US
RUN apt-get install -y python3 python3-pip python3-venv


# Install required python packages.
RUN \
    mkdir -p $INSTALL_PATH && \
    python3 -m venv $INSTALL_PATH/venv && \
    . $INSTALL_PATH/venv/bin/activate && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade build && \
    python3 -m pip install --upgrade setuptools


# Copy the project file.
COPY ./pyproject.toml $INSTALL_PATH/
WORKDIR $INSTALL_PATH


# Install python dependencies.
RUN . $INSTALL_PATH/venv/bin/activate && \
    python3 -m pip install -e . && \
    python3 -m pip install --upgrade uvicorn[standard]


# Copy the content of the package to the docker image.
COPY ./$MODULE_NAME $INSTALL_PATH/$MODULE_NAME


# And run it.
ENV PATH=$INSTALL_PATH/venv/bin:$PATH
CMD [ \
    "uvicorn", "$MODULE_NAME.server:app", \
    "--host", "$HOST", \
    "--port", "$PORT", \
    "--proxy-headers", \
    "--workers", "$NUM_PROCESSES" \
]
