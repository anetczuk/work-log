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
from typing import List

from worklog import persist


_LOGGER = logging.getLogger(__name__)


class WorkLogEntry( persist.Versionable ):

    _class_version = 0

    def __init__(self):
        ## Date    In    Out    Break    in_out_diff    Duration    Overtime    Project    Task
        self.entryDate: date     = None
        self.startTime: time     = None
        self.endTime: time       = None
        self.breakTime: time     = None
        self.duration: time      = None
        self.project             = None
        self.task                = None
        self.description         = ""

    def getDuration(self):
        if self.entryDate is None or self.startTime is None or self.endTime is None:
            return self.duration
        dateTimeA = datetime.combine( self.entryDate, self.startTime )
        dateTimeB = datetime.combine( self.entryDate, self.endTime )
        timeDiff = dateTimeB - dateTimeA
        if self.breakTime is not None:
            deltaA = datetime.combine(date.min, self.breakTime) - datetime.min
            timeDiff -= deltaA
            if timeDiff < timedelta():
                timeDiff = timedelta()
        return (datetime.min + timeDiff).time()

    def printData( self ):
        return str( self.entryDate ) + " " + str( self.project ) + " " + str( self.task )


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

    def getEntriesForDate(self, dateValue):
        retList = []
        for entry in self.entries:
            if entry.entryDate == dateValue:
                retList.append( entry )
        return retList

    def getProjectsList(self):
        retSet = list()
        for entry in self.entries:
            if entry.project is None or not entry.project:
                continue
            if entry.project in retSet:
                continue
            retSet.append( entry.project )
        return retSet

    def getTasksList(self):
        retSet = list()
        for entry in self.entries:
            if entry.task is None or not entry.task:
                continue
            if entry.task in retSet:
                continue
            retSet.append( entry.task )
        return retSet

    def addEntry(self, entry):
        self.entries.append( entry )
        self.sort()

    def removeEntry(self, entry):
        self.entries.remove( entry )

    def addEntryTime(self, entryDate: date, startTime: time, endTime: time, project: str, task: str):
        entry = WorkLogEntry()
        entry.entryDate = entryDate
        entry.startTime = startTime
        entry.endTime   = endTime
        ## no break
        ## no duration
        entry.project   = project
        entry.task      = task
        self.addEntry( entry )
        return entry

    def addEntryDuration(self, entryDate: date, duration: time, project: str, task: str):
        entry = WorkLogEntry()
        entry.entryDate = entryDate
        ## no startTime
        ## no endTime
        ## no break
        entry.duration  = duration
        entry.project   = project
        entry.task      = task
        self.addEntry( entry )
        return entry

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
        retDate = entry.entryDate
        if retDate is None:
            return date.min
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
