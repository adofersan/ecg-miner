# Standard library imports
from dataclasses import dataclass
from dataclasses import field

# Application-specific imports
from utils.graphics.Point import Point


@dataclass(frozen=True)
class Rectangle:
    """
    Abstract representation of a rectangle in 2D. It is defined with two integer points;
    the one on the top left corner, and the other in the bottom right corner.
    """

    top_left: Point = field()
    bottom_right: Point = field()

    @property
    def height(self) -> int:
        """
        Get the height of the rectangle.

        Returns:
            int: Height of the rectangle.
        """
        return self.bottom_right.y - self.top_left.y

    @property
    def width(self) -> int:
        """
        Get the width of the rectangle.

        Returns:
            int: Width of the rectangle.
        """
        return self.bottom_right.x - self.top_left.x
