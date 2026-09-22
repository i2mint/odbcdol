# odbcdol

odbc (through pyodbc) with a simple (dict-like or list-like) interface

### Classes

| [`SQLServerPersister`](#odbcdol.SQLServerPersister)([conn_protocol, host, ...])   |    |
|---------------------------------------------------------------------------------------------------|----|

### *class* odbcdol.SQLServerPersister(conn_protocol='tcp', host='localhost', port='1433', db_username='SA', db_pass='Admin123x', db_name='py2store', table_name='person', primary_key='id', data_fields=('name',))

Bases: [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

### Modules

| [`check_requirements`](odbcdol.check_requirements.md#module-odbcdol.check_requirements)   | System requirements checking and helpful error messages for odbcdol.   |
|---------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
