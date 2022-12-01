#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Main window to try custom dialogs

        
"""

# 1. Import sentences
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sys
from osgeo import ogr, osr
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import numpy as np
from landspy import HCurve
from dialogs import ColorRampDialog
from dialogs import SaveImagesDialog

class TestWindow(QMainWindow):
    
    def __init__(self, parent=None):

        # Init constructor with a parent window
        super().__init__(parent)

        # Window title
        self.setWindowTitle("Test Window")
        self.setGeometry(100, 100, 300, 100)
        # Initialize GUI
        self.GUI()
        
    def GUI(self):
        """
        This function creates the Graphic User Interface (buttons and actions)
        """
        btn = QPushButton("Click ME!" ,self)
        btn.move(100, 30)
        btn.clicked.connect(self.show_dialog)
        self.show()

    def show_dialog(self):
        dlg = SaveImageDialog(self)
        if dlg.exec() == 1:
            print(dlg.reversed.isChecked(), dlg.cmap_combo.currentText(), dlg.prop_combo.currentText())

def main():
    app = QApplication(sys.argv)
    win = TestWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

