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
from typing import List, Tuple

from worklog import persist


_LOGGER = logging.getLogger(__name__)


class WorkLogEntry( persist.Versionable ):

    # 1: added "description" field
    _class_version = 1

    def __init__(self):
        self.startTime: datetime = None
        self.endTime: datetime   = None
        self.description         = ""

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ < 1:
            # pylint: disable=W0201
            dict_["description"] = ""

        # pylint: disable=W0201
        self.__dict__ = dict_

    def getDuration(self):
        return self.endTime - self.startTime

    def calculateTimeSpan(self, entryDate: date):
        startDate: datetime = self.startTime
        endDate: datetime   = self.endTime
        return calc_time_span( entryDate, startDate, endDate )

    def printData( self ):
        return str( self.startTime ) + " " + str( self.getDuration() )


class WorkLogData( persist.Versionable ):

    ## 1 - rename field
    _class_version = 1

    def __init__(self):
        self.entries: List[ WorkLogEntry ] = list()

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ < 1:
            ## skip old version data
            self.entries = list()
            return

        # pylint: disable=W0201
        self.__dict__ = dict_

    ## [] (array) operator
    def __getitem__(self, arg):
        return self.getEntry( arg )

    def size(self):
        return len( self.entries )

    def getEntry(self, row) -> WorkLogEntry:
        return self.entries[ row ]

    def recentEntry(self) -> WorkLogEntry:
        if self.entries:
            return self.entries[-1]
        return None

    def getEntriesForDate(self, dateValue: date) -> List[ WorkLogEntry ]:
        retList = []
        for entry in self.entries:
            startDate = entry.startTime.date()
            endDate   = entry.endTime.date()
            if startDate <= dateValue and endDate >= dateValue:
                retList.append( entry )
                continue
        return retList

    def findEntriesInRange(self, fromDate: datetime, toDate: datetime) -> List[ WorkLogEntry ]:
        retList = []
        for entry in self.entries:
            if entry.endTime < fromDate:
                continue
            if entry.startTime > toDate:
                continue
            retList.append( entry )
        return retList

    def addEntry(self, entry):
        self.entries.append( entry )
        self.sort()

    def removeEntry(self, entry):
        self.entries.remove( entry )

    def joinEntryUp(self, entry):
        try:
            entryIndex = self.entries.index( entry )
            if entryIndex < 1:
                ## first element
                return
            prevEntry = self.entries[ entryIndex - 1 ]
            prevEntry.endTime = entry.endTime
            if entry.description:
                prevEntry.description += "\n" + entry.description
            self.entries.remove( entry )
        except ValueError:
            print("entry:", entry, self.entries)
            raise

    def joinEntryDown(self, entry):
        entryIndex = self.entries.index( entry )
        if entryIndex == len( self.entries ) - 1:
            ## last element
            return
        nextEntry = self.entries[ entryIndex + 1 ]
        nextEntry.startTime = entry.startTime
        if entry.description:
            nextEntry.description = entry.description + "\n" + nextEntry.description
        self.entries.remove( entry )

    def addEntryTime(self, entryDate: date, startTime: time, endTime: time, desc: str = ""):
        dateTimeStart = datetime.combine( entryDate, startTime )
        dateTimeEnd   = datetime.combine( entryDate, endTime )
        entry = WorkLogEntry()
        entry.startTime   = dateTimeStart
        entry.endTime     = dateTimeEnd
        entry.description = desc
        self.addEntry( entry )
        return entry

    def addEntryTimeList(self, timeList: List[ Tuple[datetime, datetime] ]):
        for span in timeList:
            entry = WorkLogEntry()
            entry.startTime = span[0]
            entry.endTime   = span[1]
            self.addEntry( entry )

    def replaceEntry( self, oldEntry: WorkLogEntry, newEntry: WorkLogEntry ):
        _LOGGER.debug( "replacing entry %s with %s", oldEntry, newEntry )
        for i, _ in enumerate( self.entries ):
            currItem = self.entries[i]
            if currItem == oldEntry:
                self.entries[i] = newEntry
                self.sort()
                return True
        _LOGGER.debug( "replacing failed" )
        return False

    def sort(self):
        self.entries.sort( key=self._sortKey, reverse=False )

    @staticmethod
    def _sortKey( entry: WorkLogEntry ):
        retDate = entry.startTime
        if retDate is None:
            return datetime.min
        return retDate

    def printData( self ):
        retStr = ""
        for currItem in self.entries:
            retStr += "item: " + currItem.printData() + "\n"
        return retStr


## ==================================================================


class DataContainer( persist.Versionable ):

    ## 0 - first version
    ## 1 - add worklog history
    _class_version = 1

    def __init__(self):
        self.history: WorkLogData = WorkLogData()
        self.notes                = { "notes": "" }        ## default notes


## ==================================================================


def calc_time_span(entryDate: date, start: datetime, end: datetime):
    midnight = datetime.combine( entryDate, datetime.min.time() )
    daySecs  = timedelta( days=1 ).total_seconds()
    startFactor = 0.0
    if start is not None:
        startDate = start.date()
        if entryDate < startDate:
            return None
        elif entryDate == startDate:
            startDiff = start - midnight
            startFactor = startDiff.total_seconds() / daySecs
    dueFactor = 1.0
    if end is not None:
        endDate = end.date()
        if entryDate > endDate:
            return None
        elif entryDate == endDate:
            startDiff = end - midnight
            dueFactor = startDiff.total_seconds() / daySecs
    ret = [startFactor, dueFactor]
    return ret
