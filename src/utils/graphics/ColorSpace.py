# Standard library imports
from enum import Enum


class ColorSpace(Enum):
    """
    Enumeration of color spaces.
    """
    GRAY = 0
    BGR = 1
    RGB = 2
    HSV = 3