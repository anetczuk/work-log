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
from datetime import datetime
import copy

from worklog.gui.datatypes import WorkLogEntry, WorkLogData

from .. import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


_LOGGER = logging.getLogger(__name__)


class EntryDialog( QtBaseClass ):           # type: ignore

    def __init__(self, history: WorkLogData, entry: WorkLogEntry, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.history: WorkLogData = history
        self.entry: WorkLogEntry = None

        self.finished.connect( self._done )

        self.setObject( entry )

    def setObject(self, entry: WorkLogEntry):
        if entry is not None:
            self.entry = copy.deepcopy( entry )
        else:
            self.entry = WorkLogEntry()

        startDate = entry.startTime
        if startDate is None:
            startDate = datetime.now()
        self.ui.startDTE.setDateTime( startDate )

        endDate = entry.endTime
        if endDate is None:
            endDate = datetime.now()
        self.ui.endDTE.setDateTime( endDate )

        self.ui.workCB.setChecked( entry.work )

        self.ui.descriptionTE.setText( entry.description )

        self.adjustSize()

    def _done(self, newValue):
        newValue = self.ui.startDTE.dateTime()
        data     = newValue.toPyDateTime()
        self.entry.startTime = data

        newValue = self.ui.endDTE.dateTime()
        data     = newValue.toPyDateTime()
        self.entry.endTime = data.replace( second=0, microsecond=0 )

        self.entry.work = self.ui.workCB.isChecked()

        self.entry.description = self.ui.descriptionTE.toPlainText()
