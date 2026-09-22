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


_IDENTIFIER_RE = re.compile(r"[A-Za-z_@#][A-Za-z0-9_@#$]{0,127}")


def _quote_identifier(name: str) -> str:
    """Validate a table/column name and return it bracket-quoted for SQL Server.

    Identifiers cannot be passed as query parameters, so anything that is not a
    plain (regular) SQL Server identifier is refused rather than escaped.
    """
    if not isinstance(name, str) or not _IDENTIFIER_RE.fullmatch(name):
        raise ValueError(f"Not a valid SQL identifier: {name!r}")
    return f"[{name}]"


def _connection_string(**parts) -> str:
    """Build an ODBC connection string, brace-quoting values that need it.

    A value containing ``;``, ``{``, ``}``, ``=`` or surrounding spaces would
    otherwise end its attribute and start another (e.g. a password
    ``x;DATABASE=other``). Values already wrapped in braces are kept as is.
    """

    def _value(v) -> str:
        v = str(v)
        if v.startswith("{") and v.endswith("}"):
            return v
        if any(c in v for c in ";{}=") or v != v.strip():
            return "{" + v.replace("}", "}}") + "}"
        return v

    return ";".join(f"{k}={_value(v)}" for k, v in parts.items())


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
                DRIVER="{ODBC Driver 17 for SQL Server}",
                SERVER=f"{conn_protocol}:{host},{port}",
                DATABASE=db_name,
                UID=db_username,
                PWD=db_pass,
            )
        )

        self._cursor = self._sql_server_client.cursor()
        self._table_name = table_name
        self._primary_key = primary_key

        # Identifiers cannot be bound as parameters, so they are validated and
        # bracket-quoted; every VALUE is bound (``?``) and never formatted in.
        table = _quote_identifier(self._table_name)
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
        self._cursor.execute(self._select_query, k)
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
                *(v[c] for c in columns),
            )
        except pyodbc.IntegrityError as e:
            # TODO: Raise a proper exception here
            print("ERROR: Cannot insert a duplicate entry")

        self._sql_server_client.commit()

    def __delitem__(self, k):
        self._cursor.execute(self._del_query, k)
        self._sql_server_client.commit()

    def __iter__(self):
        self._cursor.execute(self._select_all_query)
        records = self._cursor.fetchall()

        yield from records

    def __len__(self):
        self._cursor.execute(self._select_all_query)
        records = self._cursor.fetchall()
        return len(records)
