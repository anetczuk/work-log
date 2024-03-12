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
from datetime import timedelta
import pathlib

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

    def __init__(self, parent: QWidget = None):
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
        item_date = None
        if entryDate is not None:
            item_date = entryDate.toPyDate()
        else:
            item_date = datetime.datetime.today().date()
        entry.startTime = datetime.datetime.combine( item_date, datetime.time( hour=9 ) )
        entry.endTime   = datetime.datetime.combine( item_date, datetime.time( hour=17 ) )
        self.addEntryNew( entry )

    def addEntry2(self, startTime: datetime.datetime):
        entry = WorkLogEntry()
        entry.startTime = startTime
        entry.endTime   = startTime + timedelta( hours=1 )
        self.addEntryNew( entry )

    def addEntryNew(self, entry: WorkLogEntry):
        if entry is None:
            self.addEntry()
            return
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

    def addNewEntry(self, workLog):
        entry = WorkLogEntry()
        entryDate = datetime.datetime.today()
        entryDate = entryDate.replace( second=0, microsecond=0 )
        entry.startTime = entryDate
        entry.endTime   = entryDate
        entry.work      = workLog
        self.history.addEntry( entry )
        self.entryChanged.emit()
        return entry

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

    def calculateWorkDuration(self, day: datetime.date):
        entries = self.history.getEntriesForDate( day )
        workTime = timedelta()
        for item in entries:
            if item.work:
                workTime += item.getDuration()
        return workTime

    def readFromKernlog(self, recentWorking=True):
        oldEntry = self.history.recentEntry()

        self._readKeylogFile( "/var/log/kern.log.1" )
        self._readKeylogFile( "/var/log/kern.log" )

        newEntry = self.history.recentEntry()
        if newEntry is not None:
            if newEntry != oldEntry:
                newEntry.work = recentWorking

    def readFromSyslog(self, recentWorking=True):
        oldEntry = self.history.recentEntry()

        self._readKeylogFile( "/var/log/syslog.1" )
        self._readKeylogFile( "/var/log/syslog" )

        newEntry = self.history.recentEntry()
        if newEntry is not None:
            if newEntry != oldEntry:
                newEntry.work = recentWorking

    def _readKeylogFile(self, filePath: str):
        _LOGGER.info("reading log file: %s", filePath)
        recentEntry = self.history.recentEntry()
        recentDate = None
        if recentEntry is not None:
            recentDate = recentEntry.endTime

        items: List[ DateTimePair ] = SysLogParser.parseLogFile( filePath )
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


def create_entry_contextmenu( parent: QWidget, dataObject: DataObject,
                              editEntry: WorkLogEntry, addEntry: WorkLogEntry = None ):
    contextMenu      = QtWidgets.QMenu( parent )
    addAction        = contextMenu.addAction("Add Entry")
    editAction       = contextMenu.addAction("Edit Entry")
    removeAction     = contextMenu.addAction("Remove Entry")

    joinSubMenu      = contextMenu.addMenu("Join")
    joinUpAction     = joinSubMenu.addAction("Up")
    joinDownAction   = joinSubMenu.addAction("Down")

    mergeSubMenu     = contextMenu.addMenu("Merge")
    mergeUpAction    = mergeSubMenu.addAction("Up")
    mergeDownAction  = mergeSubMenu.addAction("Down")

    if editEntry is None:
        editAction.setEnabled( False )
        removeAction.setEnabled( False )
        joinSubMenu.setEnabled( False )
        mergeSubMenu.setEnabled( False )

    globalPos = QtGui.QCursor.pos()
    action = contextMenu.exec_( globalPos )

    if action == addAction:
        dataObject.addEntryNew( addEntry )
    elif action == editAction:
        dataObject.editEntry( editEntry )
    elif action == removeAction:
        dataObject.removeEntry( editEntry )
    elif action == joinUpAction:
        dataObject.joinEntryUp( editEntry )
    elif action == joinDownAction:
        dataObject.joinEntryDown( editEntry )
    elif action == mergeUpAction:
        dataObject.mergeEntryUp( editEntry )
    elif action == mergeDownAction:
        dataObject.mergeEntryDown( editEntry )


## ===================================================


# contains two values:
#    1 - wall clock of log entry
#    2 - time from boot (it helps detect when boot happened)
KernLogPair  = Tuple[datetime.datetime, float]
DateTimePair = Tuple[datetime.datetime, datetime.datetime]


# class TimeRange():
#
#     def __init__(self):
#         self.start_time: datetime.datetime = None
#         self.end_time: datetime.datetime = None
#
#     def setTime(self, next_time: datetime.datetime):
#         if self.start_time is None:
#             self.start_time = next_time
#         self.end_time = next_time


