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
from datetime import datetime, date, time, timedelta

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QTableView
from PyQt5.QtGui import QColor

from worklog.gui.datatypes import WorkLogData, WorkLogEntry
from worklog.gui.dataobject import DataObject, create_entry_contextmenu

from .. import guistate


_LOGGER = logging.getLogger(__name__)


class WorkLogTableModel( QAbstractTableModel ):

    def __init__(self, data: WorkLogData):
        super().__init__()
        self._rawData: WorkLogData = data

    # pylint: disable=R0201
    def getItem(self, itemIndex: QModelIndex):
        if itemIndex.isValid():
            return itemIndex.internalPointer()
        return None

    def setContent(self, data: WorkLogData):
        self.beginResetModel()
        self._rawData = data
        self.endResetModel()

    # pylint: disable=W0613
    def rowCount(self, parent=None):
        if self._rawData is None:
            return 0
        return self._rawData.size()

    # pylint: disable=W0613
    def columnCount(self, parnet=None):
        if self._rawData is None:
            return 0
        attrsList = self.attributeLabels()
        return len( attrsList )

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            attrsList = self.attributeLabels()
            return attrsList[ section ]
        return super().headerData( section, orientation, role )

    ## for invalid parent return elements form root list
    def index(self, row, column, parent: QModelIndex):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        entry = self._rawData.getEntry( row )
        return self.createIndex(row, column, entry)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            entry = self._rawData.getEntry( index.row() )
            rawData = self.attribute( entry, index.column() )
            if rawData is None:
                return "-"
            if isinstance(rawData, time):
                return rawData.strftime("%H:%M")
            if isinstance(rawData, timedelta):
                return print_timedelta( rawData )
            if isinstance(rawData, datetime):
                return rawData.strftime("%Y-%m-%d %H:%M")
            strData = str(rawData)
            return strData

        if role == Qt.UserRole:
            entry = self._rawData.getEntry( index.row() )
            rawData = self.attribute( entry, index.column() )
            return rawData

        if role == Qt.EditRole:
            entry = self._rawData.getEntry( index.row() )
            rawData = self.attribute( entry, index.column() )
            return rawData

        if role == Qt.TextAlignmentRole:
            if index.column() == 4:
                return Qt.AlignLeft | Qt.AlignVCenter
            return Qt.AlignHCenter | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            entry = self._rawData.getEntry( index.row() )
            return get_entry_fgcolor( entry )

        if role == Qt.BackgroundRole:
            entry = self._rawData.getEntry( index.row() )
            weekday = entry.startTime.weekday()
            if weekday == 5 or weekday == 6:
                return QColor( "#FFCC00" )

        return None

    def attribute(self, entry: WorkLogEntry, index):
        if index == 0:
            return entry.startTime
        elif index == 1:
            return entry.endTime
        elif index == 2:
            return entry.getDuration()
        elif index == 3:
            return entry.work
        elif index == 4:
            return entry.description
        return None

    @staticmethod
    def attributeLabels():
        return ( "Start time", "End time", "Duration", "Work", "Description" )


## ===========================================================


class WorkLogSortFilterProxyModel( QtCore.QSortFilterProxyModel ):

    def __init__(self, parentObject=None):
        super().__init__(parentObject)
        self._monthDate = None

    def setMonth(self, year: int, month: int):
        self._monthDate = date( year=year, month=month, day=1 )
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent: QModelIndex):
        startIndex = self.sourceModel().index( sourceRow, 0, sourceParent )
        endIndex   = self.sourceModel().index( sourceRow, 1, sourceParent )
        startData = self.sourceModel().data(startIndex, QtCore.Qt.EditRole)
        endData   = self.sourceModel().data(endIndex, QtCore.Qt.EditRole)
        if startData is None or endData is None:
            return True

        if self._monthDate is None:
            return True

        if startData.year > self._monthDate.year or endData.year < self._monthDate.year:
            return False
        if startData.year == self._monthDate.year:
            if startData.month > self._monthDate.month:
                return False
        if endData.year == self._monthDate.year:
            if endData.month < self._monthDate.month:
                return False

        return True


## ===========================================================


