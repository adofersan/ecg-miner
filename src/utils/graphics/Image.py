# Standard library imports
from __future__ import annotations
import copy
import io
from os.path import splitext
from typing import ClassVar, Iterable, Sequence, Tuple

# Third-party imports
import cv2 as cv
import numpy as np
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError

# Application-specific imports
from utils.graphics.ColorSpace import ColorSpace
from utils.graphics.Point import Point
from utils.graphics.Rectangle import Rectangle


class Image:
    """
    Representation of an Image. It contains the image data itself, and also
    the color space in which it is stored. Could be GRAY, BGR, RGB or HSV.
    """

    def __init__(self, path: str) -> None:
        """
        Initialization of the image, by default is in BGR format.

        Args:
            path (str): Path of the image.

        Raises:
            FileNotFoundError: File does not exist.
        """
        self.__data = None
        self.__color_space = ColorSpace.BGR
        _, file_extension = splitext(path)
        pdf_except = False
        # PDF is converted to a temporary PNG
        if file_extension == ".pdf":
            try:
                buffer = io.BytesIO()
                pdf = convert_from_path(path)
                pdf[0].save(buffer, format="png")
                buffer.seek(0)
                img_arr = np.frombuffer(buffer.getvalue(), dtype=np.uint8)
                buffer.close()
                self.__data = cv.imdecode(img_arr, cv.IMREAD_COLOR)
            except PDFPageCountError:
                pdf_except = True
        else:
            self.__data = cv.imread(path)
        if self.__data is None or pdf_except:
            raise FileNotFoundError(f'File "{path}" does not exist')

    def __getitem__(
        self, index: Sequence
    ) -> Iterable[Iterable[int | Iterable[int]]]:
        """
        Get an slice of image data.

        Args:
            index (Sequence): Index of the slice to get.

        Returns:
            Iterable[Iterable[int | Iterable[int]]]: Slice of the data.
        """
        return self.__data[index]

    def __setitem__(
        self, index: Sequence, value: Iterable[Iterable[int | Iterable[int]]]
    ) -> None:
        """
        Set an slice of image data.

        Args:
            index (Sequence): Index of the slice to set.
            value (Iterable[Iterable[int | Iterable[int]]]): New value of the slice.
        """
        self.__data[index] = value

    @property
    def data(self) -> Iterable[Iterable[int | Iterable[int]]]:
        """
        Returns the image data.

        Returns:
            Iterable[Iterable[int | Iterable[int]]]: Copy of image data.
        """
        return self.__data

    @data.setter
    def data(self, data: Iterable[Iterable[int | Iterable[int]]]) -> None:
        """
        Set the image data.

        Args:
            data (Iterable[Iterable[int  |  Iterable[int]]]): New image data.
        """
        self.__data = data

    @property
    def height(self) -> int:
        """
        Get the height of the image.

        Returns:
            int: Height of the image.
        """
        return self.__data.shape[0]

    @property
    def width(self) -> int:
        """
        Get the width of the image.

        Returns:
            int: Width of the image.
        """
        return self.__data.shape[1]

    @property
    def white(self) -> int | Tuple[int, int, int]:
        """
        Get the white color depending of current image color space:
        - GRAY: 255
        - HSV: [0, 0, 255]
        - RGB: [255, 255, 255]
        - BGR: [255, 255, 255]
        Returns:
            int | Tuple[int, int, int]: White color.
        """
        if self.__color_space == ColorSpace.GRAY:
            return 255
        if self.__color_space == ColorSpace.HSV:
            return [0, 0, 255]
        return [255, 255, 255]

    @property
    def black(self) -> int | Tuple[int, int, int]:
        """
        Get the black color depending of current image color space:
        - GRAY: 0
        - HSV: [0, 0, 0]
        - RGB: [0, 0, 0]
        - BGR: [0, 0, 0]
        Returns:
            int | Tuple[int, int, int]: Black color.
        """
        if self.__color_space == ColorSpace.GRAY:
            return 0
        return [0, 0, 0]

    def copy(self) -> Image:
        """
        Get a deep copy of the image.

        Returns:
            Image: Copy of the image.
        """
        return copy.deepcopy(self)

    def save(self, path: str) -> None:
        """
        Save image in PNG.

        Args:
            path (str): Path where image will be stored.
        """
        self.to_BGR()
        cv.imwrite(path, self.__data)

    def crop(self, r: Rectangle) -> None:
        """
        Crop the image.

        Args:
            r (Rectangle): Rectangle of the image to crop.
        """
        tl = r.top_left
        br = r.bottom_right
        self.__data = self.__data[tl.y : br.y, tl.x : br.x]

    def threshold(self, thres: int, value: int) -> None:
        """
        Thresholds the image, if a pixel is smaller than the threshold, it is
        set to 0, otherwise it is set to a certain value.

        Args:
            threshold (int): Threshold to apply to the image.
            value (int): Value to set pixels greater or equal than threshold.
        """
        _, self.__data = cv.threshold(
            self.__data, thres, value, cv.THRESH_BINARY
        )
        self.to_GRAY()

    def line(
        self, p1: Point, p2: Point, color: Tuple[int, int, int], thickness: int
    ):
        """
        Creates a line in the image.

        Args:
            p1 (Point): First point of the line.
            p2 (Point): Second point of the line
            color (Tuple[int, int, int]): Color to paint the line.
            thickness (int): Thickness of the line.
        """
        cv.line(
            self.data,
            (p1.x, p1.y),
            (p2.x, p2.y),
            color,
            thickness=thickness,
        )

    def is_GRAY(self) -> bool:
        """
        Check if image is in GRAY space.

        Returns:
            bool: True if image is in GRAY space False if not.
        """
        return self.__color_space == ColorSpace.GRAY

    def is_BGR(self) -> bool:
        """
        Check if image is in BGR space.

        Returns:
            bool: True if image is in BGR space False if not.
        """
        return self.__color_space == ColorSpace.BGR

    def is_RGB(self) -> bool:
        """
        Check if image is in RGB space.

        Returns:
            bool: True if image is in RGB space False if not.
        """
        return self.__color_space == ColorSpace.RGB

    def is_HSV(self) -> bool:
        """
        Check if image is in HSV space.

        Returns:
            bool: True if image is in HSV space False if not.
        """
        return self.__color_space == ColorSpace.HSV

    def to_GRAY(self) -> None:
        """
        Converts image into GRAY color space.
        """
        if self.is_RGB():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_RGB2GRAY)
        elif self.is_BGR():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_BGR2GRAY)
        elif self.is_HSV():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_HSV2GRAY)
        self.__color_space = ColorSpace.GRAY

    def to_BGR(self) -> None:
        """
        Converts image into BGR color space.
        """
        if self.is_GRAY():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_GRAY2BGR)
        elif self.is_RGB():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_RGB2BGR)
        elif self.is_HSV():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_HSV2BGR)
        self.__color_space = ColorSpace.BGR

    def to_RGB(self) -> None:
        """
        Converts image into RGB color space.
        """
        if self.is_GRAY():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_GRAY2RGB)
        elif self.is_BGR():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_BGR2RGB)
        elif self.is_HSV():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_HSV2RGB)
        self.__color_space = ColorSpace.RGB

    def to_HSV(self) -> None:
        """
        Converts image into HSV color space.
        """
        if self.is_GRAY():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_GRAY2HSV)
        elif self.is_BGR():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_BGR2HSV)
        elif self.is_RGB():
            self.__data = cv.cvtColor(self.__data, cv.COLOR_RGB2HSV)
        self.__color_space = ColorSpace.HSV
