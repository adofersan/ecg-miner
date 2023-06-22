# Standard library imports
import time
from os.path import basename, dirname, realpath, sep, splitext
from typing import Iterable, Optional, Tuple

# Third-party imports
import numpy as np
from PyQt5.QtCore import QThreadPool

# Application-specific imports
from app.controller.Thread import Thread
from app.model.Model import Model
from app.view.View import View
from utils.ecg.Lead import Lead
from utils.ecg.Format import Format
from utils.graphics.Image import Image
from digitization.Digitizer import Digitizer


class Controller:
    """
    Main controller of ECG Miner app. It contains a all the logic to process the
    inputs from the view and communicate with the model.
    """

    def __init__(self, model: Model, view: View) -> None:
        """
        Initialization of the controller.

        Args:
            model (Model): Model of the app.
            view (View): View of the app.
        """
        self.__model = model
        self.__view = view
        self.__active_threads = 0
        self.__ini_time = None

    def __load_img(self, path: str) -> Optional[Image]:
        """
        Loads an ECG image.

        Args:
            path (str): Path of the ECG image.

        Returns:
            Optional[Image]: ECG Image or None if file was not found.
        """
        img = None
        try:
            img = Image(path)
            img.to_RGB()
        except FileNotFoundError as e:
            self.__view.log(str(e), error=True)
        finally:
            return img

    def proc_layout_evt(self, layout: Tuple[int, int]) -> None:
        """
        Process the layout changed event. If layout has only 1 column,
        rhythm strips will be disabled.

        Args:
            layout (Tuple[int, int]): New layout of the ECG.
        """
        self.__model.layout = layout
        enable = layout[1] != 1
        self.__view.enable_rhythm(enable)

    def proc_rhythm_evt(self, leads_selected: Iterable[str]) -> None:
        """
        Process the rhythm strips changed event. Force to each lead to not be selected
        more than once.
        Args:
            leads_selected (Iterable[str]): List with the selected lead in each rhythm strip.
        """
        DELETE = lambda l, idx: l[:idx] + l[idx + 1 :]
        # If a rhythm strip is None, the following ones will be too
        for i in range(1, len(leads_selected)):
            if leads_selected[i - 1] == "None":
                leads_selected[i] = "None"
        leads_available = [None] * 3
        for i in range(len(leads_available)):
            lead_list = ["None"]
            # A rhythm strip can not be None if previous ones are not None
            if i == 0 or leads_selected[i - 1] != "None":
                lead_list += [lead.name for lead in Format.STANDARD]
            # Force a lead to not be chosen more than once
            leads_available[i] = [
                item
                for item in lead_list
                if item not in set(DELETE(leads_selected, i)) - {"None"}
            ]
        self.__model.rhythm = [Lead[s] for s in leads_selected if s != "None"]
        self.__view.set_rhythm(leads_available, leads_selected)

    def proc_rp_evt(self, rp_at_right: bool) -> None:
        """
        Process the reference pulse event.

        Args:
            rp_at_right (bool): True if reference pulse is at left False if not.
        """
        self.__model.rp_at_right = rp_at_right

    def proc_cabrera_evt(self, cabrera: bool) -> None:
        """
        Process the cabrera format event.

        Args:
            cabrera (bool): True if Cabrera format has been selected False if not.
        """
        self.__model.cabrera = cabrera

    def proc_outpath_evt(self, outpath: str) -> None:
        """
        Process the browse output path changed event.

        Args:
            outpath (str): New output directory path.
        """
        if outpath == "":
            return
        self.__model.outpath = outpath
        self.__view.log(f'Output path set to "{outpath}"')

    def proc_ocr_evt(self, ocr: bool) -> None:
        """
        Process the metadata OCR event.

        Args:
            ocr (bool): True if metadata OCR has been selected False if not.
        """
        self.__model.ocr = ocr

    def proc_interpolate_evt(self, interpolation: Optional[int]) -> None:
        """
        Process the interpolation event.

        Args:
            interpolation (Optional[int]): Number of total observation to interpolate.
                If None no interpolation will be applied.
        """
        self.__model.interpolation = interpolation

    def proc_ecg_selected_evt(self, idx: int) -> None:
        """
        Process the ECG selected event. Load that ECG in the view.

        Args:
            idx (int): Index of the ECG selected.
        """
        if self.__model.ecg_paths is None:
            return
        self.__model.selected_ecg_idx = idx
        self.__model.signals_highlighted = False
        self.__view.set_highlight(False)
        ecg = self.__model.ecg_paths[self.__model.selected_ecg_idx]
        img = self.__load_img(ecg)
        self.__view.load_ecg(img)
        self.__view.set_ecg_counter(idx + 1, len(self.__model.ecg_paths))

    def proc_browse_evt(self, paths: Iterable[str]) -> None:
        """
        Process the browse ECG event. Load the first ECG and also enable all settings
        and actions.
        Args:
            paths (Iterable[str]): _description_
        """
        if not len(paths):
            return
        self.__total_time = 0
        self.__model.ecg_paths = paths
        self.__model.selected_ecg_idx = 0
        self.__view.set_ecg_selector(
            [realpath(ecg).split(sep)[-1] for ecg in self.__model.ecg_paths]
        )
        self.__view.enable_settings(True)
        self.__view.enable_ecg_selector(True)
        self.__view.enable_outpath(True)
        self.__view.enable_digitize(True)
        self.__view.enable_highlight(True)
        self.__view.enable_cancel(True)
        self.__view.enable_ecg_counter(True)
        self.__view.set_ecg_counter(1, len(self.__model.ecg_paths))
        self.__view.set_progress(0)
        self.__view.log(f"{len(self.__model.ecg_paths)} images loaded")
        path = self.__model.ecg_paths[self.__model.selected_ecg_idx]
        self.proc_outpath_evt(dirname(path))
        img = self.__load_img(path)
        self.__view.load_ecg(img)

    def proc_digitize_evt(self) -> None:
        """
        Process the digitize event with the selected configuration.
        """
        total_paths = self.__model.ecg_paths
        self.__model.digitizing = True
        self.__view.enable_progress(True)
        # Disable settings, browse and cancel
        self.__view.enable_digitize(False)
        self.__view.enable_settings(False)
        self.__view.enable_browse(False)
        # ThreadPool
        pool = QThreadPool.globalInstance()
        self.__active_threads = max(1, pool.maxThreadCount() - 1)
        # Split pending ECG in a partition
        pending_paths = np.array(
            [
                (i, path)
                for i, path in enumerate(total_paths)
                if not self.__model.is_digitized(i)
            ],
            dtype=object,
        )
        split = np.array_split(pending_paths, self.__active_threads)
        self.__view.log(f"STARTING DIGITIZATION of {len(total_paths)} files")
        self.__ini_time = time.time()
        for i in range(self.__active_threads):
            miner = Digitizer(
                layout=self.__model.layout,
                rhythm=self.__model.rhythm,
                rp_at_right=self.__model.rp_at_right,
                cabrera=self.__model.cabrera,
                outpath=self.__model.outpath,
                ocr=self.__model.ocr,
                interpolation=self.__model.interpolation,
            )
            is_digitizing = lambda: self.__model.digitizing
            worker = Thread(miner, split[i], is_digitizing)
            worker.finished_connect(self.finished_callback)
            worker.progress_connect(self.progress_callback)
            worker.error_connect(self.error_callback)
            pool.start(worker)

    def finished_callback(self) -> None:
        """
        Callback for a thread when it has finished.
        """
        self.__active_threads -= 1
        if self.__model.progress == 100:
            self.__view.log(
                f"FINISHED DIGITIZATION of {len(self.__model.ecg_paths)} files "
                + f"({round(time.time() - self.__ini_time,2)} s)"
            )
        if self.__active_threads == 0:
            self.__view.enable_browse(True)
            self.__view.enable_cancel(False)

    def progress_callback(self, idx: int, msg: str) -> None:
        """
        Callback for a thread to report its progress.
        """
        self.__model.set_digitized(idx)
        self.__view.log(msg)
        self.__view.set_progress(self.__model.progress)

    def error_callback(self, idx: int, msg: str) -> None:
        """
        Callback for a thread when an error has ocurred.
        """
        self.__model.set_digitized(idx)
        self.__view.log(msg, error=True)
        self.__view.set_progress(self.__model.progress)

    def proc_highlight_evt(self) -> None:
        """
        Process the highlight signals event. If the current ECG has been digitized
        switch the visualize mode (highlight the leads or show the original image),
        otherwise report an error in the log.
        """
        sel_ecg = self.__model.ecg_paths[self.__model.selected_ecg_idx]
        path = (
            sel_ecg
            if self.__model.signals_highlighted
            else (
                self.__model.outpath
                + "/"
                + splitext(basename(sel_ecg))[0]
                + "_trace.png"
            )
        )
        img = self.__load_img(path)
        self.__view.load_ecg(img)
        if img is not None:
            self.__model.signals_highlighted = (
                not self.__model.signals_highlighted
            )
            self.__view.set_highlight(self.__model.signals_highlighted)

    def proc_cancel_evt(self, cancel: bool) -> None:
        """
        Process the cancel digitization event.

        Args:
            cancel (bool): True if current digitization will be cancelled False if not.
        """
        if not cancel:
            return
        self.__model.digitizing = False
        self.__model.ecg_paths = None
        self.__model.selected_ecg_idx = None
        self.__ini_time = None
        self.__view.enable_browse(True)
        self.__view.enable_cancel(False)
        self.__view.log(
            f"Waiting for the completion of the ongoing processes to cancel the remaining digitizations..."
        )
