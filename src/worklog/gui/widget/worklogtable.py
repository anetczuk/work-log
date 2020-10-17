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

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtWidgets import QTableView

from worklog.gui.datatypes import WorkLogData, WorkLogEntry
from worklog.gui.dataobject import DataObject
from worklog.gui.widget.entrydialog import EntryDialog
from worklog.gui.command.editentrycommand import EditEntryCommand

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
            return Qt.AlignHCenter | Qt.AlignVCenter

        return None

    def attribute(self, entry: WorkLogEntry, index):
        if index == 0:
            return entry.entryDate
        elif index == 1:
            return entry.startTime
        elif index == 2:
            return entry.endTime
        elif index == 3:
            return entry.breakTime
        elif index == 4:
            return entry.duration
        elif index == 5:
            return entry.project
        elif index == 6:
            return entry.task
        elif index == 7:
            return entry.description
        return None

    @staticmethod
    def attributeLabels():
        return ( "date", "start time", "end time", "break", "duration", "project", "task", "description" )


## ===========================================================


class WorkLogSortFilterProxyModel( QtCore.QSortFilterProxyModel ):

    def __init__(self, parentObject=None):
        super().__init__(parentObject)
        self._scope     = "Month"
        self._dayDate   = None
        self._monthDate = None

    def setScope(self, scope: str):
        self._scope = scope
        self.invalidateFilter()

    def setDay(self, dateValue: date):
        self._dayDate = dateValue
        self.invalidateFilter()

    def setMonth(self, year: int, month: int):
        self._monthDate = date( year=year, month=month, day=1 )
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent: QModelIndex):
        if self._dayDate is None:
            return True
        if self._monthDate is None:
            return True

        dataIndex = self.sourceModel().index( sourceRow, 0, sourceParent )
        data = self.sourceModel().data(dataIndex, QtCore.Qt.EditRole)

        if self._scope == "Day":
            return data == self._dayDate
        if self._scope == "Month":
            if data.year != self._monthDate.year:
                return False
            if data.month != self._monthDate.month:
                return False
            return True
        if self._scope == "Year":
            if data.year != self._monthDate.year:
                return False
            return True
        if self._scope == "All":
            return True

        _LOGGER.warning( "unknown scope value: %s", self._scope )
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

        self.doubleClicked.connect( self._editEntry )

    def setScope(self, scope: str):
        self.proxyModel.setScope( scope )

    def setDay(self, dateValue: date):
        self.proxyModel.setDay( dateValue )

    def setMonth(self, year: int, month: int):
        self.proxyModel.setMonth( year, month )

    def loadSettings(self, settings):
        wkey = guistate.get_widget_key(self, "tablesettings")
        settings.beginGroup( wkey )
        visDict = settings.value("columnsVisible", None, type=dict)
        if visDict is None:
            visDict = dict()
        headersDict = settings.value("customHeaders", None, type=dict)
        settings.endGroup()
        self.setColumnsVisibility( visDict )
        if headersDict is not None:
            self.pandaModel.setHeaders( headersDict )

    def saveSettings(self, settings):
        wkey = guistate.get_widget_key(self, "tablesettings")
        settings.beginGroup( wkey )
        settings.setValue("columnsVisible", self.columnsVisible )
        settings.setValue("customHeaders", self.pandaModel.customHeader )
        settings.endGroup()

    ## ===============================================

    def connectData(self, dataObject: DataObject ):
        self.dataObject = dataObject
        self.dataObject.entryChanged.connect( self.refreshData )
        self.refreshData()

    def refreshData(self):
        history: WorkLogData = self.dataObject.history
        self.dataModel.setContent( history )
#         _LOGGER.debug( "entries: %s\n%s", type(history), history.printData() )

    def getItem(self, itemIndex: QModelIndex ) -> WorkLogEntry:
        sourceIndex = self.proxyModel.mapToSource( itemIndex )
        return self.dataModel.getItem( sourceIndex )

    def currentChanged(self, current, previous):
        super().currentChanged( current, previous )
        item = self.getItem( current )
        if item is not None:
            self.selectedItem.emit( item )
        else:
            self.itemUnselected.emit()

    def _editEntry(self, item: QModelIndex):
        history = self.dataObject.history
        entry = history.getEntry( item.row() )
        if entry is None:
            return
        parentWidget = self.parent()
        entryDialog = EntryDialog( entry, parentWidget )
        entryDialog.setModal( True )
        dialogCode = entryDialog.exec_()
        if dialogCode == QtWidgets.QDialog.Rejected:
            return
        command = EditEntryCommand( self.dataObject, entry, entryDialog.entry )
        self.dataObject.pushUndo( command )
