# Standard library imports
from datetime import datetime
import os
from typing import Iterable, Optional

# Third-party imports
from PyQt5.QtWidgets import (
    QMainWindow,
    QFileDialog,
    qApp,
    QMessageBox,
)
from PyQt5.QtGui import QIcon, QTextCursor, QPixmap, QImage
from PyQt5.uic import loadUi

# Application-specific imports
from utils.graphics.Image import Image
from utils.ecg.Format import Format


class View(QMainWindow):
    """
    Main view of ECG Miner app. It contains a GUI to digitize the signals of ECG.
    """

    def __init__(self) -> None:
        """
        Initialization of the view. Load the GUI and show it.
        """
        super(View, self).__init__()
        UI_PATH = r"./ui/"
        # Attributes
        self.controller = None
        self.__browse_path = None
        self.__signal_icon = QIcon(UI_PATH + "signal.png")
        self.__color_signal_icon = QIcon(UI_PATH + "color_signal.png")
        # Load GUI and icons
        loadUi(UI_PATH + "gui.ui", self)
        self.setWindowIcon(QIcon(UI_PATH + "logo.ico"))
        self.setWindowTitle("ECG Miner")
        self.icon_lbl.setPixmap(QPixmap(UI_PATH + "logo.ico"))
        self.browse_bttn.setIcon(QIcon(UI_PATH + "browse.png"))
        self.outpath_bttn.setIcon(QIcon(UI_PATH + "outpath.png"))
        self.digitize_bttn.setIcon(QIcon(UI_PATH + "digitize.png"))
        self.cancel_bttn.setIcon(QIcon(UI_PATH + "cancel.png"))
        self.highlight_bttn.setIcon(QIcon(UI_PATH + "color_signal.png"))

        # Events
        self.layout_cbox.currentIndexChanged.connect(self.__layout_idx_changed)
        self.rhythm_1_cbox.currentIndexChanged.connect(
            self.__rhythm_idx_changed
        )
        self.rhythm_2_cbox.currentIndexChanged.connect(
            self.__rhythm_idx_changed
        )
        self.rhythm_3_cbox.currentIndexChanged.connect(
            self.__rhythm_idx_changed
        )
        self.rp_left_rbttn.toggled.connect(self.__rp_toggled)
        self.rp_right_rbttn.toggled.connect(self.__rp_toggled)
        self.cabrera_chk.stateChanged.connect(self.__cabrera_state_chg)
        self.ocr_chk.stateChanged.connect(self.__ocr_state_chg)
        self.interpolate_chk.stateChanged.connect(
            self.__interpolate_state_or_val_chg
        )
        self.interpolate_spin.valueChanged.connect(
            self.__interpolate_state_or_val_chg
        )
        self.ecg_name_cbox.currentTextChanged.connect(
            self.__ecg_selector_curr_txt_chg
        )
        self.browse_bttn.clicked.connect(self.__browse_clicked)
        self.outpath_bttn.clicked.connect(self.__outpath__clicked)
        self.digitize_bttn.clicked.connect(self.__digitize_clicked)
        self.highlight_bttn.clicked.connect(self.__highlight_clicked)
        self.cancel_bttn.clicked.connect(self.__cancel_clicked)

        # Show
        self.log("SESSION STARTED")
        self.show()
    def set_controller(self, controller: "Controller") -> None:
        """
        Set the controller of the app to the view.

        Args:
            controller (Controller): Controller of the app.
        """
        self.controller = controller
        self.restart()
        
    def log(self, msg: str, error: bool = False) -> None:
        """
        Show a message in the log.

        Args:
            msg (str): Message to show
            error (bool, optional): True if the message to be shown is an error
                False if not. Defaults to False.
        """
        color = "red" if error else "white"
        lvl = "ERROR: " if error else "INFO: &nbsp;"
        get_log = lambda message: (
            f"<div style='color:{color};'>"
            + "["
            + datetime.now().strftime("%H:%M:%S")
            + "] "
            + lvl
            + message
            + "</div>"
            + "<br>"
        )
        cursor = QTextCursor(self.log_txt_browser.textCursor())
        cursor.insertHtml(get_log(msg))
        verScrollBar = self.log_txt_browser.verticalScrollBar()
        verScrollBar.setValue(verScrollBar.maximum())

    def restart(self) -> None:
        """
        Restart the GUI. It will leave the interface in the initial state,
        except for the log which will remain the same.
        """
        # Settings
        self.enable_settings(False)
        self.layout_cbox.setCurrentIndex(0)
        RYTHM = ["None"] + [lead.name for lead in Format.STANDARD]
        self.rhythm_1_cbox.blockSignals(True)
        self.rhythm_2_cbox.blockSignals(True)
        self.rhythm_3_cbox.blockSignals(True)
        for lead in RYTHM:
            self.rhythm_1_cbox.addItem(lead)
            self.rhythm_2_cbox.addItem(lead)
            self.rhythm_3_cbox.addItem(lead)
        self.rhythm_2_cbox.setCurrentIndex(0)
        self.rhythm_3_cbox.setCurrentIndex(0)
        self.rhythm_1_cbox.blockSignals(False)
        self.rhythm_2_cbox.blockSignals(False)
        self.rhythm_3_cbox.blockSignals(False)
        self.rhythm_1_cbox.setCurrentIndex(2)
        self.cabrera_chk.setChecked(False)
        self.ocr_chk.setChecked(False)
        self.interpolate_chk.setChecked(False)
        self.interpolate_spin.setValue(5000)
        self.interpolate_spin.setVisible(False)
        # ECG viewer
        self.enable_ecg_selector(False)
        self.ecg_name_cbox.clear()
        self.enable_ecg_counter(False)
        self.ecg_counter_lbl.setText("")
        self.viewer.clear()
        self.enable_progress(False)
        self.set_progress(0)
        # Action buttons
        self.enable_browse(True)
        self.enable_digitize(False)
        self.enable_highlight(False)
        self.set_highlight(False)
        self.enable_cancel(False)

    def enable_settings(self, enable: bool) -> None:
        """
        Choose if settings will be enabled or not.

        Args:
            enable (bool): True if settings will be enabled False if not.
        """
        style = (
            "color: rgb(255,255,255)" if enable else "color: rgb(150,150,150)"
        )
        # Layout
        self.layout_lbl.setStyleSheet(style)
        self.layout_cbox.setEnabled(enable)
        self.layout_cbox.setStyleSheet(style)
        # Rhythm strips
        self.rhythm_1_lbl.setStyleSheet(style)
        self.rhythm_2_lbl.setStyleSheet(style)
        self.rhythm_3_lbl.setStyleSheet(style)
        self.rhythm_1_cbox.setStyleSheet(style)
        self.rhythm_2_cbox.setStyleSheet(style)
        self.rhythm_3_cbox.setStyleSheet(style)
        self.rhythm_1_cbox.setEnabled(enable)
        self.rhythm_2_cbox.setEnabled(enable)
        self.rhythm_3_cbox.setEnabled(enable)
        # RP radio buttons
        self.rp_left_rbttn.setStyleSheet(style)
        self.rp_right_rbttn.setStyleSheet(style)
        self.rp_left_rbttn.setEnabled(enable)
        self.rp_right_rbttn.setEnabled(enable)
        # Cabrera format
        self.cabrera_chk.setStyleSheet(style)
        self.cabrera_chk.setEnabled(enable)
        # Browse outpath
        self.change_path_lbl.setStyleSheet(style)
        self.outpath_bttn.setStyleSheet(style)
        self.outpath_bttn.setEnabled(enable)
        # Metadata OCR
        self.ocr_chk.setStyleSheet(style)
        self.ocr_chk.setEnabled(enable)
        # Interpolate
        self.interpolate_chk.setStyleSheet(style)
        self.interpolate_chk.setEnabled(enable)
        self.interpolate_spin.setStyleSheet(style)
        self.interpolate_spin.setEnabled(enable)

    def __layout_idx_changed(self) -> None:
        """
        Listener invoked when "currentIndexChanged" event is performed on the layout
        combobox.
        """
        text = self.layout_cbox.currentText()
        layout = (int(text[0:-2]), int(text[-1]))
        self.controller.proc_layout_evt(layout)

    def __rhythm_idx_changed(self) -> None:
        """
        Listener invoked when "currentIndexChanged" event is performed on
        any of the rhythm strips comboboxes.
        """
        CBOXES = [self.rhythm_1_cbox, self.rhythm_2_cbox, self.rhythm_3_cbox]
        leads_selected = [cbox.currentText() for cbox in CBOXES]
        self.controller.proc_rhythm_evt(leads_selected)

    def set_rhythm(
        self,
        leads_available: Iterable[Iterable[str]],
        leads_selected: Iterable[str],
    ) -> None:
        """
        Set the available leads on each rhythm strip. Each lead cannot be selected
        more than once.

        Args:
            rhythm_available (Iterable[Iterable[str]]): List with the available leads of each rhythm strip.
            leads_selected (Iterable[str]): List with the selected lead in each rhythm strip.
        """
        CBOXES = [self.rhythm_1_cbox, self.rhythm_2_cbox, self.rhythm_3_cbox]
        ALL_ITEMS = lambda cbox: [
            cbox.itemText(i) for i in range(cbox.count())
        ]
        for idx, cbox in enumerate(CBOXES):
            cbox = CBOXES[idx]
            cbox.blockSignals(True)
            cbox.clear()
            cbox.addItems(leads_available[idx])
            for i, item in enumerate(ALL_ITEMS(cbox)):
                if item == leads_selected[idx]:
                    cbox.setCurrentIndex(i)
            cbox.blockSignals(False)

    def enable_rhythm(self, enable: bool) -> None:
        """
        Choose if rhythm strips will be enabled or not.

        Args:
            enable (bool): True if rhythm strips will be enabled False if not.
        """
        style = (
            "color: rgb(255,255,255)" if enable else "color: rgb(150,150,150)"
        )

        self.rhythm_1_lbl.setStyleSheet(style)
        self.rhythm_2_lbl.setStyleSheet(style)
        self.rhythm_3_lbl.setStyleSheet(style)
        self.rhythm_1_cbox.setStyleSheet(style)
        self.rhythm_2_cbox.setStyleSheet(style)
        self.rhythm_3_cbox.setStyleSheet(style)

        self.rhythm_1_cbox.setEnabled(enable)
        self.rhythm_2_cbox.setEnabled(enable)
        self.rhythm_3_cbox.setEnabled(enable)
        if not enable:
            self.rhythm_1_cbox.setCurrentIndex(0)
            self.rhythm_2_cbox.setCurrentIndex(0)
            self.rhythm_3_cbox.setCurrentIndex(0)

    def __rp_toggled(self) -> None:
        """
        Listener invoked when "toggled" event is performed on the "RP radio buttons".
        """
        self.controller.proc_rp_evt(self.rp_right_rbttn.isChecked())
    
    def __cabrera_state_chg(self) -> None:
        """
        Listener invoked when "stateChanged" event is performed on the "Cabrera"
        checkbox.
        """
        self.controller.proc_cabrera_evt(self.cabrera_chk.isChecked())

    def __outpath__clicked(self) -> None:
        """
        Listener invoked when "clicked" event is performed on the "browse output
        path" button. It will displays a file dialog to choose a directory to be
        set as the output path of the digitization.
        """
        directory = QFileDialog.getExistingDirectory(self)
        self.controller.proc_outpath_evt(directory)

    def enable_outpath(self, enable: bool) -> None:
        """
        Choose if browse output path setting will be enabled or not.

        Args:
            enable (bool): True if output path setting will be enabled False if not.
        """
        self.outpath_bttn.setEnabled(enable)

    def __ocr_state_chg(self) -> None:
        """
        Listener invoked when "stateChanged" event is performed on the "Metadata OCR"
        checkbox.
        """
        self.controller.proc_ocr_evt(self.ocr_chk.isChecked())

    def __interpolate_state_or_val_chg(self) -> None:
        """
        Listener invoked when "stateChanged" event is performed on the "Interpolate"
        checkbox or "valueChanged" on the "Interpolate" checkbox.
        """
        chk = self.interpolate_chk.isChecked()
        self.interpolate_spin.setVisible(chk)
        self.controller.proc_interpolate_evt(
            self.interpolate_spin.value() if chk else None
        )

    def load_ecg(self, img: Optional[Image]) -> None:
        """
        Loads an ECG image in the main viewer of the app.

        Args:
            img (Image): ECG image. If None no image will be shown.
        """
        if img is None:
            return
        img = QImage(
            img.data,
            img.width,
            img.height,
            img.width * 3,
            QImage.Format_RGB888,
        )
        pixmap = QPixmap(img)
        self.viewer.setPixmap(pixmap)
        qApp.processEvents()

    def set_ecg_selector(self, files: Iterable[str]) -> None:
        """
        Set the contents of the ECG selector.

        Args:
            files (Iterable[str]): List with filenames of the ECG.
        """
        self.ecg_name_cbox.clear()
        for ecg in files:
            self.ecg_name_cbox.addItem(ecg)

    def __ecg_selector_curr_txt_chg(self) -> None:
        """
        Listener invoked when "currentTextChanged" event is performed on the
        ECG combobox selector.
        """
        self.controller.proc_ecg_selected_evt(
            self.ecg_name_cbox.currentIndex()
        )

    def enable_ecg_selector(self, enable: bool) -> None:
        """
        Choose if ECG selector will be enabled or not.

        Args:
            enable (bool): True if ECG selector will be enabled False if not.
        """
        self.ecg_name_cbox.setEnabled(enable)

    def set_ecg_counter(self, curr: int, last: int) -> None:
        """
        Set the counter of the current ECG displayed.

        Args:
            curr (int): Current value to set the counter.
            last (int): Last possible value of the counter.
        """
        self.ecg_counter_lbl.setText(f"({curr}/{last})")

    def enable_ecg_counter(self, enable: bool) -> None:
        """
        Choose if ECG counter will be enabled or not.

        Args:
            enable (bool): True if ECG counter will be enabled False if not.
        """
        self.ecg_counter_lbl.setEnabled(enable)

    def set_progress(self, progress: int) -> None:
        """
        Set the progress of the digitization.

        Args:
            progress (int): Progress of the digitization.
        """
        self.progress_bar.setValue(progress)

    def enable_progress(self, enable: bool) -> None:
        """
        Choose if digitization progress will be enabled or not.

        Args:
            enable (bool): True if progress bar will be enabled False if not.
        """
        self.progress_bar.setEnabled(enable)

    def __browse_clicked(self) -> None:
        """
        Listener invoked when "clicked" event is performed on the "Browse files" button.
        It will displays a file dialog to choose the ECG files to be digitized.
        """
        paths = QFileDialog.getOpenFileNames(
            None,
            "Open files",
            self.__browse_path,
            "Images (*.jpeg *.jpg *.pdf *.png *.webp)",
        )
        files = paths[0]
        if len(files) > 0:
            self.__browse_path = os.path.dirname(files[0])
        self.controller.proc_browse_evt(files)

    def enable_browse(self, enable: bool) -> None:
        """
        Choose if browse files action will be enabled or not.

        Args:
            enable (bool): True if browse files action will be enabled False if not.
        """
        self.browse_bttn.setEnabled(enable)

    def __digitize_clicked(self) -> None:
        """
        Listener invoked when "clicked" event is performed on the "Digitized" button.
        """
        self.controller.proc_digitize_evt()

    def enable_digitize(self, enable: bool) -> None:
        """
        Choose if digitize action will be enabled or not.

        Args:
            enable (bool): True if digitize action will be enabled False if not.
        """
        self.digitize_bttn.setEnabled(enable)

    def __highlight_clicked(self) -> None:
        """
        Listener invoked when "clicked" event is performed on the "Highlight signals" button.
        """
        self.controller.proc_highlight_evt()

    def set_highlight(self, highlight: bool) -> None:
        """
        Set the visual aspect of the "Highlight signals" action.

        Args:
            highlighted (bool): True if lead signals are highlighted False if not.
        """
        icon = self.__signal_icon if highlight else self.__color_signal_icon
        self.highlight_bttn.setIcon(icon)

    def enable_highlight(self, enable: bool) -> None:
        """
        Choose if highlight action will be enabled or not.

        Args:
            enable (bool): True if highlight action will be enabled False if not.
        """
        self.highlight_bttn.setEnabled(enable)

    def __cancel_clicked(self) -> None:
        """
        Listener invoked when "clicked" event is performed on the "Cancel" button.
        A message box will be displayed to confirm the cancel.
        """
        cancel_question = QMessageBox.question(
            self,
            "Cancel digitization",
            "Are you sure you want to cancel digitization and close all files?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        self.controller.proc_cancel_evt(cancel_question == QMessageBox.Yes)

    def enable_cancel(self, enable: bool) -> None:
        """
        Choose if cancel action will be enabled or not.

        Args:
            enable (bool): True if cancel action will be enabled False if not.
        """
        self.cancel_bttn.setEnabled(enable)
