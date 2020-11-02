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
from datetime import date

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QRect
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor

from worklog.gui.datatypes import WorkLogEntry
from worklog.gui.datatypes import WorkLogData
from worklog.gui.dataobject import create_entry_contextmenu


_LOGGER = logging.getLogger(__name__)


class DrawWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        ## it seems to be redundant, but widget won't respect forcing sizing
        ## if it does not have layout and any child content
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( hlayout )
        hlayout.addWidget( QWidget(self) )


class DayTimeline( DrawWidget ):
    """Timeline strip placed on left side of widget."""

    itemClicked = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )
        self.setFixedWidth( 30 )

    def paintEvent(self, event):
        super().paintEvent( event )

        painter = QPainter(self)

        width  = self.width()
        height = self.height()

        bgColor = self.palette().color( self.backgroundRole() )
        painter.fillRect( 0, 0, width, height, bgColor )

        hourStep = height / 24

        pen = painter.pen()
        pen.setColor( QColor("black") )
        painter.setPen(pen)
        painter.drawText( 0, 0, width - 6, hourStep, Qt.TextSingleLine | Qt.AlignTop | Qt.AlignRight, "0" )

        for h in range(0, 24):
            hourHeight = hourStep * h
            text = str(h)

            pen = painter.pen()
            pen.setColor( QColor("gray") )
            painter.setPen(pen)
            painter.drawLine( 0, hourHeight, width, hourHeight )

            pen = painter.pen()
            pen.setColor( QColor("black") )
            painter.setPen(pen)
            painter.drawText( 0, hourHeight, width - 6, hourStep,
                              Qt.TextSingleLine | Qt.AlignTop | Qt.AlignRight,
                              text )

        hourHeight = hourStep * 24 - 1
        pen = painter.pen()
        pen.setColor( QColor("gray") )
        painter.setPen(pen)
        painter.drawLine( 0, hourHeight, width, hourHeight )

    def mousePressEvent(self, _):
        self.itemClicked.emit()


class DayItem( DrawWidget ):
    """Item widget."""

    selectedItem       = pyqtSignal( DrawWidget )
    itemDoubleClicked  = pyqtSignal( DrawWidget )

#     def __init__(self, _, day: date, parentWidget=None):
    def __init__(self, entry: WorkLogEntry, day: date, parentWidget=None):
        super().__init__( parentWidget )

        self.day                  = day
        self.entry: WorkLogEntry  = entry

#         self.setStyleSheet( "background-color: red" )

    def resizeItem( self, lineRect: QRect ):
        allowedWidth  = lineRect.width()
        allowedHeight = lineRect.height()
        xOffset       = lineRect.x()

        calcSpan = self.entry.calculateTimeSpan( self.day )      ## pair of numbers in range [0, 1]

        yOffset = allowedHeight * calcSpan[0]
        self.move(xOffset, yOffset)

        spanDuration = calcSpan[1] - calcSpan[0]
        self.setFixedWidth( allowedWidth )
        self.setFixedHeight( allowedHeight * spanDuration )

    def paintEvent(self, event):
        super().paintEvent( event )

        painter = QPainter(self)

        width  = self.width()
        height = self.height()

        path = QPainterPath()
        path.addRoundedRect( 2, 0, width - 4, height, 5, 5 )

#         itemBgColor = monthcalendar.get_task_bgcolor( self.task )
        selected = self.isSelected()
        itemBgColor = get_entry_bgcolor( self.entry, selected )
        painter.fillPath( path, itemBgColor )

        pathPen = QPen( QColor("black") )
        pathPen.setWidth( 2 )
        painter.strokePath( path, pathPen )

        pen = painter.pen()
        pen.setColor( QColor("black") )
        painter.setPen(pen)
        if height < 32:
            painter.drawText( 6, 0, width - 12, height,
                              Qt.TextSingleLine | Qt.AlignVCenter | Qt.AlignLeft,
                              self.entry.description )
        else:
            painter.drawText( 6, 0, width - 12, 32,
                              Qt.TextSingleLine | Qt.AlignVCenter | Qt.AlignLeft,
                              self.entry.description )

    def mousePressEvent(self, _):
        self.selectedItem.emit( self )

    def mouseDoubleClickEvent(self, _):
        self.itemDoubleClicked.emit( self )

    def isSelected(self):
        return self.parent().isSelected(self)


class DayListContentWidget( QWidget ):

    selectedEntry       = pyqtSignal( int )
    entryDoubleClicked  = pyqtSignal( int )

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

#         self.showCompleted = False
        self.items         = []
        self.currentIndex  = -1

    def clear(self):
        self.setCurrentIndex( -1 )
        for w in self.items:
            w.deleteLater()
        self.items.clear()

    def setCurrentIndex(self, index):
        self.currentIndex = index
        self.selectedEntry.emit( index )
        self.update()

    def getCurrentEntry(self) -> WorkLogEntry:
        return self.getEntry( self.currentIndex )

    def getEntry(self, index) -> WorkLogEntry:
        if index < 0:
            return None
        if index >= len(self.items):
            return None
        widget: DayItem = self.items[ index ]
        return widget.entry

    def setEntries(self, entriesList, day: date ):
        self.clear()