class SysLogParser():

    def __init__(self):
        self.datesList: List[ DateTimePair ] = []

    def parse(self, filePath: str):
        self.datesList.clear()
        suspendDetected = False
        timestampList: List[ KernLogPair ] = []
        ##currentDate = datetime.datetime.today()
        fileDate  = self._filemoddate( filePath )
        engLocale = QtCore.QLocale(QtCore.QLocale.English)
        recentKernTimestamp = 0.0

        # kernLogTimestampRange = TimeRange()

        with open( filePath ) as fp:
            for line in fp:
                ## Oct 29 21:02:01 wxyz kernel: [ 8353.210086] abc log entry
                ## Oct 26 00:09:42 wxyz ccc.dddd-browsed[1549]: [12927.909529] abc log entry
                matched = re.match( r'^(.*?) (\S+?) (\S+?): (.*?)$', line )
                if matched is None:
                    _LOGGER.warning("log parsing failed: %s", line)
                    continue
                logTimestampStr = matched.group(1)             # timestamp

                logTimestampStr = logTimestampStr.strip()
                logTimestampStr = logTimestampStr.replace("  ", " ")

                ## can happen that there is some trashy \0 signs in front of string
                logTimestampStr = logTimestampStr.strip('\0')

                ## have to use Qt, because Qt corrupts native "datetime.strptime"
                # logTimestamp = datetime.datetime.strptime(logTimestampStr, '%b %d %H:%M:%S')
                # _LOGGER.info("parsed: %s | %s", logTimestampStr, logTimestamp)

                try:
                    ## add year to properly handle leap year date (Feb 29)
                    logTimestampStr = f"{fileDate.year} {logTimestampStr}"
                    qtTimestamp  = engLocale.toDateTime( logTimestampStr, "yyyy MMM d HH:mm:ss")
                    if not qtTimestamp.isValid():
                        _LOGGER.error("unable to parse date: '%s'", logTimestampStr)

                    logTimestamp = qtTimestamp.toPyDateTime()
                    logTimestamp = logTimestamp.replace( second=0, microsecond=0 )
                except ValueError as exc:
                    _LOGGER.error("unable to parse '%s', reason: %s, parsed: %s", logTimestampStr, exc, qtTimestamp.toString())
                    raise

                process = matched.group(3)
                if process == "kernel":
                    messageStr = matched.group(4)
                    matched = re.match( r'^\[(.*?)\] (.*?)$', messageStr )
                    if matched is None:
                        _LOGGER.warning("kernel log parsing failed: %s", line)
                        continue

                    try:
                        logEntry          = matched.group(2)
                        kernTimestampStr  = matched.group(1).strip()
                        currKernTimestamp = float( kernTimestampStr )

                        if currKernTimestamp < recentKernTimestamp:
                            # reboot detected
                            timestampList.append( (logTimestamp, currKernTimestamp) )     # will be trimmed
                            self._fixYear(timestampList)
                            trimmed_list, next_part_list = self._trimTime(timestampList)
                            self._addDates(trimmed_list)
                            timestampList = next_part_list

                        recentKernTimestamp = currKernTimestamp

                    except ValueError as exc:
                        # happens when log line is mangled/corrupt
                        _LOGGER.warning("unable to parse log line: %s", exc)

                    if "PM: suspend entry" in logEntry:
                        # entering suspend
                        self._addDates(timestampList)
                        timestampList.clear()
                        suspendDetected = True
                        continue

                    elif "PM: suspend exit" in logEntry:
                        # exiting from suspend
                        suspendDetected = False

                if suspendDetected:
                    continue

                timestampList.append( (logTimestamp, recentKernTimestamp) )

        # end of file
        self._addDates(timestampList)
        self._fixYear(self.datesList)
        return self.datesList

    def _filemoddate(self, filePath: str):
        fname = pathlib.Path( filePath )
        mtime = datetime.datetime.fromtimestamp( fname.stat().st_mtime )
        return mtime

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

    # (logTimestamp, recentKernTimestamp)
    def _trimTime(self, timestamp_list):
        list_size = len( timestamp_list )
        if list_size < 2:
            return (timestamp_list, [])
        last_entry = timestamp_list[-1]
        last_timestamp: datetime.datetime = last_entry[0]
        reboot_margin_timestamp = (last_timestamp - timedelta(minutes=2))
        for index, curr_entry in enumerate( timestamp_list ):
            curr_timestamp: datetime.datetime = curr_entry[0]
            if curr_timestamp > reboot_margin_timestamp:
                rest_list = timestamp_list[index: ]
                timestamp_list = timestamp_list[0: index]
                return (timestamp_list, rest_list)
        return (timestamp_list, [])

    def _fixYear(self, timestamp_list):
        ## fix years
        i = len(timestamp_list) - 1
        if i <= 0:
            return
        recentPair = timestamp_list[i]
        recentDate = recentPair[0]

        i -= 1
        while ( i >= 0 ):
            recentPair = timestamp_list[i]
            currDate = recentPair[0]
            if currDate > recentDate:
                ## last day of year found
                currDate = currDate.replace( year=currDate.year - 1 )
                recentPair = ( currDate, recentPair[1] )
                timestamp_list[i] = recentPair
                recentDate = currDate

            i -= 1

    @staticmethod
    def parseLogFile( filePath: str ) -> List[ DateTimePair ]:
        parser = SysLogParser()
        return parser.parse( filePath )
