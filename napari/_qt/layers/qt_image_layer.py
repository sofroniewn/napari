from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QLabel,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QSlider,
)
from .qt_image_base_layer import QtBaseImageControls, QtBaseImageDialog
from ...layers.image._constants import Interpolation, Rendering


arg_2_check_state = {
    False: Qt.Unchecked,
    None: Qt.PartiallyChecked,
    True: Qt.Checked,
}
check_state_2_arg = {
    Qt.Unchecked: False,
    Qt.PartiallyChecked: None,
    Qt.Checked: True,
}


class QtImageControls(QtBaseImageControls):
    def __init__(self, layer):
        super().__init__(layer)

        self.layer.events.interpolation.connect(self._on_interpolation_change)
        self.layer.events.rendering.connect(self._on_rendering_change)
        self.layer.events.iso_threshold.connect(self._on_iso_threshold_change)
        self.layer.dims.events.ndisplay.connect(self._on_ndisplay_change)

        interp_comboBox = QComboBox()
        for interp in Interpolation:
            interp_comboBox.addItem(str(interp))
        index = interp_comboBox.findText(
            self.layer.interpolation, Qt.MatchFixedString
        )
        interp_comboBox.setCurrentIndex(index)
        interp_comboBox.activated[str].connect(
            lambda text=interp_comboBox: self.changeInterpolation(text)
        )
        self.interpComboBox = interp_comboBox
        self.interpLabel = QLabel('interpolation:')

        renderComboBox = QComboBox()
        for render in Rendering:
            renderComboBox.addItem(str(render))
        index = renderComboBox.findText(
            self.layer.rendering, Qt.MatchFixedString
        )
        renderComboBox.setCurrentIndex(index)
        renderComboBox.activated[str].connect(
            lambda text=renderComboBox: self.changeRendering(text)
        )
        self.renderComboBox = renderComboBox
        self.renderLabel = QLabel('rendering:')

        sld = QSlider(Qt.Horizontal)
        sld.setFocusPolicy(Qt.NoFocus)
        sld.setMinimum(0)
        sld.setMaximum(100)
        sld.setSingleStep(1)
        sld.setValue(self.layer.iso_threshold * 100)
        sld.valueChanged[int].connect(
            lambda value=sld: self.changeIsoTheshold(value)
        )
        self.isoThesholdSilder = sld
        self.isoThesholdLabel = QLabel('iso threshold:')
        self._on_ndisplay_change(None)

        # grid_layout created in QtLayerControls
        # addWidget(widget, row, column, [row_span, column_span])
        self.grid_layout.addWidget(QLabel('opacity:'), 0, 0, 1, 3)
        self.grid_layout.addWidget(self.opacitySilder, 0, 3, 1, 4)
        self.grid_layout.addWidget(QLabel('contrast limits:'), 1, 0, 1, 3)
        self.grid_layout.addWidget(self.contrastLimitsSlider, 1, 3, 1, 4)
        self.grid_layout.addWidget(QLabel('gamma:'), 2, 0, 1, 3)
        self.grid_layout.addWidget(self.gammaSlider, 2, 3, 1, 4)
        self.grid_layout.addWidget(self.isoThesholdLabel, 3, 0, 1, 3)
        self.grid_layout.addWidget(self.isoThesholdSilder, 3, 3, 1, 4)
        self.grid_layout.addWidget(QLabel('colormap:'), 4, 0, 1, 3)
        self.grid_layout.addWidget(self.colormapComboBox, 4, 3, 1, 3)
        self.grid_layout.addWidget(self.colorbarLabel, 4, 6)
        self.grid_layout.addWidget(QLabel('blending:'), 5, 0, 1, 3)
        self.grid_layout.addWidget(self.blendComboBox, 5, 3, 1, 4)
        self.grid_layout.addWidget(self.renderLabel, 6, 0, 1, 3)
        self.grid_layout.addWidget(self.renderComboBox, 6, 3, 1, 4)
        self.grid_layout.addWidget(self.interpLabel, 7, 0, 1, 3)
        self.grid_layout.addWidget(self.interpComboBox, 7, 3, 1, 4)
        self.grid_layout.setRowStretch(8, 1)
        self.grid_layout.setVerticalSpacing(4)

    def changeInterpolation(self, text):
        self.layer.interpolation = text

    def changeRendering(self, text):
        self.layer.rendering = text
        self._toggle_iso_threhold_visbility()

    def changeIsoTheshold(self, value):
        with self.layer.events.blocker(self._on_iso_threshold_change):
            self.layer.iso_threshold = value / 100

    def _on_iso_threshold_change(self, event):
        with self.layer.events.iso_threshold.blocker():
            self.isoThesholdSilder.setValue(self.layer.iso_threshold * 100)

    def _on_interpolation_change(self, event):
        with self.layer.events.interpolation.blocker():
            index = self.interpComboBox.findText(
                self.layer.interpolation, Qt.MatchFixedString
            )
            self.interpComboBox.setCurrentIndex(index)

    def _on_rendering_change(self, event):
        with self.layer.events.rendering.blocker():
            index = self.renderComboBox.findText(
                self.layer.rendering, Qt.MatchFixedString
            )
            self.renderComboBox.setCurrentIndex(index)
            self._toggle_iso_threhold_visbility()

    def _toggle_iso_threhold_visbility(self):
        rendering = self.layer.rendering
        if isinstance(rendering, str):
            rendering = Rendering(rendering)
        if rendering == Rendering.ISO:
            self.isoThesholdSilder.show()
            self.isoThesholdLabel.show()
        else:
            self.isoThesholdSilder.hide()
            self.isoThesholdLabel.hide()

    def _on_ndisplay_change(self, event):
        if self.layer.dims.ndisplay == 2:
            self.isoThesholdSilder.hide()
            self.isoThesholdLabel.hide()
            self.renderComboBox.hide()
            self.renderLabel.hide()
            self.interpComboBox.show()
            self.interpLabel.show()
        else:
            self.renderComboBox.show()
            self.renderLabel.show()
            self.interpComboBox.hide()
            self.interpLabel.hide()
            self._toggle_iso_threhold_visbility()


