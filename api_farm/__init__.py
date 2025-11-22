"""
API Farm - Shared API Key Pool Server and Client

This package provides both a client SDK and server for managing and using
a shared pool of API keys.

For CLI usage:
    api-farm --help              # Client commands
    api-farm-server --help       # Server commands

For SDK usage:
    from api_farm import APIPoolClient
    
    # Set environment variable first
    import os
    os.environ['API_FARM_SERVER_URL'] = 'http://localhost:8081'
    
    client = APIPoolClient()
    # or explicitly:
    client = APIPoolClient(server_url='http://localhost:8081')
"""

__version__ = "0.1.0"

from api_farm.client_sdk import APIPoolClient

__all__ = ["APIPoolClient", "__version__"]
