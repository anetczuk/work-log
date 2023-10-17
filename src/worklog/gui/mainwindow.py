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
from worklog.gui.datatypes import WorkLogData, WorkLogEntry
from worklog.gui.useractivity import UserActivity
from worklog.gui.widget.settingsdialog import SettingsDialog, AppSettings
from worklog.gui.widget.navcalendar import NavCalendarHighlightModel
from worklog.gui.widget import logwidget

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

        self.activity = UserActivity( self )

        self.tickTimer = QtCore.QTimer( self )
        self.tickTimer.timeout.connect( self.updateRecentEntry )
        self.tickTimer.start( 45 * 1000 )                           ## every 45 secs

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
        self.ui.actionLogs.triggered.connect( self.openLogsWindow )
        self.ui.actionOptions.triggered.connect( self.openSettingsDialog )

        ## =============================================================

        self.trayIcon = trayicon.TrayIcon(self)
        self.trayIcon.setWorkLogging( True )
        self.updateTrayToolTip()
        self._setTrayIndicator( trayicon.TrayIconTheme.WHITE )

        self.ui.navcalendar.highlightModel = DataHighlightModel( self.data )

        self.ui.worklogTable.connectData( self.data )
        self.ui.dayEntriesWidget.connectData( self.data )

        ## ================== connecting signals ==================

        self.data.entryChanged.connect( self.updateView )

        self.activity.sessionChanged.connect( self._sessionChanged )
        self.activity.ssaverChanged.connect( self._screenSaverChanged )

        self.trayIcon.workLoggingChanged.connect( self.switchWorkLogging )

        self.ui.navcalendar.currentPageChanged.connect( self.calendarPageChanged )
        self.ui.navcalendar.selectionChanged.connect( self.calendarSelectionChanged )
        self.ui.navcalendar.addEntry.connect( self.data.addEntry )

        self.ui.showWorkOnlyCB.stateChanged.connect( self._filterWorkEntries )

        self.ui.worklogTable.selectedItem.connect( self.showDetails )
        self.ui.worklogTable.selectedItem.connect( self.setCalendarDateFromTable )
        self.ui.worklogTable.itemUnselected.connect( self.hideDetails )
        self.ui.dayEntriesWidget.selectedEntry.connect( self.showDetails )
        self.ui.dayEntriesWidget.entryUnselected.connect( self.hideDetails )

        self.ui.notesWidget.dataChanged.connect( self._handleNotesChange )

        self.trayIcon.show()

        self.setWindowTitle()

        self.ui.navcalendar.setSelectedDate( date.today() )

        ## update table's filter
        selectedDate = self.ui.navcalendar.selectedDate()
        self.calendarPageChanged( selectedDate.year(), selectedDate.month() )
        self.calendarSelectionChanged()

        self.setStatusMessage( "Ready", timeout=10000 )

        QtCore.QTimer.singleShot( 100, self._finishInit )

    def _finishInit(self):
        self.applySettings( True )
        self.updateRecentEntry()
        self.refreshView()

    def loadData(self):
        """Load user related data (e.g. favs, notes)."""
        dataPath = self.getDataPath()
        self.data.load( dataPath )
        self.readFromKernlog()
        self.refreshView()

    def readFromKernlog(self):
        workMode = self.appSettings.workMode
        self.data.readFromKernlog( workMode )

    def triggerSaveTimer(self):
        timeout = 30000
        _LOGGER.info("triggering save timer with timeout %s", timeout)
        QtCore.QTimer.singleShot( timeout, self.saveData )

    def saveData(self):
        self.updateRecentEntry()
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

    def switchWorkLogging(self, loggingWork: bool):
        history = self.data.history
        recentEntry = history.recentEntry()
        if recentEntry is None:
            ## add new entry
            self.data.addNewEntry( loggingWork )
        elif recentEntry.work != loggingWork:
            ## add new entry
            self.data.addNewEntry( loggingWork )
        self._refreshIconTheme()
        self.updateRecentEntry()

    def updateRecentEntry(self):
        history = self.data.history
        recentEntry = history.recentEntry()
        if recentEntry is None:
            _LOGGER.warning( "unable to update -- no recent entry" )
            return
        currTime = datetime.today()
        timeDiff = currTime - recentEntry.endTime
        if timeDiff > timedelta( hours=2 ):
            _LOGGER.warning( "unable to update -- recent entry end time to old" )
            return
        recentEntry.endTime = currTime
        self.refreshEntryView( recentEntry )
        working = self.isWorking()
        if working == recentEntry.work:
            _LOGGER.warning( "unable to update -- work status not changed: %s %s", working, recentEntry.printData() )
            return
        newEntry = self.data.addNewEntry( working )
        _LOGGER.warning( "adding new entry: %s", newEntry.printData() )
        self.refreshEntryView( newEntry )

    def refreshEntryView(self, entity):
        self.ui.worklogTable.refreshEntry( entity )
        self.ui.dayEntriesWidget.update()
        if self.isShowDetails( entity ):
            self.showDetails( entity )
        self.ui.dayEntriesWidget.updateDayWorkTime()
        self.updateTrayToolTip()

    def _screenSaverChanged(self, state):
        ### state:
        ###    True  -- screen saver started
        ###    False -- screen saver stopped
        self.awayFromKeyboardChanged( state, "screen saver changed" )
        self.refreshView()

    def _sessionChanged(self, state):
        ### state:
        ###    True  -- session locked
        ###    False -- session unlocked
        self.awayFromKeyboardChanged( state, "session lock changed" )
        self.refreshView()

    def awayFromKeyboardChanged(self, state, description="") -> WorkLogEntry:
        ### state:
        ###    True  -- away from keyboard
        ###    False -- returned
        history = self.data.history
        recentEntry = history.recentEntry()
        if state is True:
            ## away from keyboard
            if recentEntry.work is False:
                _LOGGER.debug( "recent is not work -- ignore" )
                return None
            newEntry = self.data.addNewEntry( False )
            newEntry.description = description
            history.joinDown( recentEntry, newEntry )
            _LOGGER.debug( "added new entry: %s", newEntry.printData() )
            return newEntry
        else:
            ## returned to keyboard
            if self.trayIcon.isWorkLogging() is False:
                return None
            ## if user went away for short period, then do not count break
            if recentEntry.getDuration() < timedelta( minutes=3 ):
                recentEntry.description = ""
                _LOGGER.debug( "merging entry up: %s", recentEntry.printData() )
                history.mergeEntryUp( recentEntry )
                return None
            newEntry = self.data.addNewEntry( True )
            history.joinDown( recentEntry, newEntry )
            _LOGGER.debug( "added new entry: %s", newEntry.printData() )
            return newEntry

    def isWorking(self):
        if self.trayIcon.isWorkLogging() is False:
            return False
        if self.activity.isAwayFromKeyboard() is True:
            return False
        return True

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
        self.updateTrayToolTip()

    def refreshView(self):
        self.ui.worklogTable.refreshData()
        self.ui.notesWidget.setNotes( self.data.notes )
        self.ui.dayEntriesWidget.updateView()
        self.showDetails( None )

    def updateView(self):
        self.ui.navcalendar.updateCells()
        self.hideDetails()
        self.ui.dayEntriesWidget.updateDayWorkTime()
        self.updateTrayToolTip()

    def calendarPageChanged(self, year: int, month: int):
        self.ui.worklogTable.setMonth( year, month )

    def calendarSelectionChanged(self):
        self.ui.worklogTable.clearSelection()
        selectedDate = self.ui.navcalendar.selectedDate()
        dateValue = selectedDate.toPyDate()
        self.ui.dayEntriesWidget.setCurrentDate( dateValue )

    def showDetails(self, entity):
        if entity is None:
            self.hideDetails()
            return
        self.ui.entrydetails.setObject( entity )
        self.ui.itemSW.setCurrentIndex( 1 )

    def hideDetails(self):
        self.ui.itemSW.setCurrentIndex( 0 )

    def isShowDetails(self, entity):
        if self.ui.itemSW.currentIndex() == 0:
            return False
        if self.ui.entrydetails.entry is not entity:
            return False
        return True

    def setCalendarDateFromTable(self, entity):
        if entity is None:
            return
        entryDate = entity.startTime
        if entryDate is None:
            return
        entryDate = entryDate.date()
        tableMonth = self.ui.worklogTable.getMonth()
        if tableMonth is not None and entryDate < tableMonth:
            self.ui.navcalendar.setSelectedDate( tableMonth )
            return
        self.ui.navcalendar.setSelectedDate( entryDate )

    def _filterWorkEntries(self):
        checked = self.ui.showWorkOnlyCB.isChecked()
        self.ui.worklogTable.filterWorkEntries( checked )

    ## ====================================================================

    def _handleNotesChange(self):
        self.triggerSaveTimer()

    ## ====================================================================

    def setStatusMessage(self, firstStatus, changeStatus: list = None, timeout=6000):
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

    def updateTrayToolTip(self):
        if hasattr(self, 'trayIcon') is False:
            return
        toolTip = self.windowTitle()
        if hasattr(self, 'data') is False:
            self.trayIcon.setToolTip( toolTip )
            return
        recentEntry = self.data.history.recentEntry()
        if recentEntry is not None:
            recentDuration = recentEntry.getDuration()
            toolTip += "\n\n" + "Current duration: " + str( recentDuration )

        currDate = datetime.today().date()
        workTime = self.data.calculateWorkDuration( currDate )
        toolTip += "\n" + "Work duration: " + str( workTime )
        self.trayIcon.setToolTip( toolTip )

    def setIconTheme(self, theme: trayicon.TrayIconTheme):
        _LOGGER.debug("setting tray theme: %r", theme)
        self._setTrayIndicator( theme )

    def _refreshIconTheme(self):
        theme = self.getIconTheme()
        self._setTrayIndicator( theme )

    def _setTrayIndicator(self, theme: trayicon.TrayIconTheme):
        iconName = None
        if self.trayIcon.isWorkLogging():
            iconName = theme.working
        else:
            iconName = theme.normal
        appIcon = trayicon.load_icon( iconName )
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
            self.updateRecentEntry()
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
        self.updateRecentEntry()
        ##self.close()
        qApp.quit()

    def saveAll(self):
        _LOGGER.info("saving application state")
        self.saveSettings()
        self.saveData()

    ## ====================================================================

    def openLogsWindow(self):
        logwidget.create_window( self )

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

    def applySettings(self, force=False):
        self.setIconTheme( self.appSettings.trayIcon )
        workMode = self.appSettings.workMode
        if self.trayIcon.isWorkLogging() is not workMode or force is True:
            self.trayIcon.setWorkLogging( workMode )
            self.switchWorkLogging( workMode )

    def loadSettings(self):
        """Load Qt related settings (e.g. layouts, sizes)."""
        settings = self.getSettings()
        _LOGGER.debug( "loading app state from %s", settings.fileName() )

        self.appSettings.loadSettings( settings )

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
