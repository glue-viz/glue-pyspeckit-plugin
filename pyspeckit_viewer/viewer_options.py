import os

from qtpy import QtWidgets

from glue.core.qt.data_combo_helper import ComponentIDComboHelper
from glue.utils.qt.widget_properties import CurrentComboProperty, TextProperty
from glue.utils.qt import load_ui

__all__ = ["OptionsWidget"]


class OptionsWidget(QtWidgets.QWidget):

    x_att = TextProperty('ui.text_x_attribute')
    y_att = CurrentComboProperty('ui.combo_y_attribute')

    def __init__(self, parent=None, data_viewer=None):

        super(OptionsWidget, self).__init__(parent=parent)

        self.ui = load_ui('viewer_options.ui', self,
                          directory=os.path.dirname(__file__))

        self.y_helper = ComponentIDComboHelper(self.ui.combo_y_attribute,
                                               data_viewer._data, categorical=False)

        self._data_viewer = data_viewer

        self._data = None

    def append(self, data):
        self.y_helper.append_data(data)

    def remove(self, data):
        self.y_helper.remove_data(data)
