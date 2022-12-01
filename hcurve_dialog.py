#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog to represent Hypsometric Curves (landspy.HCurve instances)
"""

# 1. Import sentences
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys, os
import math
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from landspy import HCurve
from dialogs import ColorRampDialog, FigureGridDialog


class HypsometricWindow(QMainWindow):
    
    window_closed = pyqtSignal()
    
    def __init__(self, parent=None, iface=None, app_path=""):

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

        # Display setting
        self.cmap = "RdYlBu"
        self.prop = "Id"

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
        self.qa_showLegend.setEnabled(False)

        # File menu (Load, Save, Close)
        self.qa_loadCurves = QAction("Load curves", self)
        self.qa_saveCurves = QAction("Save curves", self)
        self.qa_close = QAction("Close", self)
        self.qa_loadCurve = QAction("Add curve", self)
        self.qa_removeCurve = QAction("Remove curve", self)
        self.qa_saveCurve = QAction("Save curve", self)

        # Tools menu (Smooth channel, Delete knickpoints, Delete regressions)
        self.qa_displaySetting = QAction("Display settings", self)
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
        self.qa_displaySetting.triggered.connect(self.displaySetting)
        self.qa_setName.triggered.connect(self.setName)
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
        Private function to create the main menu
        """
        # Create empty menu bar and add different menus
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        editmenu = menubar.addMenu("&Edit")
        export_menu = menubar.addMenu("E&xport")
        tools_menu = menubar.addMenu("&Tools")
        
        # Add actions to menus
        file_menu.addAction(self.qa_loadCurves)
        file_menu.addAction(self.qa_saveCurves)
        file_menu.addAction(self.qa_close)
        editmenu.addAction(self.qa_loadCurve)
        editmenu.addAction(self.qa_removeCurve)
        editmenu.addAction(self.qa_saveCurve)
        export_menu.addAction(self.qa_saveFigure)
        export_menu.addAction(self.qa_saveFigures)
        tools_menu.addAction(self.qa_setName)
        tools_menu.addAction(self.qa_displaySetting)

    def _format_ax(self, grids=True):
        """
        Private function to format the main window Axe object
        """
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
        Removes the current hypsometric curve from the App.
        """
        # Check if App has channels
        if self.n_curves == 0:
            return

        # Removes current channel (self.active_channel)
        if self.curves.size == 1:
            # If the last curve is removed, empty the application
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
        """
        Saves the current figure to the disk in raster or vector format
        """
        # Check if App has channels
        if self.n_curves == 0:
            return

        file_filter = "Portable Network Graphic (*.png);;"
        file_filter += "PDF (*.pdf);;"
        file_filter += "Encapsulated PostScript File (*.eps);;"
        file_filter += "PostScript File (*.ps);;"
        file_filter += "Scalable Vector Graphics (*.svg)"

        url = QFileDialog.getSaveFileName(self, "Save Figure", "", file_filter)
        filename = url[0]
        if not filename:
            return
        self.fig.savefig(filename, dpi=400.)

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

        # If Show All button is checked; show all the curves
        if self.qa_showAll.isChecked():
            cmap = plt.get_cmap(self.cmap)
            props_id = ["HI", "Kurtosis", "Skewness", "Density Kurtosis", "Density Skewness"]
            # Get property values for the curves
            values = []
            if self.prop == "Id":
                values = list(range(self.n_curves))
            else:
                for curva in self.curves:
                    values.append(curva.moments[props_id.index(self.prop)])

            # Get maximum and minimum value (for the color ramp)
            maxvalue = max(values)
            minvalue = min(values)
            # Sort values
            positions = np.array(values).argsort()
            for n in positions:
                # Select curve
                curva = self.curves[n]
                # Get color from color ramp according property value
                if self.prop == "Id":
                    val = n
                    color = cmap(n / self.n_curves)
                else:
                    val = curva.moments[props_id.index(self.prop)]
                    color = cmap((val - minvalue) / (maxvalue-minvalue))

                # Labels for the legend. HI and other properties will have only 2 decimals
                if self.prop == "Id":
                    lbl = curva.getName() + " [{}]".format(val)
                else:
                    lbl = curva.getName() + " [{:.2f}]".format(val)

                # Plot curve, with corresponding color and label
                curva.plot(self.ax, c=color, label=lbl)
        else:
            # If not, simply draw the active hypsometric curve
            curva.plot(self.ax)
            self.ax.set_title(curva.getName())

        # Show legend if button is checked
        # If more than 17 curves in the plot, do not show legend
        if self.qa_showLegend.isChecked() and self.n_curves <= 17:
            self.ax.legend(loc='lower left', bbox_to_anchor=(1, -0.02), title=self.prop)

        # Show metrics in upper right corner if qa_showMetrics is checked
        if self.qa_showMetrics.isChecked():
            cadena = "HI: {0:.3f}\n".format(curva.getHI())
            cadena += "KU: {0:.3f}\n".format(curva.getKurtosis())
            cadena += "SW: {0:.3f}\n".format(curva.getSkewness())
            cadena += "DK: {0:.3f}\n".format(curva.getDensityKurtosis())
            cadena += "DS: {0:.3f}".format(curva.getDensitySkewness())
            self.ax.text(0.775, 0.97, cadena, size=11, verticalalignment="top")
        # Refresh canvas
        self.canvas.draw()

    def _showAll(self):
        if self.qa_showAll.isChecked():
            self.qa_showMetrics.setChecked(False)
            self.qa_showMetrics.setEnabled(False)
            self.qa_showLegend.setEnabled(True)
            self._draw()
        else:
            self.qa_showMetrics.setEnabled(True)
            self.qa_showLegend.setChecked(False)
            self.qa_showLegend.setEnabled(False)
            self._draw()

    def _showLegend(self):
        self._draw()

    def _showMetrics(self):
        self._draw()

    def displaySetting(self):
        # If no curves have been loaded, return
        if self.n_curves == 0:
            return
        # Show a Color Ramp Dialog
        dlg = ColorRampDialog()
        if dlg.exec() == 1:
            self.prop = dlg.prop_combo.currentText()
            self.cmap = plt.get_cmap(dlg.cmap_combo.currentText())
            if dlg.reversed.isChecked():
                self.cmap = self.cmap.reversed()

            self._draw()

    def nextCurve(self, direction):
        # Handler to tb_button_prev and tb_button_next buttons
        # Select the next / previous curve of the curve list (self.curves)
        if self.n_curves == 0 or self.qa_showAll.isChecked():
            return
        self.active_curve += direction
        self.active_curve = self.active_curve % self.n_curves
        self._draw(all_curves=False)
        
    def setName(self):
        if self.n_curves == 0 or self.qa_showAll.isChecked():
            return
        # Get active channel
        curve = self.curves[self.active_curve]
        # Show change_name dialog
        text, ok = QInputDialog.getText(self, 'Curve Name', 'Set Curve name:', text = curve.getName())
        # Change the name and draw
        if ok:
            curve.setName(str(text))
        self._draw()

    def closeEvent(self, event):
        # Emit closing signal
        self.window_closed.emit()
        # Close window
        event.accept()

    def saveFigures(self):
        # Check if App has channels
        if self.n_curves == 0:
            return
        # Create a simple dialog to choose nrows and ncols
        dlg = FigureGridDialog()

        if dlg.exec():
            nrow = dlg.row_spin.value()
            ncol = dlg.col_spin.value()
            grid = dlg.grid.isChecked()

            # Get the file name with a QFileDialog
            file_filter = "Portable Network Graphic (*.png);;"
            file_filter += "PDF (*.pdf);;"
            file_filter += "Encapsulated PostScript File (*.eps);;"
            file_filter += "PostScript File (*.ps);;"
            file_filter += "Scalable Vector Graphics (*.svg)"

            url = QFileDialog.getSaveFileName(self, "Save Figure", "", file_filter)
            filename = url[0]
            if not filename:
                return
            f_name, extension = os.path.splitext(filename)

            # Create the figure
            n_sheets = math.ceil(self.n_curves / (nrow * ncol))
            idf = 0
            for m in range(n_sheets):
                # By default, A4 size
                fig = plt.figure(figsize=(8.2, 11.6))
                for n in range(1, nrow * ncol + 1):
                    ax = fig.add_subplot(nrow, ncol, n)
                    curva = self.curves[idf]
                    curva.plot(ax)

                    # Format Axe
                    ax.set_xlim((0, 1))
                    ax.set_ylim((0, 1))
                    ax.set_xlabel("Relative area (a/A)")
                    ax.set_aspect("equal")
                    ax.set_title(curva.getName())
                    ax.set_ylabel("Relative elevation (h/H)")

                    # Show grid if was specified
                    if grid:
                        # Locators for X-Y axis and grid
                        ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
                        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
                        ax.grid(True, which='major', axis="both", linestyle="-", c="0.8", lw=0.75)

                    # Remove labels from Y axis except for the first graphic of each row
                    if idf % ncol:
                        ax.set_yticklabels([])
                        ax.set_ylabel("")

                    idf += 1
                    if idf >= self.n_curves:
                        break
                plt.tight_layout()
                fig.savefig("{}_{:02d}{}".format(f_name, m, extension))

def main():
    app = QApplication(sys.argv)
    # canales = np.load("canales.npy", allow_pickle=True)
    win = HypsometricWindow(None, None)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

