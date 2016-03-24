from glue.viewers.common.qt.data_viewer import DataViewer

class PyspeckitViewer(DataViewer):

    LABEL = "Pyspeckit data viewer"

    def __init__(self, session, parent=None):
        super(PyspeckitViewer, self).__init__(session, parent=parent)
        # self.setCentralWidget(my_qt_widget)

    def add_data(self, data):
        return True
    