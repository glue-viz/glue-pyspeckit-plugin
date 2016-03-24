from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.mpl_widget import MplWidget
from glue.viewers.common.qt.toolbar import GlueToolbar
from glue.viewers.common.qt.mouse_mode import (RectangleMode, HRangeMode,
                                               VRangeMode)
import pyspeckit

class PyspeckitViewer(DataViewer):

    LABEL = "Pyspeckit data viewer"

    def __init__(self, session, parent=None):
        super(PyspeckitViewer, self).__init__(session, parent=parent)
        self._mpl_widget = MplWidget()
        self._mpl_axes = self._mpl_widget.canvas.fig.add_subplot(1,1,1)
        self.setCentralWidget(self._mpl_widget)

        tb = self.make_toolbar()

    def add_data(self, data):
        sp = pyspeckit.Spectrum(data=data['PRIMARY'],
                                # TODO: generalize the x-axis generation
                                xarr=data['Vrad']*data.coords.wcs.wcs.cunit[0])
                                #xarr=data[data.coords.wcs.wcs.ctype[0]]*data.coords.wcs.wcs.cunit[0])
        self.spectrum = sp

        # DO NOT use this hack IF pyspeckit version includes the fix that checks for 'number'
        #self._mpl_axes.figure.number = 1

        self.plotter = sp.plotter(axis=self._mpl_axes)

        return True

    def _mouse_modes(self):
        axes = self._mpl_axes

        def apply_mode(mode):
            print(mode.roi())

        rect = RectangleMode(axes, roi_callback=apply_mode)
        xra = HRangeMode(axes, roi_callback=apply_mode)
        yra = VRangeMode(axes, roi_callback=apply_mode)
        return [rect, xra, yra]

    def make_toolbar(self):
        result = GlueToolbar(self._mpl_widget.canvas, self,
                             name='pyspeckit Plot')
        for mode in self._mouse_modes():
            result.add_mode(mode)
        self.addToolBar(result)
        return result
