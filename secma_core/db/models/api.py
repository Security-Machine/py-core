"""We import all the models here so that they are available in the metadata.

If you plan to create a custom application with only some of the models
then create your own ``api.py`` file and import the routes you need from
the ``secma_core.db.models`` module, then create a ``main.py`` file that
uses this api modeled on the ``main.py`` file in th e parent directory.
"""
from . import application  # noqa F401
from . import permission  # noqa F401
from . import role  # noqa F401
from . import tenant  # noqa F401
from . import user  # noqa F401
from .base import Base  # noqa F401
