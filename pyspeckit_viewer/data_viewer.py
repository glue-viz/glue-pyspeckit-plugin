from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.mpl_widget import MplWidget
from glue.viewers.common.qt.toolbar import GlueToolbar
from glue.core.roi import RectangularROI, XRangeROI
from glue.viewers.common.qt.mouse_mode import (RectangleMode, HRangeMode,)
from astropy.extern.six import iteritems
import pyspeckit
import matplotlib

class PyspeckitViewer(DataViewer):

    LABEL = "Pyspeckit data viewer"

    def __init__(self, session, parent=None):
        super(PyspeckitViewer, self).__init__(session, parent=parent)
        self._mpl_widget = MplWidget()
        self._mpl_axes = self._mpl_widget.canvas.fig.add_subplot(1,1,1)
        self.setCentralWidget(self._mpl_widget)

        self.toolbar = self.make_toolbar()

    def add_data(self, data):
        sp = pyspeckit.Spectrum(data=data['PRIMARY'],
                                # TODO: generalize the x-axis generation
                                xarr=data['Vrad']*data.coords.wcs.wcs.cunit[0])
                                #xarr=data[data.coords.wcs.wcs.ctype[0]]*data.coords.wcs.wcs.cunit[0])
        self.Spectrum = sp

        # DO NOT use this hack IF pyspeckit version includes the fix that checks for 'number'
        #self._mpl_axes.figure.number = 1

        sp.plotter(axis=self._mpl_axes)
        self.Spectrum.plotter.figure.canvas.manager.toolbar = self.toolbar

        return True

    def _mouse_modes(self):
        axes = self._mpl_axes

        def apply_mode(mode):

            for key,val in iteritems(self.Spectrum.plotter.figure.canvas.callbacks.callbacks['button_press_event']):
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
            canvas = self.Spectrum.plotter.figure.canvas
            m1 = matplotlib.backend_bases.MouseEvent('button_press_event', canvas, x1, y, button=1)
            m1.xdata = x1
            m1.ydata = y
            m2 = matplotlib.backend_bases.MouseEvent('button_press_event', canvas, x2, y, button=1)
            m2.xdata = x2
            m2.ydata = y

            event_manager(m1, force_over_toolbar=True)
            event_manager(m2, force_over_toolbar=True)
            print(mode.roi())

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
