import binascii
import base64
from typing import List, Union

def encode(s: Union[str, bytes]) -> bytes:
    """Encode a folder name using IMAP modified UTF-7 encoding.

    Input is unicode; output is bytes (Python 3) or str (Python 2). If
    non-unicode input is provided, the input is returned unchanged.
    """
    if isinstance(s, bytes):
        return s
    if not isinstance(s, str):
        raise ValueError("Input must be str or bytes")
    
    result = bytearray()
    utf7_buffer = bytearray()
    
    for char in s:
        if ord(char) in range(0x20, 0x7f) and char != '&':
            if utf7_buffer:
                result.extend(b'&' + base64.b64encode(utf7_buffer).rstrip(b'=').replace(b'/', b',') + b'-')
                utf7_buffer = bytearray()
            result.extend(char.encode('ascii'))
        else:
            if char == '&':
                result.extend(b'&-')
            else:
                utf7_buffer.extend(char.encode('utf-16be'))
    
    if utf7_buffer:
        result.extend(b'&' + base64.b64encode(utf7_buffer).rstrip(b'=').replace(b'/', b',') + b'-')
    
    return bytes(result)
AMPERSAND_ORD = ord('&')
DASH_ORD = ord('-')

def decode(s: Union[bytes, str]) -> str:
    """Decode a folder name from IMAP modified UTF-7 encoding to unicode.

    Input is bytes (Python 3) or str (Python 2); output is always
    unicode. If non-bytes/str input is provided, the input is returned
    unchanged.
    """
    if isinstance(s, str):
        s = s.encode('ascii')
    if not isinstance(s, bytes):
        raise ValueError("Input must be bytes or str")
    
    result = []
    utf7_buffer = bytearray()
    in_utf7 = False
    
    for byte in s:
        if in_utf7:
            if byte == DASH_ORD:
                if utf7_buffer:
                    utf7_bytes = base64.b64decode(utf7_buffer.replace(b',', b'/') + b'===')
                    result.append(utf7_bytes.decode('utf-16be'))
                else:
                    result.append('&')
                in_utf7 = False
                utf7_buffer = bytearray()
            else:
                utf7_buffer.append(byte)
        elif byte == AMPERSAND_ORD:
            in_utf7 = True
        else:
            result.append(chr(byte))
    
    if in_utf7:
        raise ValueError("Invalid IMAP UTF-7 encoding: unexpected end of input")
    
    return ''.join(result)
