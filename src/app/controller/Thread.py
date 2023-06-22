# Standard library imports
from typing import Callable, Iterable
from os.path import realpath, sep

# Third-party imports
from PyQt5.QtCore import QRunnable, pyqtSlot

# Application-specific imports
from app.controller.SignalContainer import SignalContainer
from utils.error.DigitizationError import DigitizationError
from digitization.Digitizer import Digitizer


class Thread(QRunnable):
    """
    Thread in charge of digitize a batch of ECG.
    """

    def __init__(
        self, digitizer: Digitizer, paths: Iterable[str], is_digitizing: Callable
    ) -> None:
        """
        Initialization of the thread.

        Args:
            digitizer (Digitizer): Object in charge of the digitization of a single ECG.
            paths (Iterable[str]): Input paths of the ECG image files.
            is_digitizing (Callable): Function to check if the system is digitizing
                or not.
        """
        super().__init__()
        self.__digitizer = digitizer
        self.__paths = paths
        self.__is_digitizing = is_digitizing
        self.__signals = SignalContainer()

    @pyqtSlot()
    def run(self):
        """
        Digitize the batch of ECG with the settings specified in the model.
        It will stop if the model state says digitization has stopped.
        """
        for i, path in self.__paths:
            filename = realpath(path).split(sep)[-1]
            if not self.__is_digitizing():
                break
            try:
                self.__digitizer.digitize(path)
            except DigitizationError as e:
                self.__signals.error.emit(i, str(e) + f" ({filename})")
            else:
                msg = filename + " digitized"
                self.__signals.progress.emit(i, msg)
        self.__signals.finished.emit()

    def progress_connect(self, func: Callable) -> None:
        """
        Connect the progress signal with a certain function.

        Args:
            func (Callable): Function to be connected.
        """
        self.__signals.progress.connect(func)

    def finished_connect(self, func: Callable) -> None:
        """
        Connect the finished signal with a certain function.

        Args:
            func (Callable): Function to be connected.
        """
        self.__signals.finished.connect(func)

    def error_connect(self, func: Callable) -> None:
        """
        Connect the error signal with a certain function.

        Args:
            func (Callable): Function to be connected.
        """
        self.__signals.error.connect(func)
