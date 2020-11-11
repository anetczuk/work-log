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
import copy

from PyQt5.QtWidgets import QUndoCommand


_LOGGER = logging.getLogger(__name__)


class MergeEntryUpCommand( QUndoCommand ):

    def __init__(self, dataObject, entry, parentCommand=None):
        super().__init__(parentCommand)

        self.data      = dataObject
        self.entry     = entry
        self.oldEntry  = None
        self.prevEntry = None

        self.setText( "Merge Entry Up: " + str(entry.startTime) )

    def redo(self):
        history = self.data.history
        self.prevEntry = history.prevEntry( self.entry )
        self.oldEntry = copy.deepcopy( self.prevEntry )
        history.mergeUp( self.entry, self.prevEntry )
        self.data.entryChanged.emit()

    def undo(self):
        history = self.data.history
        self.prevEntry.__dict__ = self.oldEntry.__dict__
        history.addEntry( self.entry )
        self.data.entryChanged.emit()
