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
import re
from typing import Dict, List, Tuple
import datetime

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack

from worklog.gui.datatypes import DataContainer, WorkLogData, WorkLogEntry
from worklog import persist
from worklog.gui.widget.entrydialog import EntryDialog
from worklog.gui.command.addentrycommand import AddEntryCommand
from worklog.gui.command.editentrycommand import EditEntryCommand
from worklog.gui.command.removeentrycommand import RemoveEntryCommand
from worklog.gui.command.joinentryupcommand import JoinEntryUpCommand
from worklog.gui.command.joinentrydowncommand import JoinEntryDownCommand
from worklog.gui.command.mergeentryupcommand import MergeEntryUpCommand
from worklog.gui.command.mergeentrydowncommand import MergeEntryDownCommand


_LOGGER = logging.getLogger(__name__)


class DataObject( QObject ):

    entryChanged = pyqtSignal()

    def __init__(self, parent: QWidget=None):
        super().__init__( parent )
        self.parentWidget = parent

        self.dataContainer = DataContainer()                   ## user data

        self.undoStack = QUndoStack(self)

    def store( self, outputDir ):
        outputFile = outputDir + "/data.obj"
        return persist.store_backup( self.dataContainer, outputFile )

    def load( self, inputDir ):
        inputFile = inputDir + "/data.obj"
        self.dataContainer = persist.load_object_simple( inputFile )
        if self.dataContainer is None:
            self.dataContainer = DataContainer()

    @property
    def history(self) -> WorkLogData:
        return self.dataContainer.history

    @history.setter
    def history(self, history: WorkLogData):
        self.dataContainer.history = history

    @property
    def notes(self) -> Dict[str, str]:
        return self.dataContainer.notes

    @notes.setter
    def notes(self, newData: Dict[str, str]):
        self.dataContainer.notes = newData

    def pushUndo(self, undoCommand):
        self.undoStack.push( undoCommand )

    ## =========================================================

    def addEntry(self, entryDate: QtCore.QDate = None):
        entry = WorkLogEntry()
        if entryDate is not None:
            entryDate = entryDate.toPyDate()
        else:
            entryDate = datetime.datetime.today().date()
        entry.startTime = datetime.datetime.combine( entryDate, datetime.time( hour=9 ) )
        entry.endTime   = datetime.datetime.combine( entryDate, datetime.time( hour=17 ) )

        parentWidget = self.parent()
        entryDialog = EntryDialog( self.history, entry, parentWidget )
        entryDialog.setModal( True )
        dialogCode = entryDialog.exec_()
        if dialogCode == QtWidgets.QDialog.Rejected:
            return
        _LOGGER.debug( "adding entry: %s", entryDialog.entry.printData() )
        command = AddEntryCommand( self, entryDialog.entry )
        self.pushUndo( command )

    def editEntry(self, entry):
        if entry is None:
            return
        parentWidget = self.parent()
        entryDialog = EntryDialog( self.history, entry, parentWidget )
        entryDialog.setModal( True )
        dialogCode = entryDialog.exec_()
        if dialogCode == QtWidgets.QDialog.Rejected:
            return
        command = EditEntryCommand( self, entry, entryDialog.entry )
        self.pushUndo( command )

    def removeEntry(self, entry):
        if entry is None:
            return
        command = RemoveEntryCommand( self, entry )
        self.pushUndo( command )

    def joinEntryUp(self, entry):
        if entry is None:
            return
        command = JoinEntryUpCommand( self, entry )
        self.pushUndo( command )

    def joinEntryDown(self, entry):
        if entry is None:
            return
        command = JoinEntryDownCommand( self, entry )
        self.pushUndo( command )

    def mergeEntryUp(self, entry):
        if entry is None:
            return
        command = MergeEntryUpCommand( self, entry )
        self.pushUndo( command )

    def mergeEntryDown(self, entry):
        if entry is None:
            return
        command = MergeEntryDownCommand( self, entry )
        self.pushUndo( command )

    def readFromKernlog(self):
        self._readKeylogFile( "/var/log/kern.log.1" )
        self._readKeylogFile( "/var/log/kern.log" )

    def _readKeylogFile(self, filePath: str):
        recentEntry = self.history.recentEntry()
        recentDate = None
        if recentEntry is not None:
            recentDate = recentEntry.endTime

        items: List[ DateTimePair ] = KernLogParser.parseKernLog( filePath )
        for item in items:
            if recentDate is not None:
                if item[1] < recentDate:
                    continue
            entry = WorkLogEntry()
            entry.startTime = item[0]
            entry.endTime   = item[1]
            foundEntries = self.history.findEntriesInRange( item[0], item[1] )
            eSize = len(foundEntries)
            if eSize < 1:
                self.history.entries.append( entry )
            elif eSize == 1:
                currEntry: WorkLogEntry = foundEntries[0]
                if currEntry.startTime > item[0]:
                    currEntry.startTime = item[0]
                if currEntry.endTime < item[1]:
                    currEntry.endTime = item[1]
        self.history.sort()


