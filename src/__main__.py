# Standard library imports
from os.path import dirname, abspath
import os
import sys
sys.path.insert(1, dirname(abspath(__file__)))

# Third-party imports
from PyQt5.QtWidgets import QApplication

# Application-specific imports
from app.view.View import View
from app.model.Model import Model
from app.controller.Controller import Controller

"""
Main script for running ECGMiner app.
"""
if __name__ == "__main__":
    # Change path if main is executed via pyinstaller .exe
    if hasattr(sys, "_MEIPASS"):
        os.chdir(sys._MEIPASS)
    app = QApplication(sys.argv)
    model = Model()
    view = View()
    controller = Controller(model, view)
    view.set_controller(controller)
    app.exec_()