class WorkLogTable( QTableView ):

    selectedItem    = pyqtSignal( WorkLogEntry )
    itemUnselected  = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.setObjectName("worklogtable")

        self.dataObject = None

        self.setSortingEnabled( True )
        self.setShowGrid( False )
        self.setAlternatingRowColors( True )
#         self.setEditTriggers( QAbstractItemView.DoubleClicked )

        header = self.horizontalHeader()
        header.setDefaultAlignment( Qt.AlignCenter )
        header.setHighlightSections( False )
        header.setStretchLastSection( True )

        self.verticalHeader().hide()

        self.dataModel = WorkLogTableModel( None )
        self.proxyModel = WorkLogSortFilterProxyModel(self)
        self.proxyModel.setSourceModel( self.dataModel )
        self.setModel( self.proxyModel )

    def setMonth(self, year: int, month: int):
        self.proxyModel.setMonth( year, month )

    def loadSettings(self, settings):
        wkey = guistate.get_widget_key(self, "tablesettings")
        settings.beginGroup( wkey )
        visDict = settings.value("columnsVisible", None, type=dict)
        if visDict is None:
            visDict = dict()

    def saveSettings(self, settings):
        wkey = guistate.get_widget_key(self, "tablesettings")
        settings.beginGroup( wkey )
        settings.setValue("columnsVisible", self.columnsVisible )
        settings.endGroup()

    ## ===============================================

    def connectData(self, dataObject: DataObject ):
        self.dataObject = dataObject
        self.dataObject.entryChanged.connect( self.refreshData )
        self.refreshData()

    def refreshData(self):
        history: WorkLogData = self.dataObject.history
        self.dataModel.setContent( history )
        self.clearSelection()
#         _LOGGER.debug( "entries: %s\n%s", type(history), history.printData() )

    def getItem(self, itemIndex: QModelIndex ) -> WorkLogEntry:
        sourceIndex = self.proxyModel.mapToSource( itemIndex )
        return self.dataModel.getItem( sourceIndex )

    def contextMenuEvent( self, event ):
        evPos               = event.pos()
        entry: WorkLogEntry = None
        mIndex = self.indexAt( evPos )
        if mIndex is not None:
            entry = self.getItem( mIndex )

        create_entry_contextmenu( self, self.dataObject, entry )

    def currentChanged(self, current, previous):
        super().currentChanged( current, previous )
        item = self.getItem( current )
        if item is not None:
            self.selectedItem.emit( item )
        else:
            self.itemUnselected.emit()

    def mouseDoubleClickEvent( self, event ):
        evPos               = event.pos()
        entry: WorkLogEntry = None
        mIndex = self.indexAt( evPos )
        if mIndex is not None:
            entry = self.getItem( mIndex )

        if entry is None:
            self._addEntry()
        else:
            self._editEntry(entry)

        return super().mouseDoubleClickEvent(event)

    def _addEntry(self):
        self.dataObject.addEntry()

    def _editEntryByIndex(self, item: QModelIndex):
        history = self.dataObject.history
        entry = history.getEntry( item.row() )
        self._editEntry( entry )

    def _editEntry(self, entry):
        self.dataObject.editEntry(entry)

    def _removeEntry(self, entry):
        self.dataObject.removeEntry(entry)


def print_timedelta( value: timedelta ):
    s = ""
    secs = value.seconds
    days = value.days
    if secs != 0 or days == 0:
        mm, _ = divmod(secs, 60)
        hh, mm = divmod(mm, 60)
        s = "%d:%02d" % (hh, mm)
#         s = "%d:%02d:%02d" % (hh, mm, ss)
    if days:
        def plural(n):
            return n, abs(n) != 1 and "s" or ""
        if s != "":
            s = ("%d day%s, " % plural(days)) + s
        else:
            s = ("%d day%s" % plural(days)) + s
#     micros = value.microseconds
#     if micros:
#         s = s + ".%06d" % micros
    return s


def get_entry_fgcolor( entry: WorkLogEntry ) -> QtGui.QBrush:
    if entry.work is False:
        ## not work -- gray
        return QtGui.QBrush( QColor( 160, 160, 160 ) )
    ## normal
    return QtGui.QBrush( QColor(0, 0, 0) )
