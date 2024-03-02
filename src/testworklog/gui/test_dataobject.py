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

import unittest
import os
import datetime

from worklog.gui.dataobject import SysLogParser
from testworklog.data import get_data_path


class SysLogParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # set datetime of file to properly deduce and test log year
        kernlogPath = get_data_path( "kern.log_regular" )
        mod_datetime = datetime.datetime( year=2020, month=10, day=2, hour=0, minute=1 )
        dt_epoch = mod_datetime.timestamp()
        os.utime(kernlogPath, (dt_epoch, dt_epoch))

    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_parseLogFile_regular(self):
        kernlogPath = get_data_path( "kern.log_regular" )
        logList = SysLogParser.parseLogFile( kernlogPath )
        self.assertEqual( len( logList ), 9 )
        item = logList[0]
        self.assertEqual( item[0], datetime.datetime( year=2020, month=10, day=26, hour=0, minute=9 ) )
        self.assertEqual( item[1], datetime.datetime( year=2020, month=10, day=26, hour=1, minute=22 ) )

    def test_parseLogFile_fail(self):
        kernlogPath = get_data_path( "kern.log_fail" )
        logList = SysLogParser.parseLogFile( kernlogPath )
        self.assertEqual( len( logList ), 1 )
        item = logList[0]
        self.assertEqual( item[0], datetime.datetime( year=2020, month=10, day=26, hour=15, minute=49 ) )
        self.assertEqual( item[1], datetime.datetime( year=2020, month=10, day=26, hour=15, minute=49 ) )

    def test_parseLogFile_suspend(self):
        kernlogPath = get_data_path( "kern.log_suspend" )
        logList = SysLogParser.parseLogFile( kernlogPath )
        self.assertEqual( len( logList ), 4 )
        item = logList[0]
        self.assertEqual( item[0], datetime.datetime( year=2020, month=10, day=31, hour=10, minute=46 ) )
        self.assertEqual( item[1], datetime.datetime( year=2020, month=10, day=31, hour=10, minute=53 ) )

    def test_parseLogFile_newyear(self):
        kernlogPath = get_data_path( "kern.log_newyear" )
        logList = SysLogParser.parseLogFile( kernlogPath )
        self.assertEqual( len( logList ), 2 )
        item1 = logList[0]
        self.assertEqual( item1[0], datetime.datetime( year=2020, month=12, day=31, hour=18, minute=28 ) )
        self.assertEqual( item1[1], datetime.datetime( year=2020, month=12, day=31, hour=18, minute=32 ) )
        item2 = logList[1]
        self.assertEqual( item2[0], datetime.datetime( year=2021, month=1, day=1, hour=20, minute=30 ) )
        self.assertEqual( item2[1], datetime.datetime( year=2021, month=1, day=1, hour=20, minute=32 ) )

    def test_parseLogFile_joinline(self):
        ## sometimes can happen that two lines of log are joined together without newline separator
        kernlogPath = get_data_path( "kern.log_joinline" )
        logList = SysLogParser.parseLogFile( kernlogPath )
        self.assertEqual( len( logList ), 2 )
        item1 = logList[0]
        self.assertEqual( item1[0], datetime.datetime( year=2021, month=5, day=7, hour=23, minute=24 ) )
        self.assertEqual( item1[1], datetime.datetime( year=2021, month=5, day=7, hour=23, minute=24 ) )
        item2 = logList[1]
        self.assertEqual( item2[0], datetime.datetime( year=2021, month=5, day=8, hour=21, minute=35 ) )
        self.assertEqual( item2[1], datetime.datetime( year=2021, month=5, day=8, hour=21, minute=35 ) )

    def test_parseLogFile_leapyear(self):
        ## parse date Feb 29
        kernlogPath = get_data_path( "kern.log_leap" )
        logList = SysLogParser.parseLogFile( kernlogPath )
        self.assertEqual( len( logList ), 1 )
        item1 = logList[0]
        self.assertEqual( item1[0], datetime.datetime( year=2024, month=2, day=29, hour=0, minute=0 ) )
        self.assertEqual( item1[1], datetime.datetime( year=2024, month=2, day=29, hour=0, minute=0 ) )

    def test_parseSysLog_regular(self):
        kernlogPath = get_data_path( "syslog_regular" )
        logList = SysLogParser.parseLogFile( kernlogPath )
        self.assertEqual( len( logList ), 2 )
        # year of last modification
        item = logList[0]
        self.assertEqual( item[0], datetime.datetime( year=2023, month=10, day=26, hour=0, minute=8 ) )
        self.assertEqual( item[1], datetime.datetime( year=2023, month=10, day=26, hour=1, minute=32 ) )
        item = logList[1]
        self.assertEqual( item[0], datetime.datetime( year=2023, month=10, day=26, hour=15, minute=48 ) )
        self.assertEqual( item[1], datetime.datetime( year=2023, month=10, day=26, hour=16, minute=38 ) )
