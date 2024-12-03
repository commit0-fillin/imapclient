import argparse
import configparser
import json
import os
import ssl
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple, TYPE_CHECKING, TypeVar
import imapclient

def parse_config_file(filename: str) -> argparse.Namespace:
    """Parse INI files containing IMAP connection details.

    Used by livetest.py and interact.py
    """
    config = configparser.ConfigParser()
    config.read(filename)

    ns = argparse.Namespace()
    
    if 'main' in config:
        main = config['main']
        ns.host = main.get('host', fallback=None)
        ns.port = main.getint('port', fallback=None)
        ns.ssl = main.getboolean('ssl', fallback=True)
        ns.username = main.get('username', fallback=None)
        ns.password = main.get('password', fallback=None)
        ns.oauth2 = main.getboolean('oauth2', fallback=False)
        ns.oauth2_client_id = main.get('oauth2_client_id', fallback=None)
        ns.oauth2_client_secret = main.get('oauth2_client_secret', fallback=None)
        ns.oauth2_refresh_token = main.get('oauth2_refresh_token', fallback=None)
        ns.ssl_check_hostname = main.getboolean('ssl_check_hostname', fallback=True)

    return ns
T = TypeVar('T')
OAUTH2_REFRESH_URLS = {'imap.gmail.com': 'https://accounts.google.com/o/oauth2/token', 'imap.mail.yahoo.com': 'https://api.login.yahoo.com/oauth2/get_token'}
_oauth2_cache: Dict[Tuple[str, str, str, str], str] = {}
