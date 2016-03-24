from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.mpl_widget import MplWidget

class PyspeckitViewer(DataViewer):

    LABEL = "Pyspeckit data viewer"

    def __init__(self, session, parent=None):
        super(PyspeckitViewer, self).__init__(session, parent=parent)
        self._mpl_widget = MplWidget()
        self._mpl_axes = self._mpl_widget.canvas.fig.add_subplot(1,1,1)
        self.setCentralWidget(self._mpl_widget)

    def add_data(self, data):
        return True
    