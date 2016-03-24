import os

import pyspeckit
import matplotlib

from glue.utils.qt import load_ui
from glue.external.qt.QtCore import Qt
from glue.external.qt import QtGui
from glue.external.six import iteritems

from glue.utils import nonpartial
from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.mpl_widget import MplWidget
from glue.viewers.common.qt.toolbar import GlueToolbar
from glue.core.roi import RectangularROI, XRangeROI
from glue.viewers.common.qt.mouse_mode import (RectangleMode, HRangeMode,)
from glue.utils.qt.widget_properties import CurrentTabProperty, ButtonProperty

from .viewer_options import OptionsWidget


class PyspeckitViewer(DataViewer):

    LABEL = "Pyspeckit data viewer"

    mode = CurrentTabProperty('_control_panel.tab_mode')

    line_identify = ButtonProperty('_control_panel.radio_line_peak')
    line_select = ButtonProperty('_control_panel.radio_line_selection')

    cont_select = ButtonProperty('_control_panel.radio_cont_selection')
    cont_exclude = ButtonProperty('_control_panel.radio_cont_exclusion')

    def __init__(self, session, parent=None):
        super(PyspeckitViewer, self).__init__(session, parent=parent)

        self._mpl_widget = MplWidget()
        self._mpl_axes = self._mpl_widget.canvas.fig.add_subplot(1,1,1)

        self._control_panel = load_ui('control_panel.ui', None,
                                directory=os.path.dirname(__file__))

        self._line_mode = QtGui.QButtonGroup()
        self._line_mode.addButton(self._control_panel.radio_line_peak)
        self._line_mode.addButton(self._control_panel.radio_line_selection)

        self._line_mode.buttonClicked.connect(nonpartial(self._update_line_mode))

        self._cont_mode = QtGui.QButtonGroup()
        self._cont_mode.addButton(self._control_panel.radio_cont_selection)
        self._cont_mode.addButton(self._control_panel.radio_cont_exclusion)

        self._cont_mode.buttonClicked.connect(nonpartial(self._update_cont_mode))

        self._options_widget = OptionsWidget(data_viewer=self)

        self._splitter = QtGui.QSplitter()
        self._splitter.setOrientation(Qt.Horizontal)
        self._splitter.addWidget(self._mpl_widget)
        self._splitter.addWidget(self._control_panel)

        self.setCentralWidget(self._splitter)

        self.toolbar = self.make_toolbar()

        self._control_panel.tab_mode.currentChanged.connect(nonpartial(self.set_mode))

    def _update_line_mode(self):
        if self.line_identify:
            print("Identify mode")
        elif self.line_select:
            print("Select mode")

    def _update_cont_mode(self):
        if self.cont_select:
            print("Select mode")
        elif self.cont_exclude:
            print("Exclude mode")

    def set_mode(self):
        if self.mode == 'Fit Line':
            self.spectrum.specfit(interactive=True)
        elif self.mode == 'Fit Continuum':
            self.spectrum.baseline(interactive=True, reset_selection=True)
        else:
            raise NotImplementedError("Unknown mode: {0}".format(self.mode))

    def add_data(self, data):

        self._options_widget.append(data)

        x_comp_id = data.world_component_ids[0]
        self._options_widget.x_att = x_comp_id.label

        y_comp_id = self._options_widget.y_att[0]

        # TODO: have a better way to query the unit in Glue Data objects

        sp = pyspeckit.Spectrum(data=data[y_comp_id], xarr=data[x_comp_id] * data.coords.wcs.wcs.cunit[0])

        self.spectrum = sp

        # DO NOT use this hack IF pyspeckit version includes the fix that checks for 'number'
        self._mpl_axes.figure.number = 1

        sp.plotter(axis=self._mpl_axes)
        self.spectrum.plotter.figure.canvas.manager.toolbar = self.toolbar

        return True

    def _mouse_modes(self):
        axes = self._mpl_axes

        def apply_mode(mode):

            for key,val in iteritems(self.spectrum.plotter.figure.canvas.callbacks.callbacks['button_press_event']):
                if "event_manager" in val.func.__name__:
                    event_manager = val.func

            roi = mode.roi()
            if isinstance(roi, RectangularROI):
                x1 = roi.xmin
                x2 = roi.xmax
            elif isinstance(roi, XRangeROI):
                x1 = roi.min
                x2 = roi.max
            y = 0
            canvas = self.spectrum.plotter.figure.canvas
            m1 = matplotlib.backend_bases.MouseEvent('button_press_event', canvas, x1, y, button=1)
            m1.xdata = x1
            m1.ydata = y
            m2 = matplotlib.backend_bases.MouseEvent('button_press_event', canvas, x2, y, button=1)
            m2.xdata = x2
            m2.ydata = y

            event_manager(m1, force_over_toolbar=True)
            event_manager(m2, force_over_toolbar=True)

        rect = RectangleMode(axes, roi_callback=apply_mode)
        xra = HRangeMode(axes, roi_callback=apply_mode)
        return [rect, xra,]

    def make_toolbar(self):
        result = GlueToolbar(self._mpl_widget.canvas, self,
                             name='pyspeckit Plot')

        #def disable_pyspeckit_callbacks(enable):
        #    if enable:
        #        # disable
        #    else:
        #        # re-enable...

        for mode in self._mouse_modes():
            result.add_mode(mode)
            #mode.enabled.add_callback(disable_pyspeckit_callbacks)
        self.addToolBar(result)
        return result

    def options_widget(self):
        return self._options_widget
