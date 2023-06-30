# Standard library imports
from typing import Iterable, Tuple

# Third-party imports
import numpy as np
import pandas as pd
from scipy import interpolate

# Application-specific imports
from utils.error.DigitizationError import DigitizationError
from utils.graphics.Image import Image
from utils.ecg.Lead import Lead
from utils.ecg.Format import Format
from utils.graphics.Point import Point


class Postprocessor:
    """
    Postprocessor of an ECG image.
    """

    def __init__(
        self,
        layout: Tuple[int, int],
        rhythm: Iterable[Lead],
        rp_at_right: bool,
        cabrera: bool,
        interpolation: int = None,
    ) -> None:
        """
        Initialization of the post-processor.

        Args:
            layout (Tuple[int, int]): Layout of the ECG.
            rhythm (Iterable[Lead]): Ordered rhythm strips.
            rp_at_right (bool): True if ECG reference pulses are at right False if not.
            cabrera (bool): True if ECG is in Cabrera format False if not.
            interpolation (int, optional): Number of total data interpolated from signals.
                It is the number of observations of the longest lead. Defaults to None.
        """
        self.__layout = layout
        self.__rhythm = rhythm
        self.__rp_at_right = rp_at_right
        self.__cabrera = cabrera
        self.__interpolation = interpolation

    def postprocess(
        self, raw_signals: Iterable[Iterable[Point]], ecg_crop: Image
    ) -> Tuple[pd.DataFrame, Image]:
        """
        Post process the raw signals, getting a matrix with the signals of 12 leads
        and an image with the trace.

        Args:
            raw_signals (Iterable[Iterable[Point]]): List with the list of points of each signal.
            ecg_crop (Image): Crop of the ECG gridline with the signals.

        Returns:
            Tuple[pd.DataFrame,Image]: Dataframe with the signals and image of the trace.
        """
        signals, ref_pulses = self.__segment(raw_signals)
        data = self.__vectorize(signals, ref_pulses)
        trace = self.__get_trace(ecg_crop, signals, ref_pulses)
        return (data, trace)

    def __segment(
        self, raw_signals: Iterable[Iterable[Point]]
    ) -> Tuple[Iterable[Iterable[Point]], Iterable[Tuple[int, int]]]:
        """
        Segments the raw signals, dividing them by lead. Reference pulses are extracted
        and removed for the signals.

        Args:
            raw_signals (Iterable[Iterable[Point]]): List with the list of points of each signal.

        Returns:
            Tuple[Iterable[Iterable[Point]], Iterable[Tuple[int, int]]]: Tuple with
            list with the points of each of the signals of each lead and list with
            the reference pulses of each ECG row.
        """
        INI, MID, END = (0, 1, 2)
        LIMIT = min([len(signal) for signal in raw_signals])
        PIXEL_EPS = 5
        # Check if ref pulse is at right side or left side of the ECG
        first_pixels = [pulso[-1].y for pulso in raw_signals]
        direction = (
            range(-1, -LIMIT, -1) if self.__rp_at_right else range(LIMIT)
        )
        pulse_pos = INI
        ini_count = 0
        cut = None
        for i in direction:
            y_coords = [
                pulso[i].y - ini
                for pulso, ini in zip(raw_signals, first_pixels)
            ]
            y_coords = sorted(y_coords)
            at_v0 = any([abs(y) <= PIXEL_EPS for y in y_coords])
            break_symmetry = (pulse_pos == END) and (
                not at_v0 or ini_count <= 0
            )
            if break_symmetry:
                cut = i
                break
            if pulse_pos == INI:
                if at_v0:
                    ini_count += 1
                else:
                    pulse_pos = MID
            elif pulse_pos == MID and at_v0:
                pulse_pos = END
                ini_count -= 1
            elif pulse_pos == END:
                ini_count -= 1
        # Slice signal
        signal_slice = (
            slice(0, cut + 1) if self.__rp_at_right else slice(cut, None)
        )
        signals = [rs[signal_slice] for rs in raw_signals]
        # Slice pulses
        pulse_slice = (
            slice(cut + 1, None) if self.__rp_at_right else slice(0, cut + 1)
        )
        ref_pulses = [
            sorted(map(lambda p: p.y, rs[pulse_slice]), reverse=True)
            for rs in raw_signals
        ]
        ref_pulses = [
            (first_pixels[i], ref_pulses[i][-1])
            for i in range(len(raw_signals))
        ]
        return (signals, ref_pulses)

    def __vectorize(
        self,
        signals: Iterable[Iterable[Point]],
        ref_pulses: Iterable[Tuple[int, int]],
    ) -> pd.DataFrame:
        """
        Vectorize the signals, normalizing them and storing them in a dataframe.

        Args:
            signals (Iterable[Iterable[Point]]): List with the points of each of
                the signals of each lead.
            ref_pulses (Iterable[Tuple[int, int]]): List with the reference pulses
                of each ECG row.

        Raises:
            DigitizationError: Reference pulses have not been detected correctly.

        Returns:
            pd.DataFrame: Dataframe with lead signals.
        """
        # Pad all signals to closest multiple number of ECG ncols
        NROWS, NCOLS = self.__layout
        ORDER = Format.CABRERA if self.__cabrera else Format.STANDARD
        max_len = max(map(lambda signal: len(signal), signals))
        max_diff = max_len % NCOLS
        max_pad = 0 if max_diff == 0 else NCOLS - max_diff
        total_obs = (
            max_len + max_pad
            if self.__interpolation is None
            else self.__interpolation
        )
        # Linear interpolation to get a certain number of observations
        interp_signals = np.empty((len(signals), total_obs))
        for i in range(len(signals)):
            signal = [p.y for p in signals[i]]
            interpolator = interpolate.interp1d(np.arange(len(signal)), signal)
            interp_signals[i, :] = interpolator(
                np.linspace(0, len(signal) - 1, total_obs)
            )
        ecg_data = pd.DataFrame(
            np.nan,
            index=np.arange(total_obs),
            columns=[lead.name for lead in Format.STANDARD],
        )
        for i, lead in enumerate(ORDER):
            rhythm = lead in self.__rhythm
            r = self.__rhythm.index(lead) + NROWS if rhythm else i % NROWS
            c = 0 if rhythm else i // NROWS
            # Reference pulses
            volt_0 = ref_pulses[r][0]
            volt_1 = ref_pulses[r][1]
            if volt_0 == volt_1:
                raise DigitizationError(
                    f"Reference pulses have not been detected correctly"
                )

            # Get correspondent part of the signal for current lead
            signal = interp_signals[r, :]
            obs_num = len(signal) // (1 if rhythm else NCOLS)
            signal = signal[c * obs_num : (c + 1) * obs_num]
            # Scale signal with ref pulses
            signal = [(volt_0 - y) * (1 / (volt_0 - volt_1)) for y in signal]
            # Round voltages to 4 decimals
            signal = np.round(signal, 4)
            # Cabrera format -aVR
            if self.__cabrera and lead == Lead.aVR:
                signal = -signal
            # Save in correspondent dataframe location
            ecg_data.loc[
                (ecg_data.index >= len(signal) * c)
                & (ecg_data.index < len(signal) * (c + 1)),
                lead.name,
            ] = signal
        return ecg_data

    def __get_trace(
        self,
        ecg: Image,
        signals: Iterable[Iterable[Point]],
        ref_pulses: Iterable[Tuple[int, int]],
    ) -> Image:
        """
        Get the trace of the extraction algorithm performed over the ECG image.

        Args:
            ecg (Image): ECG image.
            signals (Iterable[Iterable[Point]]): List with the points of each of
                the signals of each lead.
            ref_pulses (Iterable[Tuple[int, int]]): List with the reference pulses
                of each ECG row.

        Returns:
            Image: ECG image with the trace painted over.
        """
        NROWS, NCOLS = self.__layout
        ORDER = Format.CABRERA if self.__cabrera else Format.STANDARD
        COLORS = [
            (0, 0, 255),
            (0, 255, 0),
            (255, 0, 0),
            (0, 200, 255),
            (255, 255, 0),
            (255, 0, 255),
            (0, 0, 125),
            (0, 125, 0),
            (125, 0, 0),
            (0, 100, 125),
            (125, 125, 0),
            (125, 0, 125),
        ]
        H_SPACE = 20

        trace = ecg.copy()
        trace.to_BGR()
        # Draw ref pulse dot lines
        for pulse in ref_pulses:
            for x in range(0, ecg.width, H_SPACE):
                volt_0, volt_1 = pulse
                # Volt_0
                trace.line(
                    Point(x, volt_0),
                    Point(x + H_SPACE // 2, volt_0),
                    (0, 0, 0),
                    thickness=1,
                )
                # Volt_1
                trace.line(
                    Point(x, volt_1),
                    Point(x + H_SPACE // 2, volt_1),
                    (0, 0, 0),
                    thickness=1,
                )

        # Draw signals
        for i, lead in enumerate(ORDER):
            rhythm = lead in self.__rhythm
            r = self.__rhythm.index(lead) + NROWS if rhythm else i % NROWS
            c = 0 if rhythm else i // NROWS
            signal = signals[r]
            obs_num = len(signal) // (1 if rhythm else NCOLS)
            signal = signal[c * obs_num : (c + 1) * obs_num]
            color = COLORS[i % len(COLORS)]
            for p1, p2 in zip(signal, signal[1:]):
                trace.line(p1, p2, color, thickness=2)
        return trace
