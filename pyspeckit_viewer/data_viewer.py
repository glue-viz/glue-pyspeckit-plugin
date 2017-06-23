from __future__ import absolute_import, print_function, division

import pyspeckit
import numpy as np
from astropy import units as u

from qtpy import QtWidgets
from qtpy.QtCore import Qt

from glue.logger import logger as log

from glue.core.roi import RectangularROI, XRangeROI
from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.mpl_widget import MplWidget
from glue.viewers.common.qt.mpl_toolbar import MatplotlibViewerToolbar
from glue.viewers.common.qt.mouse_mode import RectangleMode, HRangeMode
from glue.utils import nonpartial
from glue.config import viewer_tool

from .viewer_options import OptionsWidget
from .control_panel import ControlPanel


def apply_mode(mode):

    if mode.viewer.toolbar.mode in ('line_select', 'cont_select'):

        assert mode.viewer.spectrum.plotter._active_gui is not None, "No active GUI tool in pyspeckit"

        roi = mode.roi()

        log.info("ROI: {0}".format(roi))

        if isinstance(roi, RectangularROI):
            x1 = roi.xmin
            x2 = roi.xmax
        elif isinstance(roi, XRangeROI):
            x1 = roi.min
            x2 = roi.max
        if x1 > x2:
            x1, x2 = x2, x1

        mode.viewer.spectrum.plotter._active_gui.selectregion(xmin=x1,
                                                              xmax=x2,
                                                              highlight=True)


@viewer_tool
class PyspeckitRectangleMode(RectangleMode):
    tool_id = 'pyspeckit:rectangle'
    def __init__(self, *args, **kwargs):
        super(PyspeckitRectangleMode, self).__init__(*args, **kwargs)
        self._roi_callback = apply_mode


@viewer_tool
class PyspeckitHRangeMode(HRangeMode):
    tool_id = 'pyspeckit:hrange'
    def __init__(self, *args, **kwargs):
        super(PyspeckitHRangeMode, self).__init__(*args, **kwargs)
        self._roi_callback = apply_mode


class PyspeckitViewerToolbar(MatplotlibViewerToolbar):

    _custom_mode = ''

    @property
    def mode(self):
        if self._mpl_nav.mode == '':
            return self._custom_mode
        else:
            return self._mpl_nav.mode

    @mode.setter
    def mode(self, value):
        if value in self.tools:
            self._mpl_nav.mode = value
        else:
            self._custom_mode = value


