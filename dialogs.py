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


class FigureGridDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Figure Grid options")
        self.GUI()

    def GUI(self):
        # Create SpinBox to select number of rows and cols
        self.row_spin = QSpinBox(self)
        self.col_spin = QSpinBox(self)
        self.row_spin.setRange(1, 10)
        self.col_spin.setRange(1, 10)

        # Create a CheckBox to show grid or not
        self.grid = QCheckBox("Show grid lines", self)

        # Create a Form layout and populate rows
        layout = QFormLayout()
        layout.addRow("Rows:", self.row_spin)
        layout.addRow("Cols:", self.col_spin)
        layout.addRow("", self.grid)
        self.setLayout(layout)

        # Create button box and add it to layout
        q_btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonbox = QDialogButtonBox(q_btn)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)
        layout.addRow(buttonbox)

        self.show()


class FigureGridDialog2(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Figure Grid options")
        self.GUI()

    def GUI(self):
        # ComboBox to define type of graphic
        items = ["Longitudinal profile", "Chi profile", "Area-slope profile", "ksn profile"]
        self.combo = QComboBox(self)
        for item in items:
            self.combo.addItem(item)

        # SpinBoxes to select rows and cols
        self.row_spin = QSpinBox(self)
        self.col_spin = QSpinBox(self)
        self.row_spin.setRange(1, 10)
        self.col_spin.setRange(1, 10)

        # Create a Form layout and populate rows
        layout = QFormLayout()
        layout.addRow("Graphic type:", self.combo)
        layout.addRow("Rows:", self.row_spin)
        layout.addRow("Cols:", self.col_spin)
        self.setLayout(layout)

        # Create button box and add it to layout
        q_btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonbox = QDialogButtonBox(q_btn)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)
        layout.addRow(buttonbox)

        self.show()
