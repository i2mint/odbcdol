"""Values reach SQL Server as bound parameters, never as SQL text.

Runs without a database: a stand-in ``pyodbc`` records what would be sent.
"""

import sys
import types

import pytest


class _Cursor:
    def __init__(self, log):
        self.log = log

    def execute(self, sql, params=()):
        self.log.append((sql, tuple(params)))

    def fetchone(self):
        return ("row",)

    def fetchall(self):
        return []


class _Conn:
    def __init__(self, conn_str, log):
        self.conn_str = conn_str
        self.log = log

    def cursor(self):
        return _Cursor(self.log)

    def commit(self):
        pass


@pytest.fixture
def persister_cls(monkeypatch):
    log = []
    fake = types.SimpleNamespace(
        connect=lambda s: _Conn(s, log), IntegrityError=type("IE", (Exception,), {})
    )
    monkeypatch.setitem(sys.modules, "pyodbc", fake)
    import odbcdol

    monkeypatch.setattr(odbcdol, "pyodbc", fake)
    monkeypatch.setattr(
        odbcdol.SQLServerPersister,
        "_SQLServerPersister__check_dependencies",
        staticmethod(lambda: None),
    )
    return odbcdol.SQLServerPersister, log


HOSTILE = ["1 OR 1=1", "x'; DROP TABLE person; --", "1; DELETE FROM person"]


@pytest.mark.parametrize("key", HOSTILE)
def test_keys_are_bound_on_read_and_delete(persister_cls, key):
    cls, log = persister_cls
    s = cls()
    s[key]
    del s[key]
    for sql, params in log:
        assert key not in sql
        assert params == (key,)
    assert log[0][0] == "SELECT * FROM [person] WHERE [id] = ?;"
    assert log[1][0] == "DELETE FROM [person] WHERE [id] = ?;"


@pytest.mark.parametrize("value", HOSTILE)
def test_values_are_bound_on_write(persister_cls, value):
    cls, log = persister_cls
    s = cls()
    s["3"] = {"id": "3", "name": value}
    sql, params = log[-1]
    assert sql == "INSERT INTO [person]([id],[name]) VALUES (?,?);"
    assert params == ("3", value)


@pytest.mark.parametrize(
    "column, quoted",
    [
        ("name) VALUES (1); --", "[name) VALUES (1); --]"),
        ("x]; DROP TABLE t; --", "[x]]; DROP TABLE t; --]"),
        ("first name", "[first name]"),
        ("[first name]", "[first name]"),
    ],
)
def test_column_names_are_always_one_identifier(persister_cls, column, quoted):
    cls, log = persister_cls
    cls()["3"] = {column: "v"}
    sql, params = log[-1]
    assert sql == f"INSERT INTO [person]({quoted}) VALUES (?);"
    assert params == ("v",)


@pytest.mark.parametrize("column", ["", "a\x00b", "x" * 129, 3])
def test_invalid_column_names_are_refused(persister_cls, column):
    cls, _ = persister_cls
    with pytest.raises(ValueError):
        cls()["3"] = {column: "v"}


@pytest.mark.parametrize(
    "table, quoted",
    [
        ("person", "[person]"),
        ("dbo.person", "[dbo].[person]"),
        ("[dbo].[person]", "[dbo].[person]"),
        ("person]; DROP TABLE x; --", "[person]]; DROP TABLE x; --]"),
    ],
)
def test_table_names_quote_part_by_part(persister_cls, table, quoted):
    cls, log = persister_cls
    s = cls(table_name=table)
    s["k"]
    assert log[-1][0] == f"SELECT * FROM {quoted} WHERE [id] = ?;"


@pytest.mark.parametrize("key", [(1, 2), [1], {"a": 1}])
def test_container_keys_bind_as_one_value(persister_cls, key):
    cls, log = persister_cls
    cls()[key]
    assert log[-1][1] == (str(key),)


@pytest.mark.parametrize(
    "password, quoted",
    [
        ("pw;DATABASE=master", "PWD={pw;DATABASE=master}"),
        ("{x};Encrypt=no;APP={y}", "PWD={{x}};Encrypt=no;APP={y}}}"),
        ("{literalbraces}", "PWD={{literalbraces}}}"),
    ],
)
def test_connection_string_values_cannot_add_attributes(
    persister_cls, password, quoted
):
    cls, _ = persister_cls
    s = cls(db_pass=password, db_name="db")
    conn_str = s._sql_server_client.conn_str
    assert conn_str.endswith(quoted)
    assert "DATABASE={db};" in conn_str
    assert conn_str.startswith("DRIVER={ODBC Driver 17 for SQL Server};")
    assert conn_str.count("Encrypt=no") <= 1 and ";Encrypt=no;" not in conn_str.replace(
        quoted, ""
    )
