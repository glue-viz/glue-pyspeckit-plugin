from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.mpl_widget import MplWidget
import pyspeckit

class PyspeckitViewer(DataViewer):

    LABEL = "Pyspeckit data viewer"

    def __init__(self, session, parent=None):
        super(PyspeckitViewer, self).__init__(session, parent=parent)
        self._mpl_widget = MplWidget()
        self._mpl_axes = self._mpl_widget.canvas.fig.add_subplot(1,1,1)
        self.setCentralWidget(self._mpl_widget)

    def add_data(self, data):
        sp = pyspeckit.Spectrum(data=data['PRIMARY'],
                                xarr=data['Vrad']*data.coords.wcs.wcs.cunit[0])
                                #xarr=data[data.coords.wcs.wcs.ctype[0]]*data.coords.wcs.wcs.cunit[0])

        self._mpl_axes.figure.number = 1
        sp.plotter(axis=self._mpl_axes)
        return True
