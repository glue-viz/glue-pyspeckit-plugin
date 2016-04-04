import pyspeckit_viewer
from pyspeckit_viewer.data_viewer import PyspeckitViewer

from glue.core import DataCollection, Session
from glue.core.data_factories import load_data
data = load_data('gbt_1d.fits')
data_collection = DataCollection([data])
hub = data_collection.hub
session = Session(data_collection=data_collection, hub=hub)

from glue.external.qt import get_qapp

app = get_qapp()

viewer = PyspeckitViewer(session)
viewer.show()
viewer.raise_()

viewer.add_data(data)

app.exec_()
