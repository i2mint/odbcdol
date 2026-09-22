# odbcdol.check_requirements

System requirements checking and helpful error messages for odbcdol.

This module provides functionality to check for system-level dependencies
required by pyodbc and provides clear installation instructions when they’re missing.

### Functions

| [`check_pyodbc_import`](#odbcdol.check_requirements.check_pyodbc_import)()       | Try to import pyodbc and provide helpful error messages if it fails.   |
|------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`check_system_dependencies`](#odbcdol.check_requirements.check_system_dependencies)() | Check if required system dependencies are installed.                   |

### odbcdol.check_requirements.check_pyodbc_import()

Try to import pyodbc and provide helpful error messages if it fails.

This function should be called before attempting to use pyodbc.
It will catch import errors and provide platform-specific installation
instructions.

* **Raises:**
  [**ImportError**](https://docs.python.org/3/builtins/exceptions.html#ImportError) – If pyodbc cannot be imported, with detailed instructions
* **Returns:**
  The pyodbc module if successfully imported
* **Return type:**
  module

```pycon
>>> # This will either return the pyodbc module or raise ImportError
>>> pyodbc = check_pyodbc_import()
```

### odbcdol.check_requirements.check_system_dependencies()

Check if required system dependencies are installed.

* **Raises:**
  [**ImportError**](https://docs.python.org/3/builtins/exceptions.html#ImportError) – If required system dependencies are missing, with
      detailed installation instructions
* **Returns:**
  True if all dependencies are satisfied
* **Return type:**
  [*bool*](https://docs.python.org/3/builtins/functions.html#bool)

```pycon
>>> # This will either return True or raise ImportError with instructions
>>> result = check_system_dependencies()
```
