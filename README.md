
# odbcdol
odbc (through pyodbc) with a simple (dict-like or list-like) interface

## System Requirements

**Important:** Before installing `odbcdol`, you need to install system-level ODBC drivers that cannot be installed via pip.

### macOS
```bash
brew install unixodbc
```

### Ubuntu/Debian
```bash
# Install unixODBC
sudo apt-get update
sudo apt-get install -y unixodbc unixodbc-dev

# Install Microsoft ODBC Driver for SQL Server
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | \
    sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### RHEL/CentOS/Fedora
```bash
# Install unixODBC
sudo yum install -y unixODBC unixODBC-devel

# Install Microsoft ODBC Driver for SQL Server
curl https://packages.microsoft.com/config/rhel/8/prod.repo | \
    sudo tee /etc/yum.repos.d/mssql-release.repo
sudo ACCEPT_EULA=Y yum install -y msodbcsql18
```

### Windows
ODBC drivers are typically pre-installed on Windows. If you encounter issues, you may need to install the [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

## Installation

After installing the system requirements above:

```bash
pip install odbcdol
```

If you encounter import errors, the package will provide detailed instructions about which system dependencies are missing.

## Usage

```python
from odbcdol import SQLServerPersister

sql_server_persister = SQLServerPersister()

print("Fetching a Record")
print(sql_server_persister[1])
print(sql_server_persister[3])
print("=========================")

print("Adding a Record")
sql_server_persister[3] = {"id": "3", "name": "new name"}
sql_server_persister[4] = {"id": "4", "name": "Hamid NEW"}
sql_server_persister[5] = {"id": "5", "name": "Hamid NEW AGAIN"}

print(sql_server_persister[3])
print(sql_server_persister[4])
print(sql_server_persister[5])
print("======================")

print("Deleting a Record")
del sql_server_persister[3]
del sql_server_persister[4]
del sql_server_persister[5]
print(sql_server_persister[3])
print("=====================")

print("Iterating over the records")
for record in sql_server_persister:
    print(record)
print("=========================")

print("Getting the length")
print(len(sql_server_persister))
```
