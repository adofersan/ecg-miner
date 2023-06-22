# Third-party imports
from PyQt5.QtCore import QObject, pyqtSignal

class SignalContainer(QObject):
    """
    Container of the possible signals of a Miner Thread (progress, finished and error).
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(int, str)
