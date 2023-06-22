# Standard library imports
from os.path import basename, splitext
from typing import Iterable, Tuple

# Application-specific imports
from digitization.MetadataExtractor import MetadataExtractor
from digitization.SignalExtractor import SignalExtractor
from digitization.Preprocessor import Preprocessor
from digitization.Postprocessor import Postprocessor
from utils.ecg.Lead import Lead
from utils.graphics.Image import Image


class Digitizer:
    """
    A tool of lead signal digitization from ECG images in paper format.
    This class provides an algorithm for detecting the leads of an ECG,
    extract its signals and optionally get the written metadata with an OCR engine.
    """

    def __init__(
        self,
        layout: Tuple[int, int],
        rhythm: Iterable[Lead],
        rp_at_right:bool,
        cabrera: bool,
        outpath: str,
        ocr: bool,
        interpolation: int = None,
    ) -> None:
        """
        Initialization of the ECG Miner.

        Args:
            layout (Tuple[int, int]): Layout of the ECG.
            rhythm (Iterable[Lead]): Ordered rhythm strips.
            rp_at_right (bool): True if ECG reference pulses are at right False if not.
            cabrera (bool): True if ECG is in Cabrera format False if not.
            outpath (str): Output path to store the results of the digitization.
            ocr (bool): True if metadata is wanted to be extracted False if not.
            interpolation (int): Number of total data interpolated from signals.
                It is the number of observations of the longest lead. Defaults to None.
        """
        self.__outpath = outpath
        self.__preprocessor = Preprocessor()
        self.__signal_extractor = SignalExtractor(layout[0] + len(rhythm))
        self.__postprocessor = Postprocessor(
            layout, rhythm, rp_at_right, cabrera, interpolation
        )
        self.__ocr = MetadataExtractor() if ocr else None
    
    def digitize(self, path: str) -> None:
        """
        Digitize an ECG image in paper format.

        Args:
            path (str): Input path of the ECG image file.

        Raises:
            DigitizationError: The image is in a non-recognized format.
        """
        f_name, _ = splitext(basename(path))
        f_outpath = self.__outpath + "/" + f_name
        ecg = Image(path)
        frame = ecg.copy()
        # Preprocess
        ecg_crop, rect = self.__preprocessor.preprocess(ecg)
        # Extraction
        raw_signals = self.__signal_extractor.extract_signals(
            ecg_crop
        )
        # Postprocess
        data, trace = self.__postprocessor.postprocess(
            raw_signals, ecg_crop
        )
        # ECG data
        data.to_csv(f_outpath + ".csv", index=False)
        # ECG tracing
        tl = rect.top_left
        br = rect.bottom_right
        ecg[tl.y : br.y, tl.x : br.x] = trace.data
        ecg.save(f_outpath + "_trace" + ".png")
        # ECG metadata
        if self.__ocr is not None:
            frame[tl.y : br.y, tl.x : br.x] = frame.white
            metadata = self.__ocr.extract_metadata(frame)
            with open(f_outpath + "_metadata" + ".txt", "w") as f:
                f.write(metadata)