class QtImageDialog(QtBaseImageDialog):
    def __init__(self, layer):
        super().__init__(layer)

        self.channelAxisSpinBox = QSpinBox()
        self.channelAxisSpinBox.setToolTip('Channel axis')
        self.channelAxisSpinBox.setKeyboardTracking(False)
        self.channelAxisSpinBox.setSingleStep(1)
        self.channelAxisSpinBox.setMinimum(-2147483647)
        self.channelAxisSpinBox.setMaximum(2147483647)
        self.channelAxisSpinBox.setValue(0)
        self.channelAxisSpinBox.hide()

        self.channelAxisCheckBox = QCheckBox(self)
        self.channelAxisCheckBox.setToolTip('Set channel axis')
        self.channelAxisCheckBox.setChecked(False)
        self.channelAxisCheckBox.stateChanged.connect(
            self._on_channel_axis_change
        )

        self.contrastLimitsLowSpinBox = QDoubleSpinBox()
        self.contrastLimitsLowSpinBox.setToolTip('Contrast limits low value')
        self.contrastLimitsLowSpinBox.setKeyboardTracking(False)
        self.contrastLimitsLowSpinBox.setSingleStep(1)
        self.contrastLimitsLowSpinBox.setMinimum(-2147483647)
        self.contrastLimitsLowSpinBox.setMaximum(2147483647)
        self.contrastLimitsLowSpinBox.setValue(0.0)
        self.contrastLimitsLowSpinBox.hide()

        self.contrastLimitsHighSpinBox = QDoubleSpinBox()
        self.contrastLimitsHighSpinBox.setToolTip('Contrast limits high value')
        self.contrastLimitsHighSpinBox.setKeyboardTracking(False)
        self.contrastLimitsHighSpinBox.setSingleStep(1)
        self.contrastLimitsHighSpinBox.setMinimum(-2147483647)
        self.contrastLimitsHighSpinBox.setMaximum(2147483647)
        self.contrastLimitsHighSpinBox.setValue(1.0)
        self.contrastLimitsHighSpinBox.hide()

        self.contrastLimitsCheckBox = QCheckBox(self)
        self.contrastLimitsCheckBox.setToolTip('Set contrast limits')
        self.contrastLimitsCheckBox.setChecked(False)
        self.contrastLimitsCheckBox.stateChanged.connect(
            self._on_contrast_limits_change
        )

        self.pyramidCheckBox = QCheckBox(self)
        self.pyramidCheckBox.setToolTip('Is pyramid')
        self.pyramidCheckBox.setTristate(True)
        state = arg_2_check_state[self.parameters['is_pyramid'].default]
        self.pyramidCheckBox.setCheckState(state)

        self.rgbCheckBox = QCheckBox(self)
        self.rgbCheckBox.setToolTip('Is rgb')
        self.rgbCheckBox.setTristate(True)
        state = arg_2_check_state[self.parameters['rgb'].default]
        self.rgbCheckBox.setCheckState(state)

        self.grid_layout.addWidget(QLabel('name:'), 0, 0)
        self.grid_layout.addWidget(self.nameTextBox, 0, 1, 1, 3)
        self.grid_layout.addWidget(QLabel('visible:'), 1, 0)
        self.grid_layout.addWidget(self.visibleCheckBox, 1, 1)
        self.grid_layout.addWidget(QLabel('is_pyramid:'), 2, 0)
        self.grid_layout.addWidget(self.pyramidCheckBox, 2, 1)
        self.grid_layout.addWidget(QLabel('rgb:'), 3, 0)
        self.grid_layout.addWidget(self.rgbCheckBox, 3, 1)
        self.grid_layout.addWidget(QLabel('channel_axis:'), 4, 0)
        self.grid_layout.addWidget(self.channelAxisCheckBox, 4, 1)
        self.grid_layout.addWidget(self.channelAxisSpinBox, 4, 2, 1, 2)
        self.grid_layout.addWidget(QLabel('contrast_limits:'), 5, 0)
        self.grid_layout.addWidget(self.contrastLimitsCheckBox, 5, 1)
        self.grid_layout.addWidget(self.contrastLimitsLowSpinBox, 5, 2)
        self.grid_layout.addWidget(self.contrastLimitsHighSpinBox, 5, 3)

    def _on_channel_axis_change(self, event):
        state = self.channelAxisCheckBox.isChecked()
        if state:
            self.channelAxisSpinBox.show()
        else:
            self.channelAxisSpinBox.hide()

    def _on_contrast_limits_change(self, event):
        state = self.contrastLimitsCheckBox.isChecked()
        if state:
            self.contrastLimitsLowSpinBox.show()
            self.contrastLimitsHighSpinBox.show()
        else:
            self.contrastLimitsLowSpinBox.hide()
            self.contrastLimitsHighSpinBox.hide()

    def get_arguments(self):
        """Get keyword arguments for layer creation.

        Returns
        ---------
        arguments : dict
            Keyword arguments for layer creation.
        """
        base_arguments = self._base_arguments()
        is_pyramid = check_state_2_arg[self.pyramidCheckBox.checkState()]
        rgb = check_state_2_arg[self.rgbCheckBox.checkState()]

        if self.channelAxisCheckBox.isChecked():
            channel_axis = self.channelAxisSpinBox.value()
        else:
            channel_axis = None

        if self.contrastLimitsCheckBox.isChecked():
            contrast_limits = [
                self.contrastLimitsLowSpinBox.value(),
                self.contrastLimitsHighSpinBox.value(),
            ]
        else:
            contrast_limits = None

        arguments = {
            'is_pyramid': is_pyramid,
            'rgb': rgb,
            'channel_axis': channel_axis,
            'contrast_limits': contrast_limits,
        }
        arguments.update(base_arguments)

        return arguments
