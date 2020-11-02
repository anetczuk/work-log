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
from enum import Enum, unique

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon, QPainter, QPainterPath, QBrush, QColor, QPen
from PyQt5.QtWidgets import QApplication, qApp
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction

from worklog.gui import resources


_LOGGER = logging.getLogger(__name__)


@unique
class TrayIconTheme(Enum):
    WHITE         = ['worklog-white.png', 'worklog-white-red.png']
    BLACK         = ['worklog-black.png', 'worklog-black-red.png']

    def __init__(self, fileNamesList):
        self._normal  = fileNamesList[0]
        self._working = fileNamesList[1]

    @property
    def normal(self):
        return self._normal

    @property
    def working(self):
        return self._working

    @classmethod
    def findByName(cls, name):
        for item in cls:
            if item.name == name:
                return item
        return None

    @classmethod
    def indexOf(cls, key):
        index = 0
        for item in cls:
            if item == key:
                return index
            if item.name == key:
                return index
            index = index + 1
        return -1


def load_main_icon( theme: TrayIconTheme ):
    fileName = theme.normal
    return load_icon( fileName )


def load_icon( fileName: str ):
    iconPath = resources.get_image_path( fileName )
    _LOGGER.debug("loading icon %s", iconPath)
    return QIcon( iconPath )


class TrayIcon(QSystemTrayIcon):

    workLoggingChanged = pyqtSignal( bool )

    def __init__(self, parent):
        super().__init__(parent)

        self.activated.connect( self._iconActivated )

        tray_menu = QMenu()

        self.toggle_window_action = QAction("Show", self)
        self.toggle_window_action.triggered.connect( self._toggleParent )
        tray_menu.addAction( self.toggle_window_action )

        self.workLoggingAction = QAction("Work logging", self)
        self.workLoggingAction.setCheckable( True )
        self.workLoggingAction.triggered.connect( self._switchWorkLogging )
        tray_menu.addAction( self.workLoggingAction )
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect( qApp.quit )
        tray_menu.addAction( quit_action )

        self.setContextMenu( tray_menu )

    def displayMessage(self, message):
        timeout = 10000
        ## under xfce4 there is problem with balloon icon -- it changes tray icon, so
        ## it cannot be changed back to proper one. Workaround is to use NoIcon parameter
        self.showMessage("Work Log", message, QSystemTrayIcon.NoIcon, timeout)

    def drawNumber( self, number, numColor=QColor("red") ):
        icon = self.icon()

        pixmap = icon.pixmap( 512, 512 )
        pixSize = pixmap.rect()

        painter = QPainter( pixmap )

        font = painter.font()
        font.setPixelSize( 256 + 128 )
        painter.setFont(font)

        path = QPainterPath()
        path.addText( 0, 0, font, str(number) )
        pathBBox = path.boundingRect()

        xOffset = ( pixSize.width() - pathBBox.width() ) / 2 - pathBBox.left()
        yOffset = ( pixSize.height() + pathBBox.height() ) / 2

        path.translate( xOffset, yOffset )

#         pathPen = QPen(QColor("black"))
        pathPen = QPen( QColor(0, 0, 0, 200) )
        pathPen.setWidth( 180 )
        painter.strokePath( path, pathPen )

        painter.fillPath( path, QBrush(numColor) )

        ## make number bolder
        pathPen = QPen( numColor )
        pathPen.setWidth( 20 )
        painter.strokePath( path, pathPen )

        painter.end()

        self.setIcon( QIcon( pixmap ) )

    def setWorkLogging(self, value: bool):
        self.workLoggingAction.setChecked( value )

    def _iconActivated(self, reason):
#         print("tray clicked, reason:", reason)
        if reason == 3:
            ## clicked
            self._toggleParent()

    def _toggleParent(self):
        parent = self.parent()
        self.updateLabel()
        if parent.isHidden() is False:
            ## hide window
            parent.hide()
            return
        ## show
        if parent.isMinimized():
            parent.showNormal()
        else:
            parent.show()
        QApplication.setActiveWindow( parent )      ## fix for KDE

    def _switchWorkLogging(self):
        checked = self.workLoggingAction.isChecked()
        self.workLoggingChanged.emit( checked )

    def updateLabel(self):
        parent = self.parent()
        if parent.isHidden():
            self.toggle_window_action.setText("Show")
        else:
            self.toggle_window_action.setText("Hide")
