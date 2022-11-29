#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de utilizacion de toolbar en Qt5

Para crear una toolbar en nuestra MainWindow y añadirla, simplemente utilizaremos
    toolbar = QToolBar("My main toolbar")
    self.addToolBar(toolbar)
        
"""

# 1. Import sentences
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sys
from osgeo import ogr, osr
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavToolBar
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import numpy as np
from landspy import HCurve


class HypsometricWindow(QMainWindow):
    
    window_closed = pyqtSignal()
    
    def __init__(self, parent=None, iface=None, app_path= ""):

        # Init constructor with a parent window
        super().__init__(parent)

        # Window title
        self.setWindowTitle("Hypsometric Curves")

        # App path
        self.app_path = app_path
        
        # Reference to QGIS interface (if running inside QGIS)
        self.iface = iface

        # Configure internal attributes
        # Show moments: 0: No moments, 1: Only HI, 2: All moments
        self.show_moments = 0

        # Hypsometric curve variables
        self.curves = np.array([])
        self.n_curves = 0
        self.active_curve = None
        
        # Initialize GUI
        self.GUI()
        
    def GUI(self):
        """
        This function creates the Graphic User Interface (buttons and actions)
        """
        # Figure Canvas Widget as central widget (to show the graphic)
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._format_ax()
       
        # Configure Canvas as central widget
        self.setCentralWidget(self.canvas)
        
        # Modify initial mainWindow size
        self.resize(750, 550)
        
        # Create Status Bar
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        
        # Create App actions (with a private function)
        self._create_actions()
        
        # Add Toolbar
        self._create_toolbar()
        
        # Add Menu
        self._create_menu()
        
        # Show window
        self.show()
    
    def _create_actions(self):
        """
        Private function that create QActions for menu and toolbar
        """
        # Next - Prev
        self.qa_previousCurve = QAction(QIcon(self.app_path + 'icons/arrow-180.png'), "Previous", self)
        self.qa_nextCurve = QAction(QIcon(self.app_path + "icons/arrow-000.png"), "Next", self)
        self.qa_showAll = QAction(QIcon(self.app_path + "icons/all_curves.ico"), "Show all curves", self)
        self.qa_showAll.setCheckable(True)
        
        # Show legend and metrics
        self.qa_showMetrics = QAction(QIcon(self.app_path + "icons/metrics.ico"), "Show Metrics", self)
        self.qa_showLegend = QAction(QIcon(self.app_path + "icons/primary_legend.ico"), "Show Legend", self)
        self.qa_showMetrics.setCheckable(True)
        self.qa_showLegend.setCheckable(True)

        # File menu (Load, Save, Close)
        self.qa_loadCurves = QAction("Load curves", self)
        self.qa_saveCurves = QAction("Save curves", self)
        self.qa_close = QAction("Close", self)
        self.qa_loadCurve = QAction("Add curve", self)
        self.qa_removeCurve = QAction("Remove curve", self)
        self.qa_saveCurve = QAction("Save curve", self)

        # Tools menu (Smooth channel, Delete knickpoints, Delete regressions)
        self.qa_colorRamp = QAction("Select color ramp", self)
        self.qa_saveFigure = QAction(QIcon(self.app_path + "icons/savefig.png"), "Save Figure", self)
        self.qa_saveFigures = QAction("Save Figures", self)
        self.qa_setName = QAction("Set Name", self)

        # ===============================================================================
        # Connect Actions and Buttons to functions
        # Next - Prev
        self.qa_previousCurve.triggered.connect(lambda x: self.nextCurve(-1))
        self.qa_nextCurve.triggered.connect(lambda x: self.nextCurve(1))
        self.qa_showAll.triggered.connect(self._showAll)

        # Show legend and metrics
        self.qa_showMetrics.triggered.connect(self._showMetrics)
        self.qa_showLegend.triggered.connect(self._showLegend)
        
        # Load, Save, Remove, Add, SaveCurrent
        self.qa_loadCurves.triggered.connect(self.loadCurves)
        self.qa_saveCurves.triggered.connect(self.saveCurves)
        self.qa_close.triggered.connect(self.close)
        self.qa_removeCurve.triggered.connect(self.removeCurve)
        self.qa_loadCurve.triggered.connect(self.loadCurve)
        self.qa_saveCurve.triggered.connect(self.saveCurve)
        
        # Tools
        self.qa_colorRamp.triggered.connect(self.setColorRamp)
        self.qa_saveFigure.triggered.connect(self.saveFigure)
        self.qa_saveFigures.triggered.connect(self.saveFigures)

    def _create_toolbar(self):
        """
        Private function to create the main Application toolBar
        """
        # Create ToolBar
        toolbar = QToolBar("Action toolbar", self)
        toolbar.setIconSize(QSize(23, 23))
        self.addToolBar(toolbar)

        # Add buttons
        toolbar.addAction(self.qa_previousCurve)
        toolbar.addAction(self.qa_nextCurve)
        toolbar.addAction(self.qa_showAll)
        toolbar.addAction(self.qa_showMetrics)
        toolbar.addAction(self.qa_showLegend)
        toolbar.addAction(self.qa_saveFigure)
        toolbar.setStyleSheet("QToolBar{spacing:2px;}")

    def _create_menu(self):
        """
        Función interna para crear el menú de la aplicación
        """
        # Create empty menu bar and add different menus
        menubar = self.menuBar()
        filemenu = menubar.addMenu("&File")
        editmenu = menubar.addMenu("&Edit")
        exportmenu = menubar.addMenu("E&xport")
        toolsmenu = menubar.addMenu("&Tools")
        
        # Add actions to menus
        filemenu.addAction(self.qa_loadCurves)
        filemenu.addAction(self.qa_saveCurves)
        filemenu.addAction(self.qa_close)
        editmenu.addAction(self.qa_loadCurve)
        editmenu.addAction(self.qa_removeCurve)
        editmenu.addAction(self.qa_saveCurve)
        exportmenu.addAction(self.qa_saveFigure)
        exportmenu.addAction(self.qa_saveFigures)
        toolsmenu.addAction(self.qa_setName)
        toolsmenu.addAction(self.qa_colorRamp)

        """
        Load a channels file into the App. 
        """
        pass

    def _format_ax(self, grids=True):
        # Function to format the Axe instance
        # Set limits (0-1) and labels for X-Y
        self.ax.set_xlim((0, 1))
        self.ax.set_ylim((0, 1))
        self.ax.set_xlabel("Relative area (a/A)")
        self.ax.set_ylabel("Relative elevation (h/H)")
        self.ax.set_aspect("equal")

        # Locators for X-Y axis and grid
        self.ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
        self.ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
        self.ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
        self.ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
        if grids:
            self.ax.grid(True, which='minor', axis="both", linestyle="--", c="0.4", lw=0.25)
            self.ax.grid(True, which='major', axis="both", linestyle="-", c="0.8", lw=0.75)

    def loadCurves(self):
        """
        This function load hypsometric curves into the App. Curves are loaded as a numpy array of HCurve objects
        """
        dlg = QFileDialog(self)
        file_filter = "Numpy array file (*.npy);;"
        file_filter += "All Files (*.*)"

        url = QFileDialog.getOpenFileName(self, "Load curves", "", file_filter)
        filename = url[0]
        if not filename:
            return
        mess = ""

        #try:
        curves = np.load(filename, allow_pickle=True)
        curve = curves[0]

        # Check if array contains HCurve instances
        if type(curve) is not HCurve:
            mess = "Cannot load Hypsometric curve, check the input file!"
            raise TypeError

        # Set curves, n_curves, and active_curve
        self.curves = curves
        self.n_curves = len(curves)
        self.active_curve = 0

        self._draw()

        # except:
        #     if not mess:
        #         mess = "Error loading hypsometric curves"
        #     msg = QMessageBox(parent=self)
        #     msg.setIcon(QMessageBox.Critical)
        #     msg.setText(mess)
        #     msg.setWindowTitle("Error")
        #     msg.show()

    def saveCurves(self):
        """
        Save channels as a numpy array
        """
        # Check if App has curves
        if self.n_curves == 0:
            return

        dlg = QFileDialog(self)
        file_filter = "Numpy array file (*.npy);;"
        file_filter += "All Files (*.*)"

        url = QFileDialog.getSaveFileName(self, "Save curves", "", file_filter)
        filename = url[0]
        if not filename:
            return

        try:
            np.save(filename, self.curves, allow_pickle=True)
        except:
            msg = QMessageBox(parent=self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error saving channels")
            msg.setWindowTitle("Error")
            msg.show()

    def removeCurve(self):
        """
        Removes the current channel from the App. 
        """
        # Check if App has channels
        if self.n_curves == 0:
            return

        # Removes current channel (self.active_channel)
        if self.curves.size == 1:
            self.curves = np.array([])
            self.n_curves = 0
            self.active_curve = None
            self.ax.clear()
            self._format_ax(grids=True)
            self.canvas.draw()
        else:
            self.curves = np.delete(self.curves, self.active_curve)
            self.n_curves -= 1
            self.active_curve += 1
            self.active_curve = self.active_curve % self.n_curves

        self._draw()

    def saveFigure(self):
        pass

    def saveCurve(self):
        """
        Saves the current curve (.dat file)
        """
        # Check if App has curves
        if self.n_curves == 0:
            return

        dlg = QFileDialog(self)
        file_filter = "Text file (*.txt);;"
        file_filter += "All Files (*.*)"

        url = QFileDialog.getSaveFileName(self, "Save curve", "", file_filter)
        filename = url[0]
        if not filename:
            return

        try:
            # Get active curve
            curve = self.curves[self.active_curve]
            curve.save(filename)

        except:
            msg = QMessageBox(parent=self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error saving Hypsometric curve")
            msg.setWindowTitle("Error")
            msg.show()
            
    def loadCurve(self):
        """
        Loads a hypsometric curve (.txt file) into the App
        """
        dlg = QFileDialog(self)
        file_filter = "Text file (*.txt);;"
        file_filter += "All Files (*.*)"

        url = QFileDialog.getOpenFileName(self, "Save curve", "", file_filter)
        filename = url[0]

        if not filename:
            return

        try:
            curve = HCurve(filename)
            # Add curve to curve list

            if self.curves.size == 0:
                self.curves = np.array([curve])
                self.active_curve = 0
                self.n_curves = 1
            else:
                self.curves = np.insert(self.curves, self.active_curve + 1, curve)
                self.n_curves = len(self.curves)
                self.active_curve += 1

            self._draw()

        except:
            msg = QMessageBox(parent=self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error loading Hypsometric Curve")
            msg.setWindowTitle("Error")
            msg.show()

    def _draw(self, all_curves=False, metrics=False, legend=False):
        # Function to draw the active channel in the current graphic mode (self.mode)
        # If there are no curves in the graph, exit function
        if self.n_curves > 0:
            curva = self.curves[self.active_curve]
        else:
            return

        # Clear the Axe
        self.ax.clear()
        self._format_ax(grids=True)

        if self.qa_showAll.isChecked():
            for curva in self.curves:
                curva.plot(self.ax)
        else:
            curva.plot(self.ax)
            self.ax.set_title(curva.getName())

        if self.qa_showLegend.isChecked():
            self.ax.legend(loc='lower left', bbox_to_anchor=(1, -0.02))

        if self.qa_showMetrics.isChecked():
            cadena = "HI: {0:.3f}\n".format(curva.getHI())
            cadena += "KU: {0:.3f}\n".format(curva.getKurtosis())
            cadena += "SW: {0:.3f}\n".format(curva.getSkewness())
            cadena += "DK: {0:.3f}\n".format(curva.getDensityKurtosis())
            cadena += "DS: {0:.3f}".format(curva.getDensitySkewness())
            self.ax.text(0.775, 0.97, cadena, size=11, verticalalignment="top")

        self.canvas.draw()

    def _showAll(self):
        if self.qa_showAll.isChecked():
            self.qa_showMetrics.setChecked(False)
            self.qa_showMetrics.setEnabled(False)
            self._draw()
        else:
            self.qa_showMetrics.setEnabled(True)
            self._draw()

    def _showLegend(self):
        self._draw()

    def _showMetrics(self):
        self._draw()

    def setColorRamp(self):
        pass

    
    def nextCurve(self, direction):
        # Handler to tb_button_prev and tb_button_next buttons
        # Select the next / previous curve of the curve list (self.curves)
        if self.n_curves == 0:
            return
        self.active_curve += direction
        self.active_curve = self.active_curve % self.n_curves
        self._draw(all_curves=False)
        
    def setName(self):
        # Get active channel
        if self.n_curves > 0:
            curve = self.curves[self.active_curve]
        else:
            return

        # Show changename dialog
        text, ok = QInputDialog.getText(self, 'Curve Name', 'Set Curve name:')
        if ok:
            curve.setName(str(text))

        self._draw()

    def closeEvent(self, event):
        # Emit closing signal
        self.window_closed.emit()
        # Close window
        event.accept()

    def saveFigures(self):
        pass
        # # Check if App has channels
        # if self.n_curves == 0:
        #     return
        #
        # dlg = QDialog(self)
        # dlg.setWindowTitle("Figure grid options")
        # layout = QFormLayout()
        # items = ["Longitudinal profile", "Chi profile", "Area-slope profile", "ksn profile"]
        # combo = QComboBox(dlg)
        # rowSpin = QSpinBox(dlg)
        # colSpin = QSpinBox(dlg)
        # rowSpin.setRange(1, 10)
        # colSpin.setRange(1, 10)
        # for item in items:
        #     combo.addItem(item)
        #
        # layout.addRow("Graphic type:", combo)
        # layout.addRow("Rows:", rowSpin)
        # layout.addRow("Cols:", colSpin)
        #
        # dlg.setLayout(layout)
        #
        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        #
        # buttonBox = QDialogButtonBox(QBtn)
        # buttonBox.accepted.connect(dlg.accept)
        # buttonBox.rejected.connect(dlg.reject)
        # layout.addRow(buttonBox)
        #
        # dlg.setLayout(layout)
        # dlg.show()
        # if dlg.exec():
        #     nrow = rowSpin.value()
        #     ncol = colSpin.value()
        #     print("Success! {} rows, {} columns".format(nrow, ncol))
        # else:
        #     print("Cancel!")

def main():
    app = QApplication(sys.argv)
    # canales = np.load("canales.npy", allow_pickle=True)
    win = HypsometricWindow(None, None)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