class PyspeckitViewer(DataViewer):

    LABEL = "Pyspeckit data viewer"

    _toolbar_cls = PyspeckitViewerToolbar
    tools = ['pyspeckit:rectangle', 'pyspeckit:hrange']

    def __init__(self, session, parent=None):
        super(PyspeckitViewer, self).__init__(session, parent=parent)

        class Client(object):
            pass

        self.central_widget = MplWidget()
        self.client = Client()
        self.client.axes = self.central_widget.canvas.fig.add_subplot(1, 1, 1)

        self.central_widget = self.central_widget

        self._control_panel = ControlPanel()
        self._control_panel.modeChanged.connect(lambda mode: self.set_mode(init=True))
        self._control_panel.fitEvent.connect(nonpartial(self.run_fitter))
        self._control_panel.subtractEvent.connect(nonpartial(self.subtract))

        self._options_widget = OptionsWidget(data_viewer=self)

        self._splitter = QtWidgets.QSplitter()
        self._splitter.setOrientation(Qt.Horizontal)
        self._splitter.addWidget(self.central_widget)
        self._splitter.addWidget(self._control_panel)

        self.setCentralWidget(self._splitter)

        self.spectra = {}
        self.spectrum = None

    @property
    def mode(self):
        return self._control_panel.mode

    def set_mode(self, init=False):

        log.info("Setting mode={0} with init={1}".format(self.mode, init))

        # do not allow THIS to override "official" toolbar modes: we handle
        # those correctly already
        overwriteable_modes = ('line_panzoom', 'line_identify',
                               'line_select', 'cont_keyboard',
                               'cont_panzoom', 'cont_select',
                               'cont_exclude', 'line_keyboard', '')

        if self.mode.startswith('line'):
            if init:
                log.info("Activating fitter")
                self.spectrum.specfit.clear_all_connections()
                self.spectrum.plotter.activate_interactive_fitter()
                assert self.spectrum.plotter._active_gui is not None
            self.spectrum.specfit.debug = self.spectrum.specfit._debug = True
        elif self.mode.startswith('cont'):
            if init:
                log.info("Activating continuum fitter")
                self.spectrum.baseline.clear_all_connections()
                self.spectrum.plotter.activate_interactive_baseline_fitter(reset_selection=True)
                assert self.spectrum.plotter._active_gui is not None
            self.spectrum.baseline.debug = self.spectrum.baseline._debug = True
        else:
            raise NotImplementedError("Unknown mode: {0}".format(self.mode))

        if self.toolbar.mode in overwriteable_modes:
            self.toolbar.mode = self.mode
        log.info("Setting mode: {0}".format(self.mode))

    def run_fitter(self):
        if self.mode.startswith('line'):
            self.spectrum.specfit.button3action(None)
            self.spectrum.plotter.refresh()
        elif self.mode.startswith('cont'):
            self.spectrum.baseline.button3action(None)
            self.spectrum.plotter.refresh()

    def click_manager(self, event):
        """
        Pass events to the appropriate pyspeckit actions
        """
        if self.toolbar.mode in ('line_identify', 'line_select', 'cont_select', 'cont_exclude'):
            log.info("Toolbar: mode={0}".format(self.toolbar.mode))
            if self.mode == 'line_identify':
                self.spectrum.specfit.guesspeakwidth(event)
                self.spectrum.plotter.refresh()
            elif self.mode == 'line_select':
                self.spectrum.specfit._selectregion_interactive(event)
            elif self.mode == 'cont_select':
                self.spectrum.baseline._selectregion_interactive(event)
            elif self.mode == 'cont_exclude':
                self.spectrum.baseline._selectregion_interactive(event, mark_include=False)
            else:
                log.info("Not in line fitter mode, clicks do NOTHING.")
        else:
            log.info("Toolbar: mode={0}".format(self.toolbar.mode))


    def add_subset(self, subset):
        # a subset is a data object except it's not....
        self._options_widget.append(subset.data)
        self.set_new_data(subset.data, mask=subset.to_mask())

    def add_data(self, data):

        self._options_widget.append(data)

        # TODO: have a better way to query the unit in Glue Data objects

        # DO NOT use this hack IF pyspeckit version includes the fix that checks for 'number'
        #self.axes.figure.number = 1

        self.set_new_data(data)

        self.set_mode()

        return True

    def set_new_data(self, data, mask=None):

        log.info("Setting new data")
        if data.ndim == 3:
            x_comp_id = data.world_component_ids[0]
            xunit = data.coords.wcs.wcs.cunit[2]
            cubedata = data[self._options_widget.y_att]
            log.info('cubedata shape: {0}'.format(cubedata.shape))
            if mask is not None:
                cubedata = np.ma.masked_array(cubedata, ~mask)
                meandata = cubedata.mean(axis=2).mean(axis=1)
            else:
                meandata = np.nanmean(cubedata, axis=(1,2))
            log.info('meandata shape: {0}'.format(meandata.shape))
            ydata = meandata
            xdata = data[x_comp_id][:,0,0]
            log.info("xdata shape: {0}".format(xdata.shape))
            xdata = u.Quantity(xdata, xunit)
        elif data.ndim == 2:
            raise ValueError("can't handle images")
        elif data.ndim == 1:
            x_comp_id = data.world_component_ids[0]
            y_comp_id = self._options_widget.y_att
            xunit = data.coords.wcs.wcs.cunit[0]
            xdata = u.Quantity(data[x_comp_id], xunit)
            ydata = data[y_comp_id]
        else:
            raise ValueError("Data have {0} dimensions.  Only 1D and 3D data"
                             " are supported".format(data.ndim))

        self._options_widget.x_att = x_comp_id.label
        log.info("Done averaging or loading 1d")

        sp = pyspeckit.Spectrum(data=ydata, xarr=xdata)
        sp.plotter(axis=self.axes, clear=False, color=data.style.color)
        sp.plotter.figure.canvas.manager.toolbar = self.toolbar
        sp.plotter.axis.figure.canvas.mpl_connect('button_press_event',
                                                  self.click_manager)
        self.spectra[data] = sp
        self.spectrum = sp

        #else:
        #    # TODO: have a better way to query the unit in Glue Data objects

        #    self.spectrum.data = ydata
        #    self.spectrum.xarr = pyspeckit.units.SpectroscopicAxis(xdata)

        #    self.spectrum.plotter(clear=True)

    def options_widget(self):
        return self._options_widget

    def subtract(self):
        """
        Subtract off the fitted model.
        Baseline (continuum) has an 'unsubtract' feature;
        line fitting does not (by default).
        """
        if self.mode.startswith('line'):
            if hasattr(self.spectrum.specfit, 'subtracted') and self.spectrum.specfit.subtracted:
                self.spectrum.data += self._line_model
                self.spectrum.specfit.subtracted = False
            model = self.spectrum.specfit.get_full_model()
            self.spectrum.data -= model
            self._line_model = model
            self.spectrum.specfit.subtracted = True
        elif self.mode.startswith('cont'):
            if self.spectrum.baseline.subtracted:
                self.spectrum.baseline.unsubtract()
            model = self.spectrum.baseline.get_model()
            self.spectrum.data -= model
            self.spectrum.baseline.subtracted = True
