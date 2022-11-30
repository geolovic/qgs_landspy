#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 Dialog and helper window classes
"""

# 1. Import sentences
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sys

class ColorRampDialog(QDialog):

    def __init__(self, parent=None, cm="RdYlBu", prop="Id"):
        super().__init__(parent)

        self.setWindowTitle("Color ramp selection")
        self.cm = cm
        self.prop = prop
        self.GUI()

    def GUI(self):
        layout = QFormLayout()
        ramp_items = ["RdYlBu", "Blues", "Greens", "Oranges", "Reds", "YlOrRd", "BrBG", "Spectral", "turbo"]
        prop_items = ["Id", "HI", "Kurtosis", "Skewness", "Density Kurtosis", "Density Skewness"]

        self.prop_combo = QComboBox(self)
        for item in prop_items:
            self.prop_combo.addItem(item)

        self.cmap_combo = QComboBox(self)
        for item in ramp_items:
            self.cmap_combo.addItem(item)

        self.reversed = QCheckBox("Invert Color Ramp", self )
        layout.addRow("Display:", self.prop_combo)
        layout.addRow("Color ramp:", self.cmap_combo)
        layout.addRow("", self.reversed)
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)
        self.show()