def setup():
    from .data_viewer import PyspeckitViewer
    from glue.config import qt_client
    qt_client.add(PyspeckitViewer)