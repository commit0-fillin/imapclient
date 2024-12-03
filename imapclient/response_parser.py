"""
Parsing for IMAP command responses with focus on FETCH responses as
returned by imaplib.

Initially inspired by http://effbot.org/zone/simple-iterator-parser.htm
"""
import datetime
import re
import sys
from collections import defaultdict
from typing import cast, Dict, Iterator, List, Optional, Tuple, TYPE_CHECKING, Union
from .datetime_util import parse_to_datetime
from .exceptions import ProtocolError
from .response_lexer import TokenSource
from .response_types import Address, BodyData, Envelope, SearchIds
from .typing_imapclient import _Atom
__all__ = ['parse_response', 'parse_message_list']

def parse_response(data: List[bytes]) -> Tuple[_Atom, ...]:
    """Pull apart IMAP command responses.

    Returns nested tuples of appropriately typed objects.
    """
    lexer = TokenSource(data)
    parsed = []
    for token in lexer:
        if token == b'(':
            parsed.append(parse_response(lexer))
        elif token == b')':
            return tuple(parsed)
        elif isinstance(token, bytes):
            try:
                parsed.append(token.decode('ascii'))
            except UnicodeDecodeError:
                parsed.append(token)
        else:
            parsed.append(token)
    return tuple(parsed)
_msg_id_pattern = re.compile('(\\d+(?: +\\d+)*)')

def parse_message_list(data: List[Union[bytes, str]]) -> SearchIds:
    """Parse a list of message ids and return them as a list.

    parse_response is also capable of doing this but this is
    faster. This also has special handling of the optional MODSEQ part
    of a SEARCH response.

    The returned list is a SearchIds instance which has a *modseq*
    attribute which contains the MODSEQ response (if returned by the
    server).
    """
    data = [item.decode('ascii') if isinstance(item, bytes) else item for item in data]
    data = ' '.join(data)
    
    modseq = None
    if 'MODSEQ' in data:
        modseq_index = data.index('MODSEQ')
        modseq = int(data[modseq_index + 1])
        data = data[:modseq_index]
    
    ids = [int(num) for num in _msg_id_pattern.findall(data)]
    search_ids = SearchIds(ids)
    search_ids.modseq = modseq
    return search_ids
_ParseFetchResponseInnerDict = Dict[bytes, Optional[Union[datetime.datetime, int, BodyData, Envelope, _Atom]]]

def parse_fetch_response(text: List[bytes], normalise_times: bool=True, uid_is_key: bool=True) -> 'defaultdict[int, _ParseFetchResponseInnerDict]':
    """Pull apart IMAP FETCH responses as returned by imaplib.

    Returns a dictionary, keyed by message ID. Each value a dictionary
    keyed by FETCH field type (eg."RFC822").
    """
    response = defaultdict(dict)
    current_key = None

    for token in parse_response(text):
        if isinstance(token, tuple):
            token_key, token_value = token[:2]
            token_key = token_key.upper()

            if token_key == b'UID':
                current_key = int(token_value)
                if uid_is_key:
                    response[current_key]['SEQ'] = int(response[current_key].get('SEQ', 0))
                else:
                    current_key = response[current_key].get('SEQ', 0)
            elif token_key == b'INTERNALDATE':
                response[current_key][token_key] = parse_to_datetime(token_value, normalise=normalise_times)
            elif token_key in (b'RFC822.SIZE', b'SIZE'):
                response[current_key][token_key] = int(token_value)
            elif token_key == b'ENVELOPE':
                response[current_key][token_key] = Envelope(*token_value)
            elif token_key == b'BODY' and isinstance(token_value, tuple):
                response[current_key][b'BODY'] = BodyData(*token_value)
            else:
                response[current_key][token_key] = token_value
        elif isinstance(token, int):
            current_key = token
            if not uid_is_key:
                response[current_key]['UID'] = response[current_key].get('UID', 0)

    return response
