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

from worklog.gui.datatypes import WorkLogEntry

from .. import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


_LOGGER = logging.getLogger(__name__)


class EntryDetailsWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.entry = None
        self.setObject( self.entry )

    def setObject(self, entry: WorkLogEntry):
        self.entry = entry
        if self.entry is None:
            return

        self.ui.startTime.setText( str( self.entry.startTime ) )
        self.ui.endTime.setText( str( self.entry.endTime ) )
        self.ui.durationTime.setText( str( self.entry.getDuration() ) )
        self.ui.description.setText( str( self.entry.description ) )
