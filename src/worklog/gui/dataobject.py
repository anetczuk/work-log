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
from typing import Dict
import datetime

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack

from worklog.gui.datatypes import DataContainer, WorkLogData, WorkLogEntry
from worklog import persist
from worklog.gui.widget.entrydialog import EntryDialog
from worklog.gui.command.addentrycommand import AddEntryCommand
from worklog.gui.command.editentrycommand import EditEntryCommand
from worklog.gui.command.removeentrycommand import RemoveEntryCommand


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

#     @history.setter
#     def history(self, history: Dict[str, str]):
#         self.dataContainer.history = history

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
            entry.entryDate = entryDate.toPyDate()
            entry.startTime = datetime.time( hour=9 )
            entry.endTime   = datetime.time( hour=17 )
        entry.breakTime = datetime.time( minute=30 )

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
        self.removeEntry(entry)
        if entry is None:
            return
        command = RemoveEntryCommand( self, entry )
        self.pushUndo( command )
