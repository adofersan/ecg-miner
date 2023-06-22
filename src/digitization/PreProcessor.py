# Standard library imports
from typing import Tuple

# Third-party imports
import cv2 as cv
import numpy as np

# Application-specific imports
from utils.graphics.Image import Image
from utils.graphics.Point import Point
from utils.graphics.Rectangle import Rectangle


class Preprocessor:
    """
    Preprocessor to clean and binarize an ECG image.
    """

    def __init__(self):
        """
        Initialization of the preprocessor.
        """
        pass

    def preprocess(self, ecg: Image) -> Tuple[Image, Rectangle]:
        """
        Preprocess and ECG image.

        Args:
            ecg (Image): ECG image.

        Returns:
            Tuple[Image, Rectangle]: A cropped image of the ECG signals binarized
                and the rectangle of the area cropped with respect to the original image.
        """
        ecg = ecg.copy()
        rect = self.__img_partitioning(ecg)
        ecg.crop(rect)
        ecg = self.__gridline_removal(ecg)
        return (ecg, rect)

    def __img_partitioning(self, ecg: Image) -> Rectangle:
        """
        Get the rectangle which contains the grid with the ECG signals.

        Args:
            ecg (Image): ECG image.

        Returns:
            Rectangle: Rectangle with the ECG signals.
        """
        ### splitting b,g,r channels
        ecg = ecg.copy()
        ecg.to_BGR()
        # Find edges with Canny operator
        edges = cv.Canny(ecg.data, 50, 200)
        # Suzuki's contour tracing algorithm
        contours, _ = cv.findContours(
            edges.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE
        )
        # Bound rectangles
        polygons = [
            cv.approxPolyDP(c, 0.01 * cv.arcLength(c, True), True)
            for c in contours
        ]
        rects = [cv.boundingRect(p) for p in polygons]

        # Get largest contour
        sorted_rects = sorted(rects, key=lambda x: x[2] * x[3], reverse=True)
        largest_rect = sorted_rects[0]
        x, y, w, h = largest_rect
        rect = Rectangle(Point(x, y), Point(x + w, y + h))
        return rect

    def __gridline_removal(self, ecg: Image) -> Image:
        """
        Removes the gridline of an ECG image.
        
        Args:
            ecg (Image): ECG image.

        Returns:
            Image: Image binarized.
        """
        gray_image = ecg.data
        gray_image = cv.cvtColor(gray_image, cv.COLOR_BGR2HSV)
        lower = np.array([0, 0, 168])
        upper = np.array([255, 255, 255])
        mask = cv.inRange(gray_image, lower, upper)
        gray_image = cv.bitwise_and(ecg.data, ecg.data, mask=mask)
        ecg.to_GRAY()
        ecg.data = mask
        # OTSU binarization
        threshold = self.__binarize(ecg)
        # Threshold
        cv.threshold(
            ecg.data, threshold, ecg.white, cv.THRESH_BINARY
        )
        #ecg.threshold(threshold, ecg.white)
        # Outline borders
        ecg = self.__outline_borders(ecg)
        ecg.to_GRAY()
        return ecg

    def __binarize(self, ecg: Image) -> Image:
        """
        Performs the Otsu's Thresholding algorithm to obtain a single intensity
        threshold that separate pixels into two classes, foreground and background.
        See http://web-ext.u-aizu.ac.jp/course/bmclass/documents/otsu1979.pdf.
        
        Args:
            ecg (Image): ECG image.

        Returns:
            Image: Image binarized.
        """
        L = 256
        N = ecg.height * ecg.width
        n, _ = np.histogram(ecg.data, L, range=(0, L - 1))
        p = n / N
        omega = lambda k: sum(p[0:k])
        mu = lambda k: sum([(i + 1) * p_i for i, p_i in enumerate(p[0:k])])
        mu_t = mu(L)
        sigma_b = lambda k: ((mu_t * omega(k) - mu(k)) ** 2) / (
            omega(k) * (1 - omega(k))
        )
        # First and last value will return NaN, so they are fixed at 0
        sigma_b_eval = map(
            lambda k: sigma_b(k) if omega(k) != 0 and omega(k) != 1 else 0,
            range(L),
        )
        # Get max sigma_b(k); 0 <= k < L
        k = max(enumerate(sigma_b_eval), key=lambda x: x[1])[0]
        ecg = ecg.threshold(k, ecg.white)
        return ecg

    def __outline_borders(self, ecg: Image) -> Image:
        """
        Outlines an ECG image, by joining all possible disconnected signals that have
        been cut off because they do not fit in the grid.

        Args:
            ecg (Image): ECG image.

        Returns:
            Image: ECG image outlined.
        """
        WHITE = ecg.white
        BLACK = ecg.black
        MAX_DIST = 0.02 * ecg.width
        # Delete thick black lines in borders
        for row in list(range(10)) + list(range(ecg.height - 10, ecg.height)):
            points = np.where(ecg[row, :] == BLACK)[0]
            prop = np.count_nonzero(points) / ecg.width
            if prop >= 0.95:
                ecg[row, :] = WHITE
        for col in list(range(10)) + list(range(ecg.width - 10, ecg.width)):
            points = np.where(ecg[:, col] == BLACK)[0]
            prop = np.count_nonzero(points) / ecg.height
            if prop >= 0.95:
                ecg[:, col] = WHITE
        # Join possible disconnected signals due to space limitations
        non_white=np.any(ecg[:,:] == 0, axis=1)
        non_white_idx = np.where(non_white)[0]
        for row in [non_white_idx[0], non_white_idx[-1]]:
            points = np.where(ecg[row, :] == BLACK)[0]
            for p1, p2 in zip(points[0:], points[1:]):
                if abs(p1 - p2) <= MAX_DIST:
                    ecg[row, p1:p2] = BLACK
        return ecg
