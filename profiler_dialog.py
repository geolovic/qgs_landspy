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

try:
    from qgis.core import QgsVectorLayer, QgsField, QgsProject, QgsFeature, QgsGeometry, QgsPoint, QgsPointXY
    from qgis.core import QgsCategorizedSymbolRenderer, QgsMarkerSymbol, QgsRendererCategory
except:
    print("No qgis module")

import sys
import os
import math
from osgeo import ogr, osr
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavToolBar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from landspy import Channel
from .dialogs import FigureGridDialog2


class ProfilerWindow(QMainWindow):
    
    window_closed = pyqtSignal()
    
    def __init__(self, parent=None, iface=None, app_path=""):

        # Init constructor with parent window
        super().__init__(parent)
        # Main window title
        self.setWindowTitle("Channel profiler")
        
        # Reference to QGIS interface (if running inside QGIS)
        self.iface = iface

        # Path to App
        self.app_path = app_path

        # Knickpoint types
        self.kp_types = {0 : {'ls':"", 'marker':"*", 'mec':"k", 'mew':0.5, 'mfc':"r", 'ms':10}, 
                         1 : {'ls':"", 'marker':"*", 'mec':"k", 'mew':0.5, 'mfc':"b", 'ms':10},
                         2 : {'ls':"", 'marker':"o", 'mec':"k", 'mew':0.5, 'mfc':"g", 'ms':6},
                         3 : {'ls':"", 'marker':"o", 'mec':"k", 'mew':0.5, 'mfc':(1, 1, 0), 'ms':6}}
        self.kp_type = 0
        
        # Drawing modes
        self.mode = 1 # 1. Long. profile, 2. Chi profile, 3. Area-slope profile, 4. ksn profile
        
        # Flag to indicate if maintain x-y scale
        self.maintain_scale = False
        
        # Point capture modes
        self.pick_mode = 0 # 0. No piking points 1. Knickpoint, 2. Regression, 3. Dam remover
        self.pc_id = None # Identify canvas conexions
        
        # Aux variable for current regression
        self.current_regression = []

        # Temporal vector layers
        self.channelVl = None
        self.kpVl = None
        self.regVl = None
        
        # Channels variables
        self.channels = np.array([])
        self.n_channels = 0
        self.active_channel = None
        self.saved = True
        
        # Initialize GUI
        self.GUI()

    def _create_actions(self):
        """
        Función interna que crea QActions (botones y acciones para menu y toolbar)
        """
        # Next - Prev
        self.qa_previousChannel = QAction(QIcon(self.app_path + "icons/arrow-180.png"), "Previous", self)
        self.qa_nextChannel = QAction(QIcon(self.app_path + "icons/arrow-000.png"), "Next", self)

        # Graphic types
        self.qa_longProfile = QAction(QIcon(self.app_path + "icons/long_prof.ico"), "Longitudinal profile", self)
        self.qa_chiProfile = QAction(QIcon(self.app_path + "icons/chi_prof.ico"), "Chi profile", self)
        self.qa_asProfile = QAction(QIcon(self.app_path + "icons/loglog_prof.ico"), "Area-slope profile", self)
        self.qa_ksnProfile = QAction(QIcon(self.app_path + "icons/ksn_prof.ico"), "ksn profile", self)

        # Capture points modes
        self.qa_setKP = QAction(QIcon(self.app_path + "icons/flag.ico"), "Set knickpoint", self)
        self.qa_setRegression = QAction(QIcon(self.app_path + "icons/reg.ico"), "Set regression", self)
        self.qa_removeDam = QAction(QIcon(self.app_path + "icons/dam.ico"), "Remove dam", self)
        self.qa_setKP.setCheckable(True)
        self.qa_setRegression.setCheckable(True)
        self.qa_removeDam.setCheckable(True)

        # Number of points (for area-slope and ksn)
        self.qlbl_nPoint = QLabel("N Points:")
        self.qspin_nPoint = QSpinBox()
        self.qa_applyNpoint = QAction(QIcon(self.app_path + "icons/apply_icon.png"), "Apply", self)
        self.qspin_nPoint.setFocusPolicy(Qt.NoFocus)
        self.qspin_nPoint.setRange(1, 200)

        # Reset elevations
        self.qa_zReset = QAction(QIcon(self.app_path + "icons/arrow-circle.png"), "Reset Elevations", self)

        # File menu (Load, Save, Close)
        self.qa_loadChannels = QAction("Load channels", self)
        self.qa_saveChannels = QAction("Save channels", self)
        self.qa_close = QAction("Close", self)

        # Edit menu (Add Channel, Remove Channel, Save Channel)
        self.qa_addChannel = QAction("Add channel", self)
        self.qa_removeChannel = QAction("Remove channel", self)
        self.qa_saveChannel = QAction("Save channel", self)

        # Export menu (Export Data, Save Figure)
        self.qa_exportChannelData = QAction("Export channel data", self)
        self.qa_saveFig = QAction(QIcon(self.app_path + "icons/savefig.png"), "Save Figure", self)
        self.qa_saveFigs = QAction("Save figures", self)

        # Tools menu (Smooth channel, Delete knickpoints, Delete regressions)
        self.qa_smooth = QAction("Smooth channel", self)
        self.qa_deleteKP = QAction("Delete knickpoints", self)
        self.qa_deleteReg = QAction("Delete regressions", self)
        self.qa_setName = QAction("Change channel name", self)

        # ===============================================================================
        # Connect Actions and Buttons to functions

        # Next - Prev
        self.qa_previousChannel.triggered.connect(lambda x: self.nextProfile(-1))
        self.qa_nextChannel.triggered.connect(lambda x: self.nextProfile(1))

        # Graphic types
        self.qa_longProfile.triggered.connect(lambda x: self.changeProfileGraph(1))
        self.qa_chiProfile.triggered.connect(lambda x: self.changeProfileGraph(2))
        self.qa_asProfile.triggered.connect(lambda x: self.changeProfileGraph(3))
        self.qa_ksnProfile.triggered.connect(lambda x: self.changeProfileGraph(4))

        # Capture points modes
        self.qa_setKP.triggered.connect(self.setKP)
        self.qa_setRegression.triggered.connect(self.setRegression)
        self.qa_removeDam.triggered.connect(self.removeDam)

        # Number of points (for area-slope and ksn)
        self.qa_applyNpoint.triggered.connect(self.calculateGradients)

        # Load, Save, Remove, Add, SaveCurrent
        self.qa_loadChannels.triggered.connect(self.loadChannels)
        self.qa_saveChannels.triggered.connect(self.saveChannels)
        self.qa_close.triggered.connect(self.close)
        self.qa_removeChannel.triggered.connect(self.removeChannel)
        self.qa_addChannel.triggered.connect(self.loadChannel)
        self.qa_saveChannel.triggered.connect(self.saveChannel)

        # Export
        self.qa_exportChannelData.triggered.connect(self.exportChannelData)
        self.qa_saveFig.triggered.connect(self.saveFigure)
        self.qa_saveFigs.triggered.connect(self.saveFigures)

        # Tools
        self.qa_zReset.triggered.connect(self.zReset)
        self.qa_setName.triggered.connect(self.setName)
        self.qa_smooth.triggered.connect(self.smoothElevations)

    def _create_toolbar(self):
        """
        Función interna para crear la barra de herramientas principal de Aplicación
        """
        # Creamos barra de herramientas
        toolbar = QToolBar("Action toolbar", self)
        toolbar.setIconSize(QSize(23, 23))
        self.addToolBar(toolbar)

        # Add Navigation toolbar and create references to the buttoms we want to maintain ("Home", "Pan", "Zoom")
        navtoolbar = NavToolBar(self.canvas, self)
        for action in navtoolbar.actions():
            if action.text() == "Home":
                self.qa_Home = action
            elif action.text() == "Pan":
                self.qa_Pan = action
            elif action.text() == "Zoom":
                self.qa_Zoom = action
            else:
                navtoolbar.removeAction(action)
        toolbar.addWidget(navtoolbar)

        # Add all the other buttons
        toolbar.addAction(self.qa_previousChannel)
        toolbar.addAction(self.qa_nextChannel)
        toolbar.addAction(self.qa_longProfile)
        toolbar.addAction(self.qa_chiProfile)
        toolbar.addAction(self.qa_asProfile)
        toolbar.addAction(self.qa_ksnProfile)
        toolbar.addAction(self.qa_setKP)
        toolbar.addAction(self.qa_setRegression)
        toolbar.addAction(self.qa_removeDam)
        toolbar.addWidget(self.qlbl_nPoint)
        toolbar.addWidget(self.qspin_nPoint)
        toolbar.addAction(self.qa_applyNpoint)
        toolbar.addAction(self.qa_zReset)
        toolbar.addAction(self.qa_saveFig)
        toolbar.setStyleSheet("QToolBar{spacing:2px;}")

        # Connect buttosn Zoom, Pan and Home
        self.qa_Pan.changed.connect(self.panChanged)
        self.qa_Zoom.changed.connect(self.zoomChanged)
        self.qa_Home.triggered.connect(self.home)

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
        filemenu.addAction(self.qa_loadChannels)
        filemenu.addAction(self.qa_saveChannels)
        filemenu.addAction(self.qa_close)
        editmenu.addAction(self.qa_addChannel)
        editmenu.addAction(self.qa_removeChannel)
        editmenu.addAction(self.qa_saveChannel)
        exportmenu.addAction(self.qa_exportChannelData)
        exportmenu.addAction(self.qa_saveFig)
        exportmenu.addAction(self.qa_saveFigs)
        toolsmenu.addAction(self.qa_smooth)
        toolsmenu.addAction(self.qa_deleteKP)
        toolsmenu.addAction(self.qa_deleteReg)
        toolsmenu.addAction(self.qa_zReset)
        toolsmenu.addAction(self.qa_setName)

    def _update_buttons(self):
        """
        This function update buttons (activate-deactivate) according the kind of profile being drawing
        """
        # Longitudinal profile
        if self.mode == 1:
            self.qa_setRegression.setEnabled(False)
            self.qa_removeDam.setEnabled(True)
            self.qspin_nPoint.setValue(self.qspin_nPoint.minimum())
            self.qspin_nPoint.setEnabled(False)
            self.qa_applyNpoint.setEnabled(False)

        # Chi profile
        elif self.mode == 2:
            self.qa_setRegression.setEnabled(True)
            self.qa_removeDam.setEnabled(True)
            self.qspin_nPoint.setValue(self.qspin_nPoint.minimum())
            self.qspin_nPoint.setEnabled(False)
            self.qa_applyNpoint.setEnabled(False)

        # Area-slope profile
        elif self.mode == 3:
            self.qa_setRegression.setEnabled(False)
            self.qa_removeDam.setEnabled(False)

            self.qspin_nPoint.setEnabled(True)
            if self.n_channels > 0:
                self.qspin_nPoint.setValue(self.channels[self.active_channel]._slp_np)
            else:
                self.qspin_nPoint.setValue(self.qspin_nPoint.minimum())

            self.qa_applyNpoint.setEnabled(True)

        # ksn profile
        elif self.mode == 4:
            self.qa_setRegression.setEnabled(False)
            self.qa_removeDam.setEnabled(False)

            self.qspin_nPoint.setEnabled(True)
            if self.n_channels > 0:
                self.qspin_nPoint.setValue(self.channels[self.active_channel]._ksn_np)
            else:
                self.qspin_nPoint.setValue(self.qspin_nPoint.minimum())

            self.qa_applyNpoint.setEnabled(True)

        # Restart self.regression list
        self.current_regression = []

    def _update_checked_buttons(self, button):
        # Only one button can be checked at time. This function "uncheck" all buttons except the
        # button passed as argument

        buttons = [self.qa_setKP, self.qa_setRegression, self.qa_removeDam, self.qa_Zoom, self.qa_Pan]

        if button in buttons:
            buttons.remove(button)

        for btn in buttons:
            if btn.isChecked():
                btn.trigger()

    def GUI(self):
        """
        This function creates the Graphic User Interface (buttons and actions)
        """
        # Create a FigureCanvas widget to show a matplotlib graphic
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim((0, 100))
        self.ax.set_ylim((0, 100))
       
        #  Set the FigureCanvas as the central Widget and modify its size
        self.setCentralWidget(self.canvas)
        self.resize(750, 550)
        
        # Create Status Bar
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        
        # Create QActions
        self._create_actions()
        
        # Add ToolBar
        self._create_toolbar()
        
        # Add Menu
        self._create_menu()
        
        # Show window
        self.show()

    def loadChannels(self):
        """
        Load a channels file into the App. 
        """
        dlg = QFileDialog(self)
        name = dlg.getOpenFileName(self, "Load channels")[0]
        mess = "Error loading channels!"
        
        if not name:
            return
        #try:
        channels = np.load(name, allow_pickle=True)
        canal = channels[0]

        # Check if array contains Channels instances
        if type(canal) is not Channel:
            mess = "Empty channel file!"
            raise TypeError

        # Check if all channels have the same crs
        proj = canal.getCRS()
        for canal in channels:
            if canal.getCRS() != proj:
                mess = "Channels have different coordinate systems"
                raise TypeError

        # Set channels, n_channels and active channel
        self.channels = channels
        self.n_channels = len(channels)
        self.active_channel = 0

        # If running inside QGIS, update temporary layers, before to draw
        if self.iface:
            # Update temporary layers
            for vl in [self.channelVl, self.kpVl, self.regVl]:
                if vl:
                    QgsProject.instance().removeMapLayer(vl)

            self.createRegLayer()
            self.updateRegLayer()
            self.createChannelLayer()
            self.updateChannelLayer()
            self.createKPLayer()
            self.updateKPLayer()

        # Change to profile graph 1 and draw
            self.changeProfileGraph(1)
            self.saved = True

        # except:
        #     msg = QMessageBox(parent=self)
        #     msg.setIcon(QMessageBox.Critical)
        #     msg.setText(mess)
        #     msg.setWindowTitle("Error")
        #     msg.show()
    
    def saveChannels(self):
        """
        Save channels as a numpy array
        """
        # Check if App has channels
        if self.n_channels == 0:
            return
        
        dlg = QFileDialog(self)
        name = dlg.getSaveFileName(self, "Save channels")[0]
        if not name:
            return
        try:
            np.save(name, self.channels, allow_pickle=True)
            self.saved = True
        except:
            msg = QMessageBox(parent=self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error saving channels")
            msg.setWindowTitle("Error")
            msg.show()
    
    def loadChannel(self):
        """
        Loads a channel (.dat file) into the App
        """
        dlg = QFileDialog(self)
        name = dlg.getOpenFileName(self, "Load channel")[0]
        mensaje = "Error loading channel"

        if not name:
            return
        try:
            canal = Channel(name)

            # Check if id of the channel already exists
            id_list = [canal.getOid() for canal in self.channels]
            if canal.getOid() in id_list:
                max_id = max(id_list)
                canal._oid = max_id + 1

            # Add channel to channel list
            self.channels = np.insert(self.channels, self.active_channel + 1, canal)
            self.n_channels = len(self.channels)
            self.active_channel += 1
            self.maintain_scale = False
            self._draw()

            if self.iface:
                # If running inside QGIS, update channel layer
                self.updateChannelLayer()
                self.saved = False

        except:
            msg = QMessageBox(parent=self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(mensaje)
            msg.setWindowTitle("Error")
            msg.show()

    def saveChannel(self):
        """
        Saves the current channel (.dat file)
        """
        # Saves current channel in the disk
        
        # Check if App has channels
        if self.n_channels == 0:
            return
        
        dlg = QFileDialog(self)
        name = dlg.getSaveFileName(self, "Save channel")[0]
        
        if not name:
            return
        try:
            # Get active channel       
            canal = self.channels[self.active_channel]
            canal.save(name)
        except:
            msg = QMessageBox(parent=self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error saving channel")
            msg.setWindowTitle("Error")
            msg.show()

    def removeChannel(self):
        """
        Removes the current channel from the App.
        """
        # Check if App has channels
        if self.n_channels == 0:
            return

        # Removes current channel (self.active_channel)
        if self.channels.size == 1:
            self.channels = np.array([])
            self.n_channels = 0
            self.active_channel = None
        else:
            self.channels = np.delete(self.channels, self.active_channel)
            self.n_channels -= 1
            self.active_channel += 1
            self.active_channel = self.active_channel % self.n_channels

        if self.iface:
            # If running inside QGIS, update layers
            self.updateChannelLayer()
            self.updateKPLayer()
            self.updateRegLayer()

        self.maintain_scale = False
        self.saved = False
        self._draw()

    def saveFigure(self):
        """
        Saves the current figure to the disk in raster or vector format
        """
        # Check if App has channels
        if self.n_channels == 0:
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

    def saveFigures(self):
        # Check if App has channels
        if self.n_channels == 0:
            return

        dlg = FigureGridDialog2()
        if dlg.exec():
            # Get parameters from Properties Dialog
            nrow = dlg.row_spin.value()
            ncol = dlg.col_spin.value()
            graph_type = dlg.combo.currentText()
            modes = {"Longitudinal profile": 1, "Chi profile": 2, "Area-slope profile": 3, "ksn profile": 4}
            mode = modes.get(graph_type, 1)

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
            n_sheets = math.ceil(self.n_channels / (nrow * ncol))
            idf = 0

            for m in range(n_sheets):
                # By default, A4 size
                fig = plt.figure(figsize=(8.2, 11.6))
                for n in range(1, nrow * ncol + 1):
                    ax = fig.add_subplot(nrow, ncol, n)
                    canal = self.channels[idf]
                    self._draw_graph(ax, canal, mode, showtitle=False)

                    # Remove labels from Y axis except for the first graphic of each row
                    if idf % ncol:
                        ax.set_yticklabels([])
                        ax.set_ylabel("")

                    idf += 1
                    if idf >= self.n_channels:
                        break
                plt.tight_layout()
                fig.savefig("{}_{:02d}{}".format(f_name, m, extension))
            QMessageBox.about(self, "Profiler", "Figure/s saved successfully")

    def createKPLayer(self):
        """
        This functions creates a temporary point layer for Knickpoints and Add it to the map

        Returns
        -------
        None.

        """
        # Get crs
        wkt = self.channels[0].getCRS()
        uri = "point?crs=" + wkt
        
        # Create new Vector layer in "memory"
        vl = QgsVectorLayer(uri, "knickpoints", "memory")
        pr = vl.dataProvider()
        pr.addAttributes([QgsField("chid", QVariant.Int),
                          QgsField("id", QVariant.Int),
                          QgsField("ksn",  QVariant.Double),
                          QgsField("type", QVariant.Int)])
        vl.updateFields()

        # Create categorized symbology for the layer
        cat_render = QgsCategorizedSymbolRenderer()
        
        # Create symbols
        symb01 =  QgsMarkerSymbol.createSimple({'name':'star', 'color':'red', 'size':'3'})
        symb02 =  QgsMarkerSymbol.createSimple({'name':'star', 'color':'blue', 'size':'3'})
        symb03 =  QgsMarkerSymbol.createSimple({'name':'circle', 'color':'green', 'size':'1.5'})
        symb04 =  QgsMarkerSymbol.createSimple({'name':'circle', 'color':'yellow', 'size':'1.5'})
        
        # Create categories
        cat01 = QgsRendererCategory('0', symb01, 'Type 1')
        cat02 = QgsRendererCategory('1', symb02, 'Type 1')
        cat03 = QgsRendererCategory('2', symb03, 'Type 1')
        cat04 = QgsRendererCategory('3', symb04, 'Type 1')
        
        # Add Categories
        for cat in [cat01, cat02, cat03, cat04]:
            cat_render.addCategory(cat)
        
        # Select Category
        cat_render.setClassAttribute("type")
        
        # Apply renderer
        vl.setRenderer(cat_render)         
        
        # Add layer to TOC
        QgsProject.instance().addMapLayer(vl)
        self.kpVl = vl
        
    def createRegLayer(self):
        """
        This functions creates a temporary polyline layer for Knickpoints and Add it to the map

        Returns
        -------
        None.
        """
        
        # Get crs
        wkt = self.channels[0].getCRS()
        uri = "linestring?crs=" + wkt
        
        # Create new Vector layer in "memory"
        vl = QgsVectorLayer(uri, "regressions", "memory")
        pr = vl.dataProvider()
        pr.addAttributes([QgsField("chid", QVariant.Int),
                          QgsField("id", QVariant.Int),
                          QgsField("ksn",  QVariant.Double),
                          QgsField("r2", QVariant.Double)])
        vl.updateFields()
        QgsProject.instance().addMapLayer(vl)
        vl.renderer().symbol().setColor(QColor(47, 182, 53))
        vl.renderer().symbol().setWidth(0.4)
        self.regVl = vl    
    
    def createChannelLayer(self):
        """
        This functions creates a temporary polyline layer for channels and adds it to the map

        Returns
        -------
        None.
        """
        
        # Get crs
        wkt = self.channels[0].getCRS()
        uri = "linestring?crs=" + wkt
        
        # Create new Vector layer in "memory"
        vl = QgsVectorLayer(uri, "channels", "memory")
        pr = vl.dataProvider()
        pr.addAttributes([QgsField("name", QVariant.String),
                          QgsField("oid",  QVariant.Int),
                          QgsField("flow", QVariant.Int)])
        vl.updateFields()
        QgsProject.instance().addMapLayer(vl)
        vl.renderer().symbol().setColor(QColor(70, 130, 180))
        vl.renderer().symbol().setWidth(0.4)
        self.channelVl = vl
    
    def updateChannelLayer(self):
        """
        This functions updates a temporary polyline layer for channels.
        
        Returns
        -------
        None.
        """       
        # First delete all features
        pr = self.channelVl.dataProvider()
        listOfIds = [feat.id() for feat in self.channelVl.getFeatures()]
        pr.deleteFeatures(listOfIds)
        
        # Load all channels
        for canal in self.channels:
            # Attributes
            name = str(canal.getName())
            oid = int(canal.getOid())
            flow = int(canal.getFlow())
            
            # Geometry
            xy = canal.getXY()
            
            f = QgsFeature()
            point_list = [QgsPoint(row[0], row[1]) for row in xy]
            f.setGeometry(QgsGeometry.fromPolyline(point_list))
            f.setAttributes([name, oid, flow])
            pr.addFeature(f)
        
        self.channelVl.updateExtents()
        
        # Refresh canvas
        self.iface.mapCanvas().refresh()
        bbox = self.channelVl.extent()
        self.iface.mapCanvas().zoomToFeatureExtent(bbox)

    def updateKPLayer(self):
        """
        This functions updates a temporary point layer for knickpoints.
        
        Returns
        -------
        None.
        """
              
        # First delete all features
        pr = self.kpVl.dataProvider()
        listOfIds = [feat.id() for feat in self.kpVl.getFeatures()]
        pr.deleteFeatures(listOfIds)
        
        # Load all channels
        for canal in self.channels:
            for kp in canal._kp:
                chid = int(canal.getOid())
                tipo = int(kp[1])
                pos = int(kp[0])
                ksn = float(canal._ksn[pos])
                
                # Adds the feature to temporary layer
                pr = self.kpVl.dataProvider()
                xy = canal.getXY()[pos]
                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(xy[0], xy[1])))
                # chid = 0
                # pos = 0
                # ksn = 0.0
                # tipo = 0
                f.setAttributes([chid, pos, ksn, tipo])
                pr.addFeature(f)
        
        self.kpVl.updateExtents()
        self.kpVl.triggerRepaint()

    def updateRegLayer(self):
        """
        This functions updates a temporary polyline layer for regressions.
        
        Returns
        -------
        None.
        """
        
        # First delete all features
        pr = self.regVl.dataProvider()
        listOfIds = [feat.id() for feat in self.regVl.getFeatures()]
        pr.deleteFeatures(listOfIds)
        
        # Load all regressions
        for canal in self.channels:
            for reg in canal._regressions:
                pos1 = reg[1]
                pos2 = reg[2]
                ksn = float(reg[3][0])
                r2ksn = float(reg[4])
                chid = int(canal.getOid())
                idx = reg[0]
                ind = canal._ix[pos1:pos2]
                row, col = canal.indToCell(ind)
                xi, yi = canal.cellToXY(row, col)
                xy = np.array((xi, yi)).T
                
                f = QgsFeature()
                point_list = [QgsPoint(row[0], row[1]) for row in xy]
                f.setGeometry(QgsGeometry.fromPolyline(point_list))
                f.setAttributes([chid, idx, ksn, r2ksn])
                pr.addFeature(f)
        
        # Refresh
        self.iface.mapCanvas().refresh()
        self.regVl.updateExtents()
        self.regVl.triggerRepaint()
        
    def addKP(self, canal, pos, tipo):
        
        canal.addKP(pos, tipo)
        
        if self.iface:
            chid = int(canal.getOid())
            tipo = int(tipo)
            pos = int(pos)
            ksn = float(canal._ksn[pos])
            
            # Adds the feature to temporary layer
            pr = self.kpVl.dataProvider()
            xy = canal.getXY()[pos]
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(xy[0], xy[1])))
            f.setAttributes([chid, pos, ksn, tipo])
            pr.addFeature(f)
            self.kpVl.updateExtents()
            self.kpVl.triggerRepaint()
            self.saved = False
    
    def removeKP(self, canal, pos):
        canal.removeKP(pos)
        if self.iface:
            self.kpVl.removeSelection()
            self.kpVl.selectByExpression('"id" = {} and "chid" = {}'.format(pos, int(canal.getOid())))
            idxs = self.kpVl.selectedFeatureIds()
            pr = self.kpVl.dataProvider()
            pr.deleteFeatures(idxs)
            self.saved = False
            
    def addReg(self, canal, pos1, pos2):
        
        if pos2 < pos1:
            pos2, pos1 = pos1, pos2
            
        idx = canal.addRegression(pos1, pos2)
        
        if self.iface:
            try:
                reg = canal.getRegression(idx)
                pr = self.regVl.dataProvider()
                
                # Attributes
                ksn = float(reg[3][0])
                r2ksn = float(reg[4])
                chid = int(canal.getOid())
                
                # Geometry
                ind = canal._ix[pos1:pos2]
                row, col = canal.indToCell(ind)
                xi, yi = canal.cellToXY(row, col)
                xy = np.array((xi, yi)).T
                
                # Add Feature
                f = QgsFeature()
                point_list = [QgsPoint(row[0], row[1]) for row in xy]
                f.setGeometry(QgsGeometry.fromPolyline(point_list))
                f.setAttributes([chid, idx, ksn, r2ksn])
                pr.addFeature(f)
                
                # Update extents and repaint
                self.regVl.updateExtents()
                self.regVl.triggerRepaint()
                self.saved = False
                return True
            
            except:
                return False

    def removeReg(self, canal, ind):
        reg = canal.getRegression(ind)
        
        if reg :
            idx = reg[0]
            canal.removeRegression(idx)
            
        if self.iface:

            self.regVl.removeSelection()
            self.regVl.selectByExpression('"id" = {} and "chid" = {}'.format(idx, int(canal.getOid())))
            idxs = self.regVl.selectedFeatureIds()
            pr = self.regVl.dataProvider()
            pr.deleteFeatures(idxs)
            self.saved = False
   
    def exportChannelData(self):
        """
        Export current profile graph as 
        """
        # Check if App has channels
        if self.n_channels == 0:
            return
        
        dlg = QFileDialog(self)
        name = dlg.getSaveFileName(self, "Export current profile")[0]
        
        if not name:
            return
        
        try:
            # Export profile data    
            # Get active channel       
            canal = self.channels[self.active_channel]
            head = canal.getName() + "\n"
            
            if self.mode == 1: # Longitudinal profile
                xi = canal.getD()
                yi = canal.getZ()
                head += "d;z"
            
            elif self.mode == 2:  # Chi profile
                xi = canal.getChi()
                yi = canal.getZ()
                head += "thetaref = {}\n".format(canal._thetaref)
                head += "chi;z"
                
            elif self.mode == 3: # Area-slope profile
                xi= canal.getA(cells=False)
                yi = canal.getSlope()
                head += "area;slope"
            
            elif self.mode == 4:
                xi = canal.getD()
                yi = canal.getKsn()
                head += "d;ksn"
            
            np.savetxt(name, np.array([xi, yi]).T, delimiter=";", header=head)
                   
        except:
            msg = QMessageBox(parent=self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error exporting profile")
            msg.setWindowTitle("Error")
            msg.show()
    
    def pick_point(self, event):
        """
        Pick a point in the active profile 
        
        event : matplotlib picker event
        """
        # Check if App has channels (and take the active one)
        if self.n_channels > 0:
            canal = self.channels[self.active_channel]
        else:
            return
        
        # Get current axe x-y limits
        if self.maintain_scale:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
        
        # In the case that many points are picked (true if the profile has several points). Take the middle one.
        if len(event.ind) > 2:
            ind = (event.ind[-1] + event.ind[0]) // 2
        else:
            ind = event.ind[0]
            
        ind = int(ind)
        
         # If self.pick_mode == 1 --> Selecting Knickpoints
        if self.pick_mode == 1:
            # Left button >> Add knickpoint
            if event.mouseevent.button==1:
                self.addKP(canal, ind, self.kp_type)

            # Rigth button >> Remove knickpoint
            elif event.mouseevent.button==3:
                kps = canal._kp[:, 0]
                diffs = np.abs(kps - ind)
                min_kp = np.min(diffs)
                pos_min = np.argmin(diffs)
                if min_kp < 3:
                    ind_to_remove = kps[pos_min]
                    self.removeKP(canal, ind_to_remove)
                    
            # Middle button >> Change knickpoint type
            elif event.mouseevent.button==2:
                self.kp_type += 1
                self.kp_type = self.kp_type % 4
                self.statusBar.showMessage("Knickpoint selection ON - Knickpoint type: {}".format(self.kp_type))
        
        # If self.pick_mode == 2 --> Selecting regression
        elif self.pick_mode == 2:
            # Left button >> Add regression point
            if event.mouseevent.button==1:
                if len(self.current_regression) == 0:
                    # If current_regression list hasn't got any point, add the clicked point to list
                    # Draw the point into the Axe, refresh canvas and exit (without calling to self._draw)
                    self.current_regression.append(ind)
                    self.ax.plot(event.mouseevent.xdata, event.mouseevent.ydata, ls="", marker="+", ms=10)
                    
                    if self.maintain_scale:
                        self.ax.set_xlim(xlim)
                        self.ax.set_ylim(ylim)
                    self.canvas.draw()
                    return
                
                elif len(self.current_regression) == 1:
                    # If current_regression list has only one point, add the second to list and create regression
                    self.current_regression.append(ind)
                    self.addReg(canal, self.current_regression[0], self.current_regression[1])
                    self.current_regression = []
            
            # Right button >> Remove regression
            if event.mouseevent.button==3:
                self.removeReg(canal, ind)
                self.current_regression = []

        # If self.pick_mode == 3 --> Removing DAM
        elif self.pick_mode == 3:
            # Left button >> Add regression point
            if event.mouseevent.button==1:
                if len(self.current_regression) == 0:
                    # Si no hay ningun punto introducido
                    # Introducimos el punto, lo dibujamos y salimos sin llamar a self._draw()
                    self.current_regression.append(ind)
                    self.ax.plot(event.mouseevent.xdata, event.mouseevent.ydata, ls="", marker="+", ms=10)
                    if self.maintain_scale:
                        self.ax.set_xlim(xlim)
                        self.ax.set_ylim(ylim)
                    self.canvas.draw()
                    return
                
                elif len(self.current_regression) == 1:
                    # Si hay un punto introducido, añadimos la regresión
                    self.current_regression.append(ind)
                    self._remove_dam()
        
        self._draw()

    def _draw_graph(self, ax,  canal, mode, knickpoints=True, regressions=True, showtitle=True):
        """
        Private function to draw a channel into an Axe
        """
        title = ""
        if mode == 1:  # Longitudinal profile
            if showtitle:
                title = "Longitudinal profile"
            if canal.getName():
                title += "  [{}]".format(canal.getName())
            ax.set_title(title)
            ax.set_xlabel("Distance (m)")
            ax.set_ylabel("Elevation (m)")
            di = canal.getD()
            zi = canal.getZ()
            ax.plot(di, zi, c="k", lw=1.25, picker=True, pickradius=25)

            # Draw knickpoints
            if knickpoints and len(canal._kp) > 0:
                for k in canal._kp:
                    self.ax.plot(di[k[0]], zi[k[0]], **self.kp_types[k[1]])

        elif mode == 2:  # Chi profile
            if showtitle:
                title = "Chi profile ($\Theta$=0.45)"
            if canal.getName():
                title += "  [{}]".format(canal.getName())
            ax.set_title(title)
            ax.set_xlabel("$\chi$ (m)")
            ax.set_ylabel("Elevation (m)")
            chi = canal.getChi()
            zi = canal.getZ()
            ax.plot(chi, zi, c="k", lw=1.25, picker=True, pickradius=25)

            # Draw knickpoints
            if knickpoints and len(canal._kp) > 0:
                for k in canal._kp:
                    ax.plot(chi[k[0]], zi[k[0]], **self.kp_types[k[1]])

            # Draw regressions
            if regressions and len(canal._regressions) > 0:
                # Channel regressions are tuples (p1, p2, poli, R2)
                # p1, p2 >> positions of first and second point of the regression
                # poli >> Polinomial with the regression
                # R2 >> Determination coeficient of the regression
                for reg in canal._regressions:
                    chi1 = chi[reg[1]]
                    chi2 = chi[reg[2]]
                    poli = reg[3]
                    z1 = np.polyval(poli, chi1)
                    z2 = np.polyval(poli, chi2)

                    ax.plot([chi1, chi2], [z1, z2], c="r", ls="--", lw=1.5)

        elif mode == 3:  # Area-slope profile
            if showtitle:
                title = "Area-slope profile"
            if canal.getName():
                title += "  [{}]".format(canal.getName())
            ax.set_title(title)
            ax.set_xlabel("Area")
            ax.set_ylabel("Slope")

            # Remove the last vertex, ussually it will be a vertex in the receiver channel and can produce a fliying point
            ai = canal.getA(cells=False)[:-1]
            slp = canal.getSlope()[:-1]
            ax.plot(ai, slp, marker=".", ls="", color="k", mfc="k", ms=5, picker=True, pickradius=10)
            ax.set_xscale("log")
            ax.set_yscale("log")

            # Draw knickpoints
            if knickpoints and len(canal._kp) > 0:
                for k in canal._kp:
                    ax.plot(ai[k[0]], slp[k[0]], **self.kp_types[k[1]])

        elif mode == 4:  # ksn profile
            if showtitle:
                title = "Ksn profile"
            if canal.getName():
                title += "  [{}]".format(canal.getName())
            ax.set_title(title)
            ax.set_title(title)
            ax.set_xlabel("Distance (m)")
            ax.set_ylabel("ksn")
            di = canal.getD()
            ksn = canal.getKsn()
            ax.plot(di, ksn, c="k", lw=1.25, picker=True, pickradius=10)

            # Draw knickpoints
            if knickpoints and len(canal._kp) > 0:
                for k in canal._kp:
                    ax.plot(di[k[0]], ksn[k[0]], **self.kp_types[k[1]])

            # Draw regressions
            if regressions and len(canal._regressions) > 0:
                # Channel regressions are tuples (p1, p2, poli, R2)
                # p1, p2 >> positions of first and second point of the regression
                # poli >> Polinomial with the regression
                # R2 >> Determination coeficient of the regression
                for reg in canal._regressions:
                    ksn = reg[3][0]
                    d1 = di[reg[1]]
                    d2 = di[reg[2]]
                    ax.plot([d1, d2], [ksn, ksn], c="r", ls="--", lw=1.5)

    def _draw(self):
        # Function to draw the active channel in the current graphic mode (self.mode)
        
        # Get active channel
        if self.n_channels > 0:
            canal = self.channels[self.active_channel]
        else:
            return
        
        # Get current axe x-y limits
        if self.maintain_scale:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

        self.ax.clear()
        self._draw_graph(self.ax, canal, self.mode, True, True)

        if self.maintain_scale:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
        
        self.canvas.draw()
        self.maintain_scale = True

        # If run inside QGIS, select the active channel
        if self.iface:
            self.channelVl.removeSelection()
            id_channel = self.channels[self.active_channel].getOid()
            self.channelVl.selectByExpression('"oid"={}'.format(id_channel))

    def setKP(self):
        if self.qa_setKP.isChecked():
            self._update_checked_buttons(self.qa_setKP)
            self.pick_mode = 1 # Knickpoint selection on
            self.statusBar.showMessage("Knickpoint selection ON - Knickpoint type: {}".format(self.kp_type))
            self.pc_id = self.canvas.mpl_connect("pick_event", self.pick_point)
        else:
            self.statusBar.clearMessage()
            if self.pc_id:
                self.canvas.mpl_disconnect(self.pc_id)
            
    def setRegression(self):
        # Handler para boton de regressions
        if self.qa_setRegression.isChecked():
            self._update_checked_buttons(self.qa_setRegression)
            self.pick_mode = 2 # Regression selection on
            self.statusBar.showMessage("Regression mode ON")
            self.pc_id = self.canvas.mpl_connect("pick_event", self.pick_point)
            self.current_regression = []
    
        else:
            self.statusBar.clearMessage()
            self.current_regression = []
            if self.pc_id:
                self.canvas.mpl_disconnect(self.pc_id)
        
    def removeDam(self):
        # Remove dam handler
        if self.qa_removeDam.isChecked():
            self._update_checked_buttons(self.qa_removeDam)
            self.pick_mode = 3 # Regression selection on
            self.statusBar.showMessage("Dam-remover mode ON")
            self.pc_id = self.canvas.mpl_connect("pick_event", self.pick_point)
            self.current_regression = []

        else:
            self.statusBar.clearMessage()
            self.current_regression = []
            if self.pc_id:
                self.canvas.mpl_disconnect(self.pc_id)
            
    def zoomChanged(self):
        if self.qa_Zoom.isChecked():
            self._update_checked_buttons(self.qa_Zoom)
            
    def panChanged(self):
        if self.qa_Pan.isChecked():
            self._update_checked_buttons(self.qa_Pan)
            
    def home(self):
        self.maintain_scale = False
        self._draw()

    def _remove_dam(self):
        # If self.current_regression hasn't got two points, return
        if len(self.current_regression) != 2:
            self.current_regression = []
            return
        
        canal = self.channels[self.active_channel]
        
        # Get the picked array indexes
        ind1, ind2 = self.current_regression
        
        # If ind2 < ind1 (change indexes)
        if ind2 < ind1:
            ind2, ind1 = ind1, ind2
            
        # Get two points depending on graph mode (self.mode)
        if self.mode == 1: # Long profile
            p1 = [canal._dx[ind1], canal._zx[ind1]]
            p2 = [canal._dx[ind2], canal._zx[ind2]]
        elif self.mode == 2: # Chi profile
            p1 = [canal._chi[ind1], canal._zx[ind1]]
            p2 = [canal._chi[ind2], canal._zx[ind2]]
        
        # Calculate straight line between the two points
        diff = p2[0] - p1[0]
        if diff == 0:
            diff = 0.0000001
        m = (p2[1] - p1[1]) / diff
        b = p1[1] - (m * p1[0])
        
        # Fill new xi and yi values
        if self.mode == 1:
            xi = canal._dx[ind1:ind2+1]
            yi = xi * m + b
            canal._zx[ind1:ind2+1] = yi     
            
        elif self.mode == 2:
            xi = canal._chi[ind1:ind2+1]
            yi = xi * m + b
            canal._zx[ind1:ind2+1] = yi
            
        # Recalculate gradients
        canal.calculateGradients(canal._slp_np, 'slp')
        canal.calculateGradients(canal._ksn_np, 'ksn')
        
        # Clear current_regression list and draw
        self.current_regression = []
        self.saved = False
        self._draw()

    def calculateGradients(self):
        # Handler to tb_button_refresh
        # Recalculates gradients of the active channel with specific number of points (npointsSpinBox)
        # Get active channel
        if self.n_channels > 0:
            canal = self.channels[self.active_channel]
        else:
            return

        n_points = self.qspin_nPoint.value()
        # If mode == 3, recalculate slope
        if self.mode == 3:
            canal.calculateGradients(n_points, 'slp')
        # If mode == 4, recalculate ksn
        elif self.mode == 4:
            canal.calculateGradients(n_points, 'ksn')

        self.saved = False
        self._draw()
        
    def nextProfile(self, direction):
        # Handler to tb_button_prev and tb_button_next buttons 
        # Select the next / previous channel of the channel list (self.channels)
        if self.n_channels == 0:
            return
        
        self.maintain_scale = False
        self.active_channel += direction
        self.active_channel = self.active_channel % self.n_channels
        self.current_regression = []
        self._update_buttons()
        self._draw()
        
    def changeProfileGraph(self, graph_number):
        # Changes the profile graph type and update buttons and options
        self.mode = graph_number
        self._update_buttons()
        self._update_checked_buttons(None)
        self.maintain_scale = False
        self._draw()

    def zReset(self):
        if self.n_channels == 0:
            return 
        
        qm = QMessageBox()
        res = qm.question(self, "Reset elevations", "Are you sure you want to reset channel elevations?.", qm.Yes|qm.No)
        if res == qm.No:
            return
        
        canal = self.channels[self.active_channel]
        canal._zx = np.copy(canal._zx0)
        
        # Recalculate gradients
        canal.calculateGradients(canal._slp_np, 'slp')
        canal.calculateGradients(canal._ksn_np, 'ksn')
        self.maintain_scale = False
        self.saved = False
        self._draw()
        
    def setName(self):
        # Get the active channel
        if self.n_channels > 0:
            canal = self.channels[self.active_channel]
        else:
            return

        # Show changename dialog
        text, ok = QInputDialog.getText(self, 'Profile Name', 'Set channel name:')
        if ok:
            canal.setName(str(text))
            self.saved = False
        self._draw()
        
    def smoothElevations(self):
        """
        Smooth channel elevations by applying a moving average
        """
        # Get active channel
        if self.n_channels > 0:
            canal = self.channels[self.active_channel]
        else:
            return
                
        # Show smooth channel dialog
        text, ok = QInputDialog.getText(self, 'Smooth Channel', 'Window size:')
        if ok:
            try:
                winsize = float(text)

            except:
                qm = QMessageBox()
                qm.critical(self, "Input error", "Wrong window size entered!")
                return
            canal.smoothChannel(winsize=winsize)

        self.maintain_scale = False
        self.saved = False
        self._draw()
       
    def closeEvent(self, event):
        """
        Exit from application, if changes were not saved, ask for saving.
        """
        if not self.saved:
            qm = QMessageBox()
            res = qm.question(self, "Exit profiler", "Are you sure you want to exit?\nUnsaved changes will be lost.", qm.Yes|qm.No)
            if res == qm.Yes:
                do_close = True
            else:
                do_close = False
        else:
            do_close = True

        if do_close:
            # Remove layers
            for vl in [self.channelVl, self.kpVl, self.regVl]:
                if vl:
                    QgsProject.instance().removeMapLayer(vl)
            # Refresh map canvas
            if self.iface:
                self.iface.mapCanvas().refresh()
            # Emit closing signal
            self.window_closed.emit()
            # Close window
            event.accept()
        else:
            # Do not close
            event.ignore()


def main():
    app = QApplication(sys.argv)
    win = ProfilerWindow(None, None)
    sys.exit(app.exec_())


if __name__ == "__main__":
        main()

