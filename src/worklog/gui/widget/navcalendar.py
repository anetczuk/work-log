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

import abc
import datetime

from PyQt5.QtWidgets import QCalendarWidget

from PyQt5 import QtCore
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu


class NavCalendarHighlightModel():

    @abc.abstractmethod
    def isHighlighted(self, dateValue: QtCore.QDate ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def isOccupied(self, dateValue: QtCore.QDate ):
        raise NotImplementedError('You need to define this method in derived class!')


class NavCalendar( QCalendarWidget ):

    addEntry  = pyqtSignal( QDate )

    def __init__( self, *args ):
        QCalendarWidget.__init__( self, *args )

        self.cellsTable = self.findChild( QTableView )

        self.itemColor = QColor( self.palette().color( QPalette.Highlight) )
        self.itemColor.setAlpha( 64 )
        self.occupiedColor = QColor( QColor(160, 160, 160) )
        self.occupiedColor.setAlpha( 64 )

        self.highlightModel = None
        self.selectionChanged.connect( self.updateCells )

    def paintCell(self, painter, rect, date):
        QCalendarWidget.paintCell(self, painter, rect, date)

        if self.isHighlighted( date ) is True:
            painter.fillRect( rect, self.itemColor )
        elif self.isOccupied( date ) is True:
            painter.fillRect( rect, self.occupiedColor )

        if date == QDate.currentDate():
            painter.drawRect( rect.left(), rect.top(), rect.width() - 1, rect.height() - 1 )

    def isHighlighted(self, date):
        if self.highlightModel is None:
            return False
        return self.highlightModel.isHighlighted( date )

    def isOccupied(self, date):
        if self.highlightModel is None:
            return False
        return self.highlightModel.isOccupied( date )

    def contextMenuEvent( self, event ):
        evPos     = event.pos()
        globalPos = self.mapToGlobal( evPos )
        tabPos    = self.cellsTable.mapFromGlobal( globalPos )
        cellIndex = self.cellsTable.indexAt( tabPos )
        if cellIndex.row() < 1:
            ## skip row with days of week
            return
        if cellIndex.column() < 1:
            ## skip column with number of week
            return

        contextMenu = QMenu(self)
        addEntryAction  = contextMenu.addAction("New Entry")
        action = contextMenu.exec_( globalPos )

        if action == addEntryAction:
            dayIndex = (cellIndex.row() - 1) * 7 + (cellIndex.column() - 1)
            contextDate = self.dateAt( dayIndex )
            self.addEntry.emit( contextDate )

    def dateAt( self, dayIndex ):
        prevMonthDays = self.daysFromPreviousMonth()
        dayOffset = dayIndex - prevMonthDays
        currYear  = self.yearShown()
        currMonth = self.monthShown()
        currDate  = QDate( currYear, currMonth, 1 )
        return currDate.addDays( dayOffset )

    def daysFromPreviousMonth( self ):
        currYear     = self.yearShown()
        currMonth    = self.monthShown()
        firstOfMonth = datetime.date( currYear, currMonth, 1 )
        days = firstOfMonth.weekday()
        if days == 0:                       # 0 means Monday
            days += 7                       # there is always one row
        return days