## ===================================================


def create_entry_contextmenu( parent: QWidget, dataObject: DataObject, entry: WorkLogEntry ):
    contextMenu      = QtWidgets.QMenu( parent )
    addAction        = contextMenu.addAction("Add Entry")
    editAction       = contextMenu.addAction("Edit Entry")
    removeAction     = contextMenu.addAction("Remove Entry")
    joinUpAction     = contextMenu.addAction("Join up")
    joinDownAction   = contextMenu.addAction("Join down")
    mergeUpAction    = contextMenu.addAction("Merge up")
    mergeDownAction  = contextMenu.addAction("Merge down")

    if entry is None:
        editAction.setEnabled( False )
        removeAction.setEnabled( False )
        joinUpAction.setEnabled( False )
        joinDownAction.setEnabled( False )
        mergeUpAction.setEnabled( False )
        mergeDownAction.setEnabled( False )

    globalPos = QtGui.QCursor.pos()
    action = contextMenu.exec_( globalPos )

    if action == addAction:
        dataObject.addEntry()
    elif action == editAction:
        dataObject.editEntry( entry )
    elif action == removeAction:
        dataObject.removeEntry( entry )
    elif action == joinUpAction:
        dataObject.joinEntryUp( entry )
    elif action == joinDownAction:
        dataObject.joinEntryDown( entry )
    elif action == mergeUpAction:
        dataObject.mergeEntryUp( entry )
    elif action == mergeDownAction:
        dataObject.mergeEntryDown( entry )


## ===================================================


KernLogPair  = Tuple[datetime.datetime, float]
DateTimePair = Tuple[datetime.datetime, datetime.datetime]


class KernLogParser():

    def __init__(self):
        self.datesList: List[ DateTimePair ] = []

    def parse(self, filePath: str):
        self.datesList.clear()
        suspendDetected = False
        timestampList: List[ KernLogPair ] = []
        currentDate = datetime.datetime.today()
        engLocale   = QtCore.QLocale(QtCore.QLocale.English)
        with open( filePath ) as fp:
            for line in fp:
                ## Oct 29 21:02:01 wxyz kernel: [ 8353.210086] abc log entry
                matched = re.match( r'^(.*) (\S+) kernel: \[(.*?)\] (.*)$', line )
                if matched is None:
                    _LOGGER.warning("log parsing failed: %s", line)
                    continue
                logTimestampStr  = matched.group(1)

                logTimestampStr  = logTimestampStr.strip()
                logTimestampStr  = logTimestampStr.replace("  ", " ")

                ## can happen that there is some trashy \0 signs in front of string
                logTimestampStr  = logTimestampStr.strip('\0')
                ## print( "timestamp:", ".join([ str(ord(c)) for c in logTimestampStr]) )

                ## have to use Qt, because Qt corrupts native "datetime.strptime"
                logTimestamp     = engLocale.toDateTime( logTimestampStr, "MMM d HH:mm:ss")
                logTimestamp     = logTimestamp.toPyDateTime()
                logTimestamp     = logTimestamp.replace( year=currentDate.year, second=0 )

                kernTimestampStr = matched.group(3).strip()
                kernTimestamp    = float( kernTimestampStr )

                logEntry         = matched.group(4)

                if "PM: suspend entry" in logEntry:
                    self._addDates(timestampList)
                    timestampList.clear()
                    suspendDetected = True
                    continue
                elif "PM: suspend exit" in logEntry:
                    suspendDetected = False
                else:
                    if suspendDetected:
                        continue

                timestampList.append( (logTimestamp, kernTimestamp) )

        self._addDates(timestampList)

        return self.datesList

    def _addDates(self, timestampList):
        tsSize = len( timestampList )
        if tsSize < 1:
            return

        firstLog = None
        lastLog  = None
        for i in range(0, tsSize):
            currLog: KernLogPair = timestampList[i]
            if firstLog is None:
                firstLog = currLog
                continue
            if lastLog is None:
                lastLog = currLog
                continue
            if currLog[1] >= lastLog[1]:
                lastLog = currLog
                continue

            # next boot found
            entry: DateTimePair = ( firstLog[0], lastLog[0] )
            self.datesList.append( entry )
            firstLog = None
            lastLog  = None

        if lastLog is not None:
            entry: DateTimePair = ( firstLog[0], lastLog[0] )
            self.datesList.append( entry )

    @staticmethod
    def parseKernLog( filePath: str ) -> List[ DateTimePair ]:
        parser = KernLogParser()
        return parser.parse( filePath )
