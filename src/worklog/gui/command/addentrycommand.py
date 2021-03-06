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

from PyQt5.QtWidgets import QUndoCommand

from worklog.gui.datatypes import WorkLogData


_LOGGER = logging.getLogger(__name__)


class AddEntryCommand( QUndoCommand ):

    def __init__(self, dataObject, newEntry, parentCommand=None):
        super().__init__(parentCommand)

        self.data = dataObject
        self.history: WorkLogData = self.data.history
        self.newEntry = newEntry

        self.setText( "Add Entry: " + str(newEntry.startTime) )

    def redo(self):
        self.history.addEntry( self.newEntry )
        self.data.entryChanged.emit()

    def undo(self):
        self.history.removeEntry( self.newEntry )
        self.data.entryChanged.emit()
