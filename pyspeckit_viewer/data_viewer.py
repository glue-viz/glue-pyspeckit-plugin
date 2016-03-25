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

        self._line_mode.buttonClicked.connect(nonpartial(lambda x: self.set_mode(init=True)))

        self._cont_mode = QtGui.QButtonGroup()
        self._cont_mode.addButton(self._control_panel.radio_cont_selection)
        self._cont_mode.addButton(self._control_panel.radio_cont_exclusion)

        self._cont_mode.buttonClicked.connect(nonpartial(lambda x: self.set_mode(init=True)))

        self._options_widget = OptionsWidget(data_viewer=self)

        self._splitter = QtGui.QSplitter()
        self._splitter.setOrientation(Qt.Horizontal)
        self._splitter.addWidget(self._mpl_widget)
        self._splitter.addWidget(self._control_panel)

        self.setCentralWidget(self._splitter)

        self.toolbar = self.make_toolbar()

        # nonpartial = wrapper that says don't pass additional arguments
        self._control_panel.tab_mode.currentChanged.connect(nonpartial(lambda x: self.set_mode(init=True)))
        #self._control_panel.button_line_identify.toggled.connect(nonpartial(self.set_click_mode))
        #self._control_panel.radio_button....toggled.connect(nonpartial(self.set_click_mode))
        self._control_panel.button_fit.clicked.connect(nonpartial(self.run_fitter))
        #self._control_panel.


    def set_mode(self, init=False):
        # do not allow THIS to override "official" toolbar modes: we handle those correctly already
        overwriteable_modes = ('line_identify', 'line_select', 'cont_select', 'cont_exclude', '')
        #from astropy import log
        #log.setLevel('DEBUG')
        if self.mode == 'Fit Line':
            if init:
                self.spectrum.specfit(interactive=True) # , print_message=False)
            self.spectrum.specfit.debug = self.spectrum.specfit._debug = True
            if self.line_identify:
                if self.toolbar.mode in overwriteable_modes:
                    self.toolbar.mode = 'line_identify'
                print("Identify mode")
            elif self.line_select:
                if self.toolbar.mode in overwriteable_modes:
                    self.toolbar.mode = 'line_select'
                print("Select mode")
        elif self.mode == 'Fit Continuum':
            if init:
                self.spectrum.baseline(interactive=True, reset_selection=True) # , print_message=False)
            self.spectrum.baseline.debug = self.spectrum.baseline._debug = True
            if self.cont_select:
                if self.toolbar.mode in overwriteable_modes:
                    self.toolbar.mode = 'cont_select'
                print("Select mode")
            elif self.cont_exclude:
                if self.toolbar.mode in overwriteable_modes:
                    self.toolbar.mode = 'cont_exclude'
                print("Exclude mode")

        else:
            raise NotImplementedError("Unknown mode: {0}".format(self.mode))

    #def set_click_mode(self):
    #    assert self.mode == 'Fit Line'
    #    self.click_mode = 'Peak/Width Identification'

    def run_fitter(self):
        if self.mode == 'Fit Line':
            self.spectrum.specfit.button3action(None)
            self.spectrum.plotter.refresh()
        elif self.mode == 'Fit Continuum':
            self.spectrum.baseline.button3action(None)
            self.spectrum.plotter.refresh()

    def click_manager(self, event):
        """
        Pass events to the appropriate pyspeckit actions
        """
        if self.toolbar.mode in ('line_identify', 'line_select', 'cont_select', 'cont_exclude'):
            print("Toolbar: mode={0}".format(self.toolbar.mode))
            if self.line_identify:
                self.spectrum.specfit.guesspeakwidth(event)
                self.spectrum.plotter.refresh()
            elif self.line_select and self.mode == 'Fit Line':
                self.spectrum.specfit.selectregion_interactive(event)
            elif self.cont_select:
                self.spectrum.baseline.selectregion_interactive(event)
            elif self.cont_exclude:
                self.spectrum.baseline.selectregion_interactive(event, mark_include=False)
            else:
                print("Not in line fitter mode, clicks do NOTHING.")
        else:
            print("Toolbar: mode={0}".format(self.toolbar.mode))


    def add_data(self, data):

        self._options_widget.append(data)

        x_comp_id = data.world_component_ids[0]
        self._options_widget.x_att = x_comp_id.label

        y_comp_id = self._options_widget.y_att[0]

        # TODO: have a better way to query the unit in Glue Data objects

        sp = pyspeckit.Spectrum(data=data[y_comp_id], xarr=data[x_comp_id] * data.coords.wcs.wcs.cunit[0])

        self.spectrum = sp

        # DO NOT use this hack IF pyspeckit version includes the fix that checks for 'number'
        #self._mpl_axes.figure.number = 1

        sp.plotter(axis=self._mpl_axes)
        self.spectrum.plotter.figure.canvas.manager.toolbar = self.toolbar

        self.spectrum.plotter.axis.figure.canvas.mpl_connect('button_press_event',
                                                             self.click_manager)
        self.set_mode()

        return True

    def _mouse_modes(self):
        axes = self._mpl_axes

        def apply_mode(mode):

            for key,val in iteritems(self.spectrum.plotter.figure.canvas.callbacks.callbacks['button_press_event']):
                if "event_manager" in val.func.__name__:
                    event_manager = val.func

            if self.line_select or self.cont_select:
                roi = mode.roi()
                print("ROI: ",roi)
                if isinstance(roi, RectangularROI):
                    x1 = roi.xmin
                    x2 = roi.xmax
                elif isinstance(roi, XRangeROI):
                    x1 = roi.min
                    x2 = roi.max
                if x1>x2:
                    x1,x2 = x2,x1
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
            mode.enabled.add_callback(nonpartial(self.set_mode))
        self.addToolBar(result)
        return result

    def options_widget(self):
        return self._options_widget
