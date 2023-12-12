# security-machine-core

The core of the security machine is intended to be used as a server that
receives requests from the client and executes the commands on the machine
where it is running. It connects to a postgres database to store and retrieve
the information.

## Installation

Follow the content of the [Dockerfile](./Dockerfile) to install this project
and run it in production.

## Database

The database uses some environment variables that are not available in the
configuration file:

- `SECURITY_MACHINE_TABLE_PREFIX`: (default is `secma_`) a string to prefix
  the table names with;
- `SECURITY_MACHINE_DB_SCHEMA`: (default is `public`) the schema where the
  tables are created;

## Usage

The virtual machine is intended to be used as a server that sits behind
a reverse proxy. The endpoints exposed by it are documented at
[the /docs route](http://localhost:8989/docs).

### Web App Configuration

The project can be configured using a configuration file and environment
variables. The configuration file is a YAML file that needs to be passed to the
application using the `SECURITY_MACHINE_CONFIG` environment variable.

To discover the configuration options, you can take a look at the
[settings module](./secma_core/server/settings.py). Note that
environment variables have precedence over the configuration file.
For each option the environment variable will have the same name prefixed
by `SECURITY_MACHINE_`. Environment variables are case insensitive.

The values extracted from environment variables are converted to the
correct type. for complex types, like lists, the value should be provided
as a JSON string.

You can also place a `.env` file in the root of the project to set the
environment variables (no other variations like `.env.local` are used).
This file is ignored by git; environment variables take precedence over
the values in this file; the values in this file take precedence over
the values in the configuration file.

The application supports docker secrets. To use it you may want to set the
`SECURITY_MACHINE_SECRETS_LOCATION` environment variable to the location
of the secrets (defaults to `/run/secrets`, same as docker),
then create your secret via the Docker CLI:

```bash
printf "This is a secret" | docker secret create my_secret_data -
```

Then you can use the secret when running docker:

```bash
docker service create --name secma-core --secret my_secret_data secma-core:latest
```

or when running docker-compose:

```yaml
version: "3.7"
services:
  secma-core:
    image: secma-core:latest
    secrets:
      - my_secret_data
secrets:
    my_secret_data:
        external: true
```

For more information about the setting loading order, you can take a look
at the [pydantic_settings](https://docs.pydantic.dev/2.5/concepts/pydantic_settings/)
module documentation that is used to load the settings.

## Development

Start by creating a virtual environment and installing the dependencies.
If you have a `make` command available, you can run `make init` after
the virtual environment is create and activated. Otherwise, you can run
the following commands:

```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m pip install -e .[server]
```

On Windows, to be able to serve the documentation, you may also need to
install the `cairo2` package:

```bash
pip install pipwin
pipwin install cairocffi
```

To run the server you have to launch the `secma_core.server.main` script.
You have a few ways of doing that:

- with reload

    ```bash
    # The server will reload when you modify the source files.
    make run
    ```

- using VsCode (a run configuration is available) to debug the server;
- using the Docker file to run the server in a container.

    ```bash
    # Build the image
    docker build -t secma-core .

    # Run the container
    docker run -it --rm -p 127.0.0.1:8080:8989 secma-core
    ```
