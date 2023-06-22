# Standard library imports
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Point:
    """
    Abstract representation of an integer Point in 2D. It is defined by a (x,y) tuple.
    """

    x: int = field()
    y: int = field()