#         if self.showCompleted is False:
#             occurrencesList = [ task for task in occurrencesList if not task.isCompleted() ]

        for entry in entriesList:
            item = DayItem(entry, day, self)
            item.selectedItem.connect( self.handleItemSelect )
            item.itemDoubleClicked.connect( self.handleItemDoubleClick )
            self.items.append( item )
            item.show()

        self._resizeItems()
        self.update()

    def paintEvent(self, event):
        super().paintEvent( event )

        painter = QPainter( self )

        width  = self.width()
        height = self.height()

        pen = painter.pen()
        pen.setColor( QColor("gray") )
        painter.setPen(pen)

        hourStep = height / 24
        for h in range(0, 24):
            hourHeight = hourStep * h
            painter.drawLine( 0, hourHeight, width, hourHeight )

        ## bottom line
        hourHeight = hourStep * 24 - 1
        painter.drawLine( 0, hourHeight, width, hourHeight )

    def resizeEvent(self, event):
        self._resizeItems()
        return super().resizeEvent( event )

    def _resizeItems(self):
        linesMap, linesNum = self._linesDict()

        for widget in self.items:
            widgetLine = linesMap[ widget ]
            lineRect = self._lineRect( widgetLine, linesNum )
            widget.resizeItem( lineRect )

    def _linesDict(self):
        sItems = len(self.items)
        if sItems < 1:
            return ({}, 0)

        firstWidget = self.items[ 0 ]
        itemLine = {}
        itemLine[ firstWidget ] = 0
        lineItem = []
        lineItem.append( firstWidget )

        for i in range(1, sItems):
            currWidget = self.items[ i ]
            currEntry  = currWidget.entry

            linesNum = len( lineItem )
            found = False
            for j in range(0, linesNum):
                lineWidget = lineItem[ j ]
                lineEntry  = lineWidget.entry
                if lineEntry.endTime <= currEntry.startTime:
                    found = True
                    lineItem[ j ] = currWidget
                    itemLine[ currWidget ] = j
                    break

            if found is False:
                itemLine[ currWidget ] = linesNum
                lineItem.append( currWidget )

        return (itemLine, len( lineItem ))

    def _lineRect(self, lineIndex, linesNum ) -> QRect:
        lineWidth  = max( 0, int( (self.width() - 16) / linesNum) )
        lineHeight = self.height()
        xPos = lineWidth * lineIndex + 8
        return QRect( xPos, 0, lineWidth, lineHeight)

    def handleItemSelect(self, item: DayItem):
        itemIndex = self.getItemIndex( item )
        self.setCurrentIndex( itemIndex )

    def handleItemDoubleClick(self, item: DayItem):
        itemIndex = self.getItemIndex( item )
        self.entryDoubleClicked.emit( itemIndex )

    def getItemIndex(self, item: DayItem):
        try:
            return self.items.index( item )
        except ValueError:
            _LOGGER.exception("item not found")
            return -1

    def mousePressEvent(self, _):
        self.setCurrentIndex( -1 )

    def mouseDoubleClickEvent(self, _):
        self.entryDoubleClicked.emit( -1 )

    def isSelected(self, item: DayItem):
        if self.currentIndex < 0:
            return False
        itemIndex = self.getItemIndex(item)
        return itemIndex == self.currentIndex


## ===========================================================


class DayListWidget( QWidget ):

    selectedEntry    = pyqtSignal( WorkLogEntry )
    entryUnselected  = pyqtSignal()
    editEntry        = pyqtSignal( WorkLogEntry )

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

#         self.setStyleSheet( "background-color: green" )

        self.data = None
        self.currentDate: date = date.today()

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins( 0, 0, 0, 0 )
        hlayout.setSpacing( 0 )
        self.setLayout( hlayout )

        self.timeline = DayTimeline( self )
        hlayout.addWidget( self.timeline )

        self.content = DayListContentWidget( self )
        hlayout.addWidget( self.content )

        self.timeline.itemClicked.connect( self.unselectItem )
        self.content.selectedEntry.connect( self.handleSelectedEntry )
        self.content.entryDoubleClicked.connect( self.entryDoubleClicked )

    def connectData(self, dataObject):
        self.data = dataObject
        self.data.entryChanged.connect( self.updateView )
        self.editEntry.connect( dataObject.editEntry )

#     def showCompletedTasks(self, show=True):
#         self.content.showCompleted = show
#         self.updateView()

    def updateView(self):
        if self.currentDate is None:
            return
        if self.data is None:
            return
        history: WorkLogData = self.data.history
        entriesList = history.getEntriesForDate( self.currentDate )
        self.setEntries( entriesList, self.currentDate )
        self.update()

    def setCurrentDate(self, currDate: date):
        self.currentDate = currDate
        self.updateView()

    def setEntries(self, entriesList, day: date ):
        self.content.setEntries( entriesList, day )

    def contextMenuEvent( self, _ ):
        entry = self.content.getCurrentEntry()
        create_entry_contextmenu( self, self.data, entry )

    def entryDoubleClicked(self, index):
        entry = self.content.getEntry( index )
        if entry is None:
            return
        self.editEntry.emit( entry )

    def unselectItem(self):
        self.content.setCurrentIndex( -1 )

    def handleSelectedEntry(self, index):
        entry = self.content.getEntry( index )
        self.emitSelectedEntry( entry )

    def emitSelectedEntry( self, entry=None ):
        if entry is not None:
            self.selectedEntry.emit( entry )
        else:
            self.entryUnselected.emit()


## =========================================================


def get_entry_bgcolor( entry: WorkLogEntry, isSelected=False ) -> QColor:
    bgColor = get_entry_base_bgcolor( entry )
    if isSelected:
        red   = min( 255, bgColor.red()   + 40 )
        green = min( 255, bgColor.green() + 40 )
        blue  = min( 255, bgColor.blue()  + 40 )
        bgColor = QColor( red, green, blue, bgColor.alpha() )
    return bgColor


def get_entry_base_bgcolor( entry: WorkLogEntry ) -> QColor:
    if entry.work is False:
        ## not work -- gray
        return QColor( 160, 160, 160 )
    ## normal
    return QColor(0, 220, 0)
