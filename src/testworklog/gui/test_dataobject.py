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
import datetime

from worklog.gui.dataobject import KernLogParser
from testworklog.data import get_data_path


class KernLogParserTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_parseKernLog_regular(self):
        kernlogPath = get_data_path( "kern.log_regular" )
        logList = KernLogParser.parseKernLog( kernlogPath )
        self.assertEqual( len( logList ), 9 )
        item = logList[0]
        self.assertEqual( item[0], datetime.datetime( year=2020, month=10, day=26, hour=0, minute=9, second=42 ) )
        self.assertEqual( item[1], datetime.datetime( year=2020, month=10, day=26, hour=1, minute=22, second=57 ) )

    def test_parseKernLog_fail(self):
        kernlogPath = get_data_path( "kern.log_fail" )
        logList = KernLogParser.parseKernLog( kernlogPath )
        self.assertEqual( len( logList ), 1 )
        item = logList[0]
        self.assertEqual( item[0], datetime.datetime( year=2020, month=10, day=26, hour=15, minute=49, second=40 ) )
        self.assertEqual( item[1], datetime.datetime( year=2020, month=10, day=26, hour=15, minute=49, second=40 ) )

    def test_parseKernLog_suspend(self):
        kernlogPath = get_data_path( "kern.log_suspend" )
        logList = KernLogParser.parseKernLog( kernlogPath )
        self.assertEqual( len( logList ), 4 )
        item = logList[0]
        self.assertEqual( item[0], datetime.datetime( year=2020, month=10, day=31, hour=10, minute=46, second=16 ) )
        self.assertEqual( item[1], datetime.datetime( year=2020, month=10, day=31, hour=10, minute=53, second=30 ) )
