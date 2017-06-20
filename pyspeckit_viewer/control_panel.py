import os

from glue.logger import logger as log

from qtpy import QtCore, QtWidgets

from glue.utils import nonpartial
from glue.utils.qt import load_ui, update_combobox, get_qapp
from glue.utils.qt.widget_properties import (CurrentTabProperty, TextProperty,
                                             CurrentComboTextProperty)

# TODO: rename default_Registry to default_registry
from pyspeckit.spectrum.fitters import default_Registry


class ControlPanel(QtWidgets.QWidget):

    modeChanged = QtCore.Signal(object)
    fitEvent = QtCore.Signal(object)
    subtractEvent = QtCore.Signal(object)

    tab_name = CurrentTabProperty('ui.tab_mode')

    log_line = TextProperty('ui.text_line')
    log_cont = TextProperty('ui.text_cont')

    line_fitter = CurrentComboTextProperty('ui.combo_line_fitters')
    cont_fitter = CurrentComboTextProperty('ui.combo_cont_fitters')

    def __init__(self, parent=None):

        super(ControlPanel, self).__init__(parent=parent)

        self.ui = load_ui('control_panel.ui', self,
                          directory=os.path.dirname(__file__))

        # Set up tabs

        self.ui.tab_mode.currentChanged.connect(nonpartial(self._mode_changed))
        self.ui.tab_mode.currentChanged.connect(nonpartial(self._update_buttons))

        # Set up radio buttons

        self._line_mode = QtWidgets.QButtonGroup()
        self._line_mode.addButton(self.ui.radio_line_panzoom)
        self._line_mode.addButton(self.ui.radio_line_identify)
        self._line_mode.addButton(self.ui.radio_line_select)
        self._line_mode.addButton(self.ui.radio_line_keyboard)

        self.ui.radio_line_panzoom.setChecked(True)

        self._line_mode.buttonClicked.connect(nonpartial(self._mode_changed))

        self._cont_mode = QtWidgets.QButtonGroup()
        self._cont_mode.addButton(self.ui.radio_cont_panzoom)
        self._cont_mode.addButton(self.ui.radio_cont_select)
        self._cont_mode.addButton(self.ui.radio_cont_exclude)
        self._line_mode.addButton(self.ui.radio_cont_keyboard)

        self.ui.radio_cont_panzoom.setChecked(True)

        self._cont_mode.buttonClicked.connect(nonpartial(self._mode_changed))

        # Set up combo box

        labels = list(default_Registry.multifitters.items())
        update_combobox(self.ui.combo_line_fitters, labels)

        self.ui.combo_cont_fitters.setEnabled(False)

        # Set up buttons

        self.ui.button_fit.clicked.connect(nonpartial(self._fit))
        self.ui.button_subtract.clicked.connect(nonpartial(self._subtract))

        # Ensure consistent state

        self._update_buttons()

    def _update_buttons(self):
        self.ui.button_subtract.setEnabled(self.tab_name == "Fit Continuum")

    def _mode_changed(self):
        self.modeChanged.emit(self.mode)

    def _fit(self):
        self.fitEvent.emit(self.mode)

    def _subtract(self):
        self.subtractEvent.emit(self.mode)

    @property
    def mode(self):
        if self.tab_name == "Fit Line":
            return self._line_mode.checkedButton().objectName().replace('radio_', '')
        else:
            return self._cont_mode.checkedButton().objectName().replace('radio_', '')


if __name__ == "__main__":

    log.setLevel("DEBUG")

    app = get_qapp()

    control = ControlPanel()

    def notify(mode):
        log.debug("Setting mode to '{0}' in pyspeckit control panel".format(mode))

    control.modeChanged.connect(notify)

    def notify_fit(mode):
        log.debug("Fitting in '{0}' mode in pyspeckit".format(mode))

    control.fitEvent.connect(notify_fit)

    def notify_subtract(mode):
        log.debug("Subtracting in '{0}' mode in pyspeckit".format(mode))

    control.subtractEvent.connect(notify_subtract)

    control.show()
    control.raise_()

    app.exec_()
