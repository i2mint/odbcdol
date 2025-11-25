"""
System requirements checking and helpful error messages for odbcdol.

This module provides functionality to check for system-level dependencies
required by pyodbc and provides clear installation instructions when they're missing.
"""

import platform
import subprocess
import sys
from pathlib import Path


def _get_system_info():
    """Get information about the operating system.

    Returns:
        tuple: (os_type, os_name) where os_type is 'linux', 'darwin', or 'windows'
               and os_name is the detailed platform string

    >>> info = _get_system_info()
    >>> isinstance(info, tuple) and len(info) == 2
    True
    """
    system = platform.system().lower()
    platform_info = platform.platform().lower()
    return system, platform_info


def _check_homebrew_package(package_name):
    """Check if a Homebrew package is installed on macOS.

    Args:
        package_name: Name of the Homebrew package to check

    Returns:
        bool: True if package is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ['brew', 'list', package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _check_dpkg_package(package_name):
    """Check if a dpkg package is installed on Debian/Ubuntu.

    Args:
        package_name: Name of the dpkg package to check

    Returns:
        bool: True if package is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ['dpkg', '-s', package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _check_rpm_package(package_name):
    """Check if an RPM package is installed on RHEL/CentOS/Fedora.

    Args:
        package_name: Name of the RPM package to check

    Returns:
        bool: True if package is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ['rpm', '-q', package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _check_odbc_library_exists(lib_paths):
    """Check if ODBC library files exist at expected locations.

    Args:
        lib_paths: List of possible library paths to check

    Returns:
        bool: True if any library path exists, False otherwise
    """
    return any(Path(p).exists() for p in lib_paths)


def check_system_dependencies():
    """Check if required system dependencies are installed.

    Raises:
        ImportError: If required system dependencies are missing, with
                     detailed installation instructions

    Returns:
        bool: True if all dependencies are satisfied

    >>> # This will either return True or raise ImportError with instructions
    >>> result = check_system_dependencies()  # doctest: +SKIP
    """
    system, platform_info = _get_system_info()

    if system == 'darwin':  # macOS
        # Check for unixodbc via Homebrew
        lib_paths = [
            '/opt/homebrew/opt/unixodbc/lib/libodbc.2.dylib',  # Apple Silicon
            '/usr/local/opt/unixodbc/lib/libodbc.2.dylib',  # Intel Mac
        ]

        if not _check_odbc_library_exists(lib_paths) and not _check_homebrew_package(
            'unixodbc'
        ):
            raise ImportError(
                "\n" + "=" * 70 + "\n"
                "❌ MISSING SYSTEM DEPENDENCY: unixodbc\n"
                "=" * 70 + "\n\n"
                "The 'odbcdol' package requires 'unixodbc' to be installed at the system level.\n"
                "This is a library that pyodbc depends on, and it cannot be installed via pip.\n\n"
                "📦 Installation Instructions for macOS:\n"
                "   Run the following command in your terminal:\n\n"
                "   brew install unixodbc\n\n"
                "   If you don't have Homebrew installed, visit: https://brew.sh\n\n"
                "🔗 More Information:\n"
                "   • pyodbc documentation: https://github.com/mkleehammer/pyodbc/wiki\n"
                "   • unixodbc package: https://formulae.brew.sh/formula/unixodbc\n\n"
                "After installing unixodbc, you may need to restart your Python environment.\n"
                "=" * 70
            )

    elif system == 'linux':
        # Check for appropriate ODBC drivers on Linux
        is_ubuntu = 'ubuntu' in platform_info or 'debian' in platform_info
        is_rhel = any(
            x in platform_info for x in ['rhel', 'centos', 'fedora', 'red hat']
        )

        if is_ubuntu:
            # Check for unixodbc and MS ODBC driver
            has_unixodbc = _check_dpkg_package('unixodbc')
            has_ms_driver = _check_dpkg_package('msodbcsql17') or _check_dpkg_package(
                'msodbcsql18'
            )

            if not has_unixodbc or not has_ms_driver:
                missing = []
                if not has_unixodbc:
                    missing.append('unixodbc')
                if not has_ms_driver:
                    missing.append('msodbcsql17/msodbcsql18')

                raise ImportError(
                    "\n" + "=" * 70 + "\n"
                    f"❌ MISSING SYSTEM DEPENDENCIES: {', '.join(missing)}\n"
                    "=" * 70 + "\n\n"
                    "The 'odbcdol' package requires ODBC drivers to be installed at the system level.\n\n"
                    "📦 Installation Instructions for Ubuntu/Debian:\n\n"
                    "   Step 1: Install unixODBC\n"
                    "   sudo apt-get update\n"
                    "   sudo apt-get install -y unixodbc unixodbc-dev\n\n"
                    "   Step 2: Install Microsoft ODBC Driver for SQL Server\n"
                    "   # Add Microsoft repository\n"
                    "   curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -\n"
                    "   curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | \\\n"
                    "       sudo tee /etc/apt/sources.list.d/mssql-release.list\n\n"
                    "   # Install ODBC driver\n"
                    "   sudo apt-get update\n"
                    "   sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18\n\n"
                    "🔗 More Information:\n"
                    "   • Microsoft ODBC Driver docs: https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server\n"
                    "   • pyodbc documentation: https://github.com/mkleehammer/pyodbc/wiki\n"
                    "=" * 70
                )

        elif is_rhel:
            has_unixodbc = _check_rpm_package('unixODBC')
            has_ms_driver = _check_rpm_package('msodbcsql17') or _check_rpm_package(
                'msodbcsql18'
            )

            if not has_unixodbc or not has_ms_driver:
                missing = []
                if not has_unixodbc:
                    missing.append('unixODBC')
                if not has_ms_driver:
                    missing.append('msodbcsql17/msodbcsql18')

                raise ImportError(
                    "\n" + "=" * 70 + "\n"
                    f"❌ MISSING SYSTEM DEPENDENCIES: {', '.join(missing)}\n"
                    "=" * 70 + "\n\n"
                    "The 'odbcdol' package requires ODBC drivers to be installed at the system level.\n\n"
                    "📦 Installation Instructions for RHEL/CentOS/Fedora:\n\n"
                    "   Step 1: Install unixODBC\n"
                    "   sudo yum install -y unixODBC unixODBC-devel\n\n"
                    "   Step 2: Install Microsoft ODBC Driver for SQL Server\n"
                    "   # Add Microsoft repository\n"
                    "   curl https://packages.microsoft.com/config/rhel/8/prod.repo | \\\n"
                    "       sudo tee /etc/yum.repos.d/mssql-release.repo\n\n"
                    "   # Install ODBC driver\n"
                    "   sudo ACCEPT_EULA=Y yum install -y msodbcsql18\n\n"
                    "🔗 More Information:\n"
                    "   • Microsoft ODBC Driver docs: https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server\n"
                    "   • pyodbc documentation: https://github.com/mkleehammer/pyodbc/wiki\n"
                    "=" * 70
                )

    elif system == 'windows':
        # On Windows, ODBC drivers are usually pre-installed or available via Windows Update
        # We'll provide guidance if pyodbc fails to import
        pass

    return True


def check_pyodbc_import():
    """Try to import pyodbc and provide helpful error messages if it fails.

    This function should be called before attempting to use pyodbc.
    It will catch import errors and provide platform-specific installation
    instructions.

    Raises:
        ImportError: If pyodbc cannot be imported, with detailed instructions

    Returns:
        module: The pyodbc module if successfully imported

    >>> # This will either return the pyodbc module or raise ImportError
    >>> pyodbc = check_pyodbc_import()  # doctest: +SKIP
    """
    # First check system dependencies
    check_system_dependencies()

    # Then try to import pyodbc
    try:
        import pyodbc

        return pyodbc
    except ImportError as e:
        # If pyodbc itself is not installed
        if 'pyodbc' in str(e).lower():
            raise ImportError(
                "\n" + "=" * 70 + "\n"
                "❌ MISSING PYTHON PACKAGE: pyodbc\n"
                "=" * 70 + "\n\n"
                "The 'odbcdol' package requires 'pyodbc' to be installed.\n\n"
                "📦 Installation Instructions:\n"
                "   pip install pyodbc\n\n"
                "   Or install odbcdol with all dependencies:\n"
                "   pip install odbcdol\n"
                "=" * 70
            ) from e
        else:
            # Some other import error - likely system dependency issue
            # Re-check system dependencies which will provide appropriate error
            check_system_dependencies()
            # If we get here, re-raise the original error
            raise
