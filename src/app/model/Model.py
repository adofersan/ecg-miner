# Standard library imports
from typing import Iterable, Tuple, Optional

# Application-specific imports
from utils.ecg.Lead import Lead


class Model:
    """
    Model of the ECG Miner app. It contains all the information about the
    settings and the status of the digitization.
    """

    def __init__(self) -> None:
        # Settings
        self.__layout = (3, 4)
        self.__rhythm = Lead.II
        self.__rp_at_right = True
        self.__cabrera = False
        self.__ocr = False
        self.__outpath = None
        self.__interpolation = None
        # Status
        self.__digitizing = False
        self.__signals_highlighted = False
        self.__ecg_paths = None
        self.__selected_ecg_idx = None
        self.__digitized_ecg = None

    @property
    def layout(self) -> Tuple[int, int]:
        """
        Get the layout of the ECG.

        Returns:
            Tuple[int, int]: Layout of the ECG.
        """
        return self.__layout

    @layout.setter
    def layout(self, layout: Tuple[int, int]) -> None:
        """
        Set the layout of the ECG.

        Args:
            layout (Tuple[int, int]): New layout of the ECG.
        """
        self.__layout = layout

    @property
    def rhythm(self) -> Iterable[Lead]:
        """
        Get the list of rhythm strips of the ECG.

        Returns:
            Iterable[Lead]: List of rhythm strips of the ECG.
        """
        return self.__rhythm

    @rhythm.setter
    def rhythm(self, rhythm: Iterable[Lead]) -> None:
        """
        Set the list of rhythm strips of the ECG.

        Args:
            rhythm (Iterable[Lead]): List of rhythm strips of the ECG.
        """
        self.__rhythm = rhythm

    
    @property
    def rp_at_right(self) -> bool:
        """
        Check if reference pulses are at right.

        Returns:
            bool: True if ECG reference pulses are at right False if not.
        """
        return self.__rp_at_right

    @rp_at_right.setter
    def rp_at_right(self, rp_at_right: bool) -> None:
        """
        Set if reference pulses are at right.

        Args:
            rp_at_right (bool): True if ECG reference pulses are at right False if not.
        """
        self.__rp_at_right = rp_at_right
    
    @property
    def cabrera(self) -> bool:
        """
        Check if ECG are in Cabrera format.

        Returns:
            bool: True if ECG are in Cabrera format False if not.
        """
        return self.__cabrera

    @cabrera.setter
    def cabrera(self, cabrera: bool) -> None:
        """
        Set if ECG are in Cabrera format.

        Args:
            cabrera (bool): True if ECG in Cabrera format False if not.
        """
        self.__cabrera = cabrera

    @property
    def ocr(self) -> bool:
        """
        Check if ECG metadata will be extracted.

        Returns:
            bool: True if metadata will be extracted False if not.
        """
        return self.__ocr

    @ocr.setter
    def ocr(self, ocr: bool) -> None:
        """
        Set if ECG metadata will be extracted.

        Args:
            ocr (bool): True if metadata will be extracted False if not.
        """
        self.__ocr = ocr

    @property
    def outpath(self) -> Optional[str]:
        """
        Get the output path where the digitization results will be stored.

        Returns:
            Optional[str]: Output path of the digitization.
        """
        return self.__outpath

    @outpath.setter
    def outpath(self, outpath: Optional[str]) -> None:
        """
        Set the output path where the digitization results will be stored.

        Args:
            outpath (Optional[str]): New output path of the digitization.
        """
        self.__outpath = outpath

    @property
    def interpolation(self) -> Optional[int]:
        """
        Get the total observation number of the interpolation.

        Returns:
            Optional[int]: Total observation number of the interpolation.
                It will be None if no interpolation will be applied.
        """
        return self.__interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Optional[int]) -> None:
        """
        Set the total observation number of the interpolation.

        Args:
            interpolation (Optional[int]): New total observation number of the
                interpolation. If None no interpolation will be applied.
        """
        self.__interpolation = interpolation

    @property
    def digitizing(self) -> bool:
        """
        Check if the digitization process is currently in process.

        Returns:
            bool: True if the digitization process is currently in process
                  False if not.
        """
        return self.__digitizing

    @digitizing.setter
    def digitizing(self, digitizing: bool) -> None:
        """
        Set if the digitization process is currently in process.

        Args:
            digitizing (bool): True if the digitization process is in process
                  False if not.
        """
        self.__digitizing = digitizing

    @property
    def signals_highlighted(self) -> bool:
        """
        Check if lead signals of the current ECG are highlighted or not.

        Returns:
            bool: True if signals are highlighted False if not.
        """
        return self.__signals_highlighted

    @signals_highlighted.setter
    def signals_highlighted(self, signals_highlighted: bool) -> None:
        """
        Set if lead signals of the current ECG are highlighted or not.

        Args:
            signals_highlighted (bool): True if signals are highlighted False if not.
        """
        self.__signals_highlighted = signals_highlighted

    @property
    def ecg_paths(self) -> Optional[Iterable[str]]:
        """
        Get the ECG paths loaded.

        Returns:
            Optional[Iterable[str]]: ECG paths loaded.
        """
        return self.__ecg_paths

    @ecg_paths.setter
    def ecg_paths(self, ecg_paths: Optional[Iterable[str]]) -> None:
        """
        Set the ECG paths loaded.

        Args:
            ecg_paths (Optional[Iterable[str]]): ECG paths loaded.
        """
        self.__ecg_paths = ecg_paths
        if ecg_paths is not None:
            self.__digitized_ecg = [False] * len(self.__ecg_paths)

    @property
    def selected_ecg_idx(self) -> Optional[int]:
        """
        Get the index of the selected ECG.

        Returns:
            Optional[int]: Index of the selected ECG. It will be None if
                not ECG is selected.
        """
        return self.__selected_ecg_idx

    @selected_ecg_idx.setter
    def selected_ecg_idx(self, idx: Optional[int]) -> None:
        """
        Set the index of the selected ECG.

        Args:
            idx (Optional[int]): Index of the selected ECG or None if
                not ECG is selected.
        """
        self.__selected_ecg_idx = idx

    @property
    def progress(self) -> int:
        """
        Check the progress of the digitization process.

        Returns:
            int: Percentage of progress or None if no ECG are loaded.
        """
        if self.__digitized_ecg is None:
            return None
        pct = sum(self.__digitized_ecg) / len(self.__digitized_ecg) * 100
        pct = int(round(pct))
        return pct

    def is_digitized(self, idx: int) -> bool:
        """
        Check if an ECG is digitized or not.

        Args:
            idx (int): Index of the ECG to be checked.

        Returns:
            bool: True if it has been digitized (or at least tried), False if not.
        """
        return self.__digitized_ecg[idx]

    def set_digitized(self, idx: int) -> None:
        """
        Mark an ECG as digitized.

        Args:
            idx (int): Index of the ECG to set as digitized.
        """
        self.__digitized_ecg[idx] = True
