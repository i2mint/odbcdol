"""
odbc (through pyodbc) with a simple (dict-like or list-like) interface
"""

import platform
import re
import subprocess
from collections.abc import MutableMapping

# Check system requirements and import pyodbc with helpful error messages
from odbcdol.check_requirements import check_pyodbc_import

pyodbc = check_pyodbc_import()


_MAX_IDENTIFIER_LEN = 128


def _quote_identifier(name: str) -> str:
    """Return *name* as a bracket-quoted SQL Server identifier.

    Identifiers cannot be passed as query parameters, so they are delimited:
    ``]`` is doubled, which makes any character sequence a single identifier.
    A name the caller already bracketed (``[first name]``) is unwrapped first.
    Empty names, names over 128 characters and control characters are refused.
    """
    if not isinstance(name, str):
        raise ValueError(f"Not a valid SQL identifier: {name!r}")
    if len(name) > 2 and name.startswith("[") and name.endswith("]"):
        name = name[1:-1].replace("]]", "]")
    if (
        not name
        or len(name) > _MAX_IDENTIFIER_LEN
        or any(ord(c) < 0x20 or ord(c) == 0x7F for c in name)
    ):
        raise ValueError(f"Not a valid SQL identifier: {name!r}")
    return "[" + name.replace("]", "]]") + "]"


def _quote_table_name(name: str) -> str:
    """Quote a possibly schema-qualified table name (``dbo.person``), part by part."""
    if not isinstance(name, str):
        raise ValueError(f"Not a valid SQL table name: {name!r}")
    parts = name.split(".")
    if not 1 <= len(parts) <= 4:
        raise ValueError(f"Not a valid SQL table name: {name!r}")
    return ".".join(_quote_identifier(p) for p in parts)


_SCALAR_TYPES = (str, int, float, bool, bytes, bytearray, type(None))


def _bindable(value):
    """A value pyodbc can bind as one parameter.

    Scalars (and dates, decimals...) pass through; containers are stored as
    their ``str()``, as before. (A lone list/tuple would otherwise be read by
    pyodbc as the whole parameter list.)
    """
    if isinstance(value, (list, tuple, dict, set, frozenset)):
        return str(value)
    return value


def _connection_string(**parts) -> str:
    """Build an ODBC connection string with every value brace-quoted.

    Braced values may contain ``;`` and ``=`` (``}`` is doubled), so no value
    -- a password such as ``x};Encrypt=no;APP={y`` included -- can end its
    attribute and start another.
    """
    return ";".join(f"{k}={{{str(v).replace('}', '}}')}}}" for k, v in parts.items())


class SQLServerPersister(MutableMapping):
    def __init__(
        self,
        conn_protocol="tcp",
        host="localhost",
        port="1433",
        db_username="SA",
        db_pass="Admin123x",
        db_name="py2store",
        table_name="person",
        primary_key="id",
        data_fields=("name",),
    ):

        self.__check_dependencies()
        self._sql_server_client = pyodbc.connect(
            _connection_string(
                DRIVER="ODBC Driver 17 for SQL Server",
                SERVER=f"{conn_protocol}:{host},{port}",
                DATABASE=db_name,
                UID=db_username,
                PWD=db_pass,
            )
        )

        self._cursor = self._sql_server_client.cursor()
        self._table_name = table_name
        self._primary_key = primary_key

        # Identifiers cannot be bound as parameters, so they are bracket-quoted
        # (which also keeps braces out of the templates below: the insert
        # template is .format-ted later); every VALUE is bound (``?``).
        table = _quote_table_name(self._table_name)
        pk = _quote_identifier(self._primary_key)
        self._select_all_query = f"SELECT * FROM {table};"
        self._insert_query = f"INSERT INTO {table}({{attributes}}) VALUES ({{values}});"
        self._select_query = f"SELECT * FROM {table} WHERE {pk} = ?;"
        self._del_query = f"DELETE FROM {table} WHERE {pk} = ?;"

    @staticmethod
    def __check_dependencies():
        """Check for required dependencies: pyodbc and (on Ubuntu) msodbcsql17 driver.
        Raises informative errors if missing.
        """
        try:
            import pyodbc  # noqa: F401
        except ImportError:
            raise ModuleNotFoundError(
                "'SQLServerPersister' depends on the module 'pyodbc' which is not installed. "
                "Try installing dependency using 'pip install pyodbc'."
            )

        if "ubuntu" in platform.platform().lower():
            result = subprocess.Popen(
                ["dpkg", "-s", "msodbcsql17"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            out, err = result.communicate()
            if not out:
                raise ModuleNotFoundError(
                    "ODBC Driver for SQL Server is missing. Please refer "
                    "https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-"
                    "microsoft-odbc-driver-for-sql-server?view=sql-server-2017"
                )

    def __getitem__(self, k):
        self._cursor.execute(self._select_query, (_bindable(k),))
        record = self._cursor.fetchone()
        return record if record else print(f"No record found for primary_key: {k}")
        # TODO: Raise a proper exception here

    def __setitem__(self, k, v):
        columns = list(v.keys())
        try:
            self._cursor.execute(
                self._insert_query.format(
                    attributes=",".join(_quote_identifier(c) for c in columns),
                    values=",".join("?" for _ in columns),
                ),
                tuple(_bindable(v[c]) for c in columns),
            )
        except pyodbc.IntegrityError as e:
            # TODO: Raise a proper exception here
            print("ERROR: Cannot insert a duplicate entry")

        self._sql_server_client.commit()

    def __delitem__(self, k):
        self._cursor.execute(self._del_query, (_bindable(k),))
        self._sql_server_client.commit()

    def __iter__(self):
        self._cursor.execute(self._select_all_query)
        records = self._cursor.fetchall()

        yield from records

    def __len__(self):
        self._cursor.execute(self._select_all_query)
        records = self._cursor.fetchall()
        return len(records)
