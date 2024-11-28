"""Encoding utilities for PHART.

This module handles character encoding issues, particularly for Windows environments
where certain Unicode characters (like box-drawing characters) can be problematic.
"""

import os
import platform
from contextlib import contextmanager
from typing import Generator


def can_use_unicode() -> bool:
    """
    Check if the current environment supports Unicode box characters.

    Returns
    -------
    bool
        True if Unicode box characters are supported
    """
    if platform.system() == "Windows":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            return bool(kernel32.GetConsoleOutputCP() == 6500)
        except BaseException:
            return False
    return True


@contextmanager
def encoding_context() -> Generator[None, None, None]:
    """
    Context manager for handling encoding settings.

    This ensures proper encoding for Unicode characters, particularly
    on Windows systems. It temporarily sets environment variables
    for UTF-8 support and restores them afterwards.

    Examples
    --------
    >>> with encoding_context():
    ...     print(renderer.render())
    """
    old_env = {
        "PYTHONIOENCODING": os.environ.get("PYTHONIOENCODING"),
        "PYTHONLEGACYWINDOWSSTDIO": os.environ.get("PYTHONLEGACYWINDOWSSTDIO"),
    }

    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"

    try:
        yield
    finally:
        # Restore original environment
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def safe_encode(s: str, encoding: str = "utf-8") -> str:
    """
    Safely encode and decode a string, falling back to ASCII if needed.

    Parameters
    ----------
    s : str
        String to encode safely
    encoding : str, optional (default='utf-8')
        Target encoding

    Returns
    -------
    str
        Safely encoded string
    """
    try:
        return s.encode(encoding).decode(encoding)
    except UnicodeEncodeError:
        return s.encode("ascii", errors="replace").decode("ascii")
