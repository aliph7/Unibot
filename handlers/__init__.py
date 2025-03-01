"""
این فایل برای مدیریت import ها در پکیج handlers استفاده می‌شود
"""

from . import start
from . import pamphlets
from . import books
from . import videos

__all__ = [
    'start',
    'pamphlets',
    'books',
    'videos',
]

