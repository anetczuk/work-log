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

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QUndoStack

from worklog.gui.datatypes import DataContainer, WorkLogData
from worklog import persist


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
