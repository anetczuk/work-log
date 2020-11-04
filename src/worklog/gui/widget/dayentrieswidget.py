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
from datetime import datetime, timedelta, date
import copy

from PyQt5.QtCore import pyqtSignal

from worklog.gui.datatypes import WorkLogEntry, WorkLogData

from .. import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


_LOGGER = logging.getLogger(__name__)


class DayEntriesWidget( QtBaseClass ):           # type: ignore

    selectedEntry    = pyqtSignal( WorkLogEntry )
    entryUnselected  = pyqtSignal()
    editEntry        = pyqtSignal( WorkLogEntry )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.ui.dayListWidget.selectedEntry.connect( self.selectedEntry )
        self.ui.dayListWidget.entryUnselected.connect( self.entryUnselected )
        self.ui.dayListWidget.editEntry.connect( self.editEntry )

    def connectData(self, dataObject):
        self.ui.dayListWidget.connectData( dataObject )

    def setCurrentDate(self, currDate: date):
        self.ui.dayListWidget.currentDate = currDate
        self.ui.dayListWidget.updateView()
        self.updateDayWorkTime()

    def updateView(self):
        self.ui.dayListWidget.updateView()

    def updateDayWorkTime(self, entry: WorkLogData=None):
        workTime = timedelta()
        entries = self.ui.dayListWidget.getEntries()
        for item in entries:
            if item.work:
                workTime += item.getDuration()
        self.ui.dayWorkDurationLabel.setText( str(workTime) )

#     def setObject(self, entry: WorkLogEntry):
#         if entry is not None:
#             self.entry = copy.deepcopy( entry )
#         else:
#             self.entry = WorkLogEntry()
# 
#         startDate = entry.startTime
#         if startDate is None:
#             startDate = datetime.now()
#         self.ui.startDTE.setDateTime( startDate )
# 
#         endDate = entry.endTime
#         if endDate is None:
#             endDate = datetime.now()
#         self.ui.endDTE.setDateTime( endDate )
# 
#         self.ui.workCB.setChecked( entry.work )
# 
#         self.ui.descriptionTE.setText( entry.description )
# 
#         self.adjustSize()
# 
#     def _done(self, newValue):
#         newValue = self.ui.startDTE.dateTime()
#         data     = newValue.toPyDateTime()
#         self.entry.startTime = data
# 
#         newValue = self.ui.endDTE.dateTime()
#         data     = newValue.toPyDateTime()
#         self.entry.endTime = data.replace( second=0, microsecond=0 )
# 
#         self.entry.work = self.ui.workCB.isChecked()
# 
#         self.entry.description = self.ui.descriptionTE.toPlainText()
