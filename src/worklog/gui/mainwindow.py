# MIT License
#
# Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import logging
from datetime import datetime, date, timedelta

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import qApp

from worklog.gui import trayicon
from worklog.gui.appwindow import AppWindow
from worklog.gui.dataobject import DataObject
from worklog.gui.datatypes import WorkLogData
from worklog.gui.widget.settingsdialog import SettingsDialog, AppSettings
from worklog.gui.widget.navcalendar import NavCalendarHighlightModel

from . import uiloader
from . import guistate


_LOGGER = logging.getLogger(__name__)


UiTargetClass, QtBaseClass = uiloader.load_ui_from_module_path( __file__ )


class MainWindow( QtBaseClass ):           # type: ignore

    appTitle = "Work Log"

    def __init__(self):
        super().__init__()
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.data = DataObject( self )
        self.appSettings = AppSettings()

        self.tickTimer = QtCore.QTimer( self )
        self.tickTimer.timeout.connect( self.handleTimerTick )
        self.tickTimer.start( 60 * 1000 )                           ## every minute

        ## =============================================================

        undoStack = self.data.undoStack

        undoAction = undoStack.createUndoAction( self, "&Undo" )
        undoAction.setShortcuts( QtGui.QKeySequence.Undo )
        redoAction = undoStack.createRedoAction( self, "&Redo" )
        redoAction.setShortcuts( QtGui.QKeySequence.Redo )

        self.ui.menuEdit.insertAction( self.ui.actionUndo, undoAction )
        self.ui.menuEdit.removeAction( self.ui.actionUndo )
        self.ui.menuEdit.insertAction( self.ui.actionRedo, redoAction )
        self.ui.menuEdit.removeAction( self.ui.actionRedo )

        self.ui.actionSave_data.triggered.connect( self.saveData )
        self.ui.actionOptions.triggered.connect( self.openSettingsDialog )

        ## =============================================================

        self.trayIcon = trayicon.TrayIcon(self)
        self._updateIconTheme( trayicon.TrayIconTheme.WHITE )

        self.ui.navcalendar.highlightModel = DataHighlightModel( self.data )

        ## ================== connecting signals ==================

        self.data.entryChanged.connect( self.ui.navcalendar.updateCells )
        self.data.entryChanged.connect( self.hideDetails )

        self.ui.navcalendar.currentPageChanged.connect( self.calendarPageChanged )
        self.ui.navcalendar.selectionChanged.connect( self.calendarSelectionChanged )
        self.ui.navcalendar.addEntry.connect( self.data.addEntry )

        self.ui.worklogTable.connectData( self.data )
        self.ui.worklogTable.selectedItem.connect( self.showDetails )
        self.ui.worklogTable.itemUnselected.connect( self.hideDetails )
        self.ui.dayListWidget.connectData( self.data )
        self.ui.dayListWidget.selectedEntry.connect( self.showDetails )
        self.ui.dayListWidget.entryUnselected.connect( self.hideDetails )

        self.ui.notesWidget.dataChanged.connect( self._handleNotesChange )

        self.applySettings()
        self.trayIcon.show()

        self.setWindowTitle()

        self.ui.navcalendar.setSelectedDate( date.today() )

        ## update table's filter
        selectedDate = self.ui.navcalendar.selectedDate()
        self.calendarPageChanged( selectedDate.year(), selectedDate.month() )
        self.calendarSelectionChanged()

        self.setStatusMessage( "Ready", timeout=10000 )

        ## for mainwindow example mostly
        QtCore.QTimer.singleShot( 1000, self.handleTimerTick )

    def loadData(self):
        """Load user related data (e.g. favs, notes)."""
        dataPath = self.getDataPath()
        self.data.load( dataPath )
        self.data.readFromKernlog()
        self.handleTimerTick()
        self.refreshView()

    def triggerSaveTimer(self):
        timeout = 30000
        _LOGGER.info("triggering save timer with timeout %s", timeout)
        QtCore.QTimer.singleShot( timeout, self.saveData )

    def saveData(self):
        if self._saveData():
            self.setStatusMessage( "Data saved" )
        else:
            self.setStatusMessage( "Nothing to save" )

    # pylint: disable=E0202
    def _saveData(self):
        ## having separate slot allows to monkey patch / mock "_saveData()" method
        _LOGGER.info( "storing data" )
        dataPath = self.getDataPath()
        self.data.notes = self.ui.notesWidget.getNotes()
        return self.data.store( dataPath )

    def disableSaving(self):
        def save_data_mock():
            _LOGGER.info("saving data is disabled")
        _LOGGER.info("disabling saving data")
        self._saveData = save_data_mock           # type: ignore

    def getDataPath(self):
        settings = self.getSettings()
        settingsDir = settings.fileName()
        settingsDir = settingsDir[0:-4]       ## remove extension
        settingsDir += "-data"
        return settingsDir

    def handleTimerTick(self):
        history = self.data.history
        recentEntry = history.recentEntry()
        if recentEntry is None:
            return
        currTime = datetime.today()
        timeDiff = currTime - recentEntry.endTime
        if timeDiff > timedelta( hours=2 ):
            return
        recentEntry.endTime = currTime
        self.ui.dayListWidget.update()

    ## ====================================================================

    def setWindowTitleSuffix( self, suffix="" ):
        if len(suffix) < 1:
            self.setWindowTitle( suffix )
            return
        newTitle = AppWindow.appTitle + " " + suffix
        self.setWindowTitle( newTitle )

    def setWindowTitle( self, newTitle="" ):
        if len(newTitle) < 1:
            newTitle = AppWindow.appTitle
        super().setWindowTitle( newTitle )
        if hasattr(self, 'trayIcon'):
            self.trayIcon.setToolTip( newTitle )

    def refreshView(self):
        self.ui.worklogTable.refreshData()
        self.ui.notesWidget.setNotes( self.data.notes )
        self.ui.dayListWidget.updateView()
        self.showDetails( None )

    def calendarPageChanged(self, year: int, month: int):
        self.ui.worklogTable.setMonth( year, month )

    def calendarSelectionChanged(self):
        self.ui.worklogTable.clearSelection()
        selectedDate = self.ui.navcalendar.selectedDate()
        dateValue = selectedDate.toPyDate()
        self.ui.dayListWidget.setCurrentDate( dateValue )

    def showDetails(self, entity):
        if entity is None:
            self.hideDetails()
            return
        entryDate = entity.startTime
        if entryDate is not None:
            entryDate = entryDate.date()
            self.ui.navcalendar.setSelectedDate( entryDate )
        self.ui.entrydetails.setObject( entity )
        self.ui.itemSW.setCurrentIndex( 1 )
        return

    def hideDetails(self):
        self.ui.itemSW.setCurrentIndex( 0 )

    ## ====================================================================

    def _handleNotesChange(self):
        self.triggerSaveTimer()

    ## ====================================================================

    def setStatusMessage(self, firstStatus, changeStatus: list=None, timeout=6000):
        if not changeStatus:
            changeStatus = [ firstStatus + " +", firstStatus + " =" ]
        statusBar = self.statusBar()
        message = statusBar.currentMessage()
        if message == firstStatus:
            statusBar.showMessage( changeStatus[0], timeout )
            return
        try:
            currIndex = changeStatus.index( message )
            nextIndex = ( currIndex + 1 ) % len(changeStatus)
            statusBar.showMessage( changeStatus[nextIndex], timeout )
        except ValueError:
            statusBar.showMessage( firstStatus, timeout )

    def setIconTheme(self, theme: trayicon.TrayIconTheme):
        _LOGGER.debug("setting tray theme: %r", theme)
        self._setTrayIndicator( theme )

    def _setTrayIndicator(self, theme: trayicon.TrayIconTheme):
        self._updateIconTheme( theme )

    def _updateIconTheme(self, theme: trayicon.TrayIconTheme):
        appIcon = trayicon.load_main_icon( theme )
        self.setWindowIcon( appIcon )
        self.trayIcon.setIcon( appIcon )

        ## update charts icon
        widgets = self.findChildren( AppWindow )
        for w in widgets:
            w.setWindowIcon( appIcon )

    def getIconTheme(self) -> trayicon.TrayIconTheme:
        return self.appSettings.trayIcon

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        _LOGGER.info("received close event, saving session: %s", qApp.isSavingSession() )
        if qApp.isSavingSession():
            ## closing application due to system shutdown
            self.saveAll()
            return
        ## windows close requested by user -- hide the window
        event.ignore()
        self.hide()
        self.trayIcon.show()

    def showEvent(self, _):
        self.trayIcon.updateLabel()

    def hideEvent(self, _):
        self.trayIcon.updateLabel()

    def setVisible(self, state):
        childrenWindows = self.findChildren( AppWindow )
        for w in childrenWindows:
            w.setVisible( state )
        super().setVisible( state )

    ## ====================================================================

    # pylint: disable=R0201
    def closeApplication(self):
        _LOGGER.info("received close request")
        ##self.close()
        qApp.quit()

    def saveAll(self):
        _LOGGER.info("saving application state")
        self.saveSettings()
        self.saveData()

    ## ====================================================================

    def openSettingsDialog(self):
        dialog = SettingsDialog( self.appSettings, self )
        dialog.setModal( True )
        dialog.iconThemeChanged.connect( self.setIconTheme )
        dialogCode = dialog.exec_()
        if dialogCode == QDialog.Rejected:
            self.applySettings()
            return
        self.appSettings = dialog.appSettings
        self.applySettings()

    def applySettings(self):
        self.setIconTheme( self.appSettings.trayIcon )

    def loadSettings(self):
        """Load Qt related settings (e.g. layouts, sizes)."""
        settings = self.getSettings()
        _LOGGER.debug( "loading app state from %s", settings.fileName() )

        self.appSettings.loadSettings( settings )

        self.applySettings()

        ## restore widget state and geometry
        guistate.load_state( self, settings )

    def saveSettings(self):
        settings = self.getSettings()
        _LOGGER.debug( "saving app state to %s", settings.fileName() )

        self.appSettings.saveSettings( settings )

        ## store widget state and geometry
        guistate.save_state(self, settings)

        ## force save to file
        settings.sync()

    def getSettings(self):
        ## store in home directory
        orgName = qApp.organizationName()
        appName = qApp.applicationName()
        settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, orgName, appName, self)
        return settings


class DataHighlightModel( NavCalendarHighlightModel ):

    def __init__(self, dataObject ):
        super().__init__()
        self.dataObject = dataObject

    def isHighlighted(self, dateValue: QtCore.QDate):
        return False

    def isOccupied(self, dateValue: QtCore.QDate):
        history: WorkLogData = self.dataObject.history
        entryDate = dateValue.toPyDate()
        entriesList = history.getEntriesForDate( entryDate )
        return len(entriesList) > 0
