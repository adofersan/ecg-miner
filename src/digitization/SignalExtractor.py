# Standard library imports
from math import ceil
from itertools import groupby
from operator import itemgetter
from typing import Iterable

# Third-party imports
import numpy as np
from scipy.signal import find_peaks

# Application-specific imports
from utils.error.DigitizationError import DigitizationError
from utils.graphics.Image import Image
from utils.graphics.Point import Point


class SignalExtractor:
    """
    Signal extractor of an ECG image.
    """

    def __init__(self, n: int) -> None:
        """
        Initialization of the signal extractor.

        Args:
            n (int): Number of signals to extract.
        """
        self.__n = n
 
    def extract_signals(self, ecg: Image) -> Iterable[Iterable[Point]]:
        """
        Extract the signals of the ECG image.

        Args:
            ecg (Image): ECG image from which to extract the signals.

        Raises:
            DigitizationError: The indicated number of ROI could not be detected.
        
        Returns:
            Iterable[Iterable[Point]]: List with the list of points of each signal.
        """
        N = ecg.width
        LEN, SCORE = (2, 3)  # Cache values
        rois = self.__get_roi(ecg)
        mean = lambda cluster: (cluster[0] + cluster[-1]) / 2
        cache = {}

        for col in range(1, N):
            prev_clusters = self.__get_clusters(ecg, col - 1)
            if not len(prev_clusters):
                continue
            clusters = self.__get_clusters(ecg, col)
            for c in clusters:
                # For each row get best cluster center based on minimizing the score
                cache[col, c] = [None] * self.__n
                for roi_i in range(self.__n):
                    costs = {}
                    for pc in prev_clusters:
                        node = (col - 1, pc)
                        ctr = ceil(mean(pc))
                        if node not in cache.keys():
                            val = [ctr, None, 1, 0]
                            cache[node] = [val] * self.__n
                        ps = cache[node][roi_i][SCORE]  # Previous score
                        d = abs(ctr - rois[roi_i])  # Vertical distance to roi
                        g = self.__gap(pc, c)  # Disconnection level
                        costs[pc] = ps + d + N / 10 * g

                    best = min(costs, key=costs.get)
                    y = ceil(mean(best))
                    p = (col - 1, best)
                    l = cache[p][roi_i][LEN] + 1
                    s = costs[best]
                    cache[col, c][roi_i] = (y, p, l, s)

        # Backtracking
        raw_signals = self.__backtracking(cache, rois)
        return raw_signals
    
    def __get_roi(self, ecg: Image) -> Iterable[int]:
        """
        Get the coordinates of the ROI of the ECG image.

        Args:
            ecg (Image): ECG image from which to extract the ROI.

        Raises:
            DigitizationError: The indicated number of ROI could not be detected.
        
        Returns:
            Iterable[int]: List of row coordinates of the ROI.
        """
        WINDOW = 10
        SHIFT = (WINDOW - 1) // 2
        stds = np.zeros(ecg.height)
        for i in range(ecg.height - WINDOW + 1):
            x0, x1 = (0, ecg.width)
            y0, y1 = (i, i + WINDOW - 1)
            std = ecg[y0:y1, x0:x1].reshape(-1).std()
            stds[i + SHIFT] = std
        # Find peaks
        min_distance = int(ecg.height * 0.1)
        peaks, _ = find_peaks(stds, distance=min_distance)
        rois = sorted(peaks, key=lambda x: stds[x], reverse=True)
        if len(rois) < self.__n:
            raise DigitizationError("The indicated number of rois could not be detected.")
        rois = rois[0 : self.__n]
        rois = sorted(rois)
        return rois

    def __get_clusters(
        self, ecg: Image, col: Iterable[int]
    ) -> Iterable[Iterable[int]]:
        """
        Get the clusters of a certain column of an ECG. The clusters are
        regions of consecutive black pixels.

        Args:
            ecg (Image): ECG image.
            col (Iterable[int]): Column of the ECG from which to extract the clusters.

        Returns:
            Iterable[Iterable[int]]: List of the row coordinates of the clusters.
        """
        BLACK = 0
        clusters = []
        black_p = np.where(ecg[:, col] == BLACK)[0]
        for _, g in groupby(
            enumerate(black_p), lambda idx_val: idx_val[0] - idx_val[1]
        ):
            clu = tuple(map(itemgetter(1), g))
            clusters.append(clu)

        return clusters

    def __gap(
        self,
        pc: Iterable[int],
        c: Iterable[int],
    ) -> int:
        """
        Compute the gap between two clusters. It is the vertical white space between
        them. This gap will be 0 if they are in direct contact with each other.

        Args:
            pc (Iterable[int]): Cluster of the previous column.
            c (Iterable[int]): Cluster of the main column.

        Returns:
            int: Gap between the clusters.
        """
        pc_min, pc_max = (pc[0], pc[-1])
        c_min, c_max = (c[0], c[-1])
        d = 0
        if pc_min <= c_min and pc_max <= c_max:
            d = len(range(pc_max + 1, c_min))
        elif pc_min >= c_min and pc_max >= c_max:
            d = len(range(c_max + 1, pc_min))
        # Otherwise clusters are adjacent
        return d

    def __backtracking(
        self, cache: dict, rois: Iterable[int]
    ) -> Iterable[Iterable[Point]]:
        """
        Performs a backtracking process over the cache of links between clusters
        to extract the signals.

        Args:
            cache (dict): Cache with the links between clusters.
            rois (Iterable[int]): List with the row coordinates of the rois.

        Returns:
            Iterable[Iterable[Point]]: List with the list of points of each signal.
        """
        X_COORD, CLUSTER = (0, 1)  # Cache keys
        Y_COORD, PREV, LEN = (0, 1, 2)  # Cache values
        mean = lambda cluster: (cluster[0] + cluster[-1]) / 2
        raw_signals = [None] * self.__n
        for roi_i in range(self.__n):
            # Get candidate points (max signal length)
            roi = rois[roi_i]
            max_len = max([v[roi_i][LEN] for v in cache.values()])
            cand_nodes = [
                node
                for node, stats in cache.items()
                if stats[roi_i][LEN] == max_len
            ]
            # Best last point is the one more closer to ROI
            best = min(
                cand_nodes,
                key=lambda node: abs(ceil(mean(node[CLUSTER])) - roi),
            )
            raw_s = []
            clusters = []
            while best is not None:
                y = cache[best][roi_i][Y_COORD]
                raw_s.append(Point(best[X_COORD], y))
                clusters.append(best[CLUSTER])
                best = cache[best][roi_i][PREV]
            raw_s = list(reversed(raw_s))
            clusters = list(reversed(clusters))
            # Peak delineation
            roi_dist = [abs(p.y - roi) for p in raw_s]
            peaks, _ = find_peaks(roi_dist)
            for p in peaks:
                cluster = clusters[p - 1]
                farthest = max(cluster, key=lambda x: abs(x - roi))
                raw_s[p] = Point(raw_s[p].x, farthest)
            raw_signals[roi_i] = raw_s
        return raw_signals
