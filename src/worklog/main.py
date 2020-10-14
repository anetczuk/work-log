#!/usr/bin/python3
#
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

import sys

import argparse
import logging

from PyQt5.QtWidgets import QApplication, QMessageBox

import worklog.logger as logger

from worklog.gui.mainwindow import MainWindow
from worklog.gui.sigint import setup_interrupt_handling
from worklog.gui.appwindow import AppWindow


logger.configure()
_LOGGER = logging.getLogger(__name__)


def run_app():
    ## GUI
    app = QApplication( sys.argv )
    app.setApplicationName("WorkLog")
    app.setOrganizationName("arnet")
    ### app.setOrganizationDomain("www.my-org.com")
    app.setQuitOnLastWindowClosed( False )

    setup_interrupt_handling()

    try:
        window = MainWindow()
        window.loadData()
        window.loadSettings()

        window.show()

        exitCode = app.exec_()

        if exitCode == 0:
            window.saveAll()

        return exitCode
    except BaseException as e:
        QMessageBox.critical( None, AppWindow.appTitle, str(e) + "\n\nInvestigate application logs for details" )
        raise


def create_parser( parser: argparse.ArgumentParser = None ):
    if parser is None:
        parser = argparse.ArgumentParser(description='Work Log')
    parser.add_argument('--minimized', action='store_const', const=True, default=False, help='Start minimized' )
    return parser


def main( args=None ):
    if args is None:
        parser = create_parser()
        args = parser.parse_args()

    _LOGGER.debug( "Starting the application" )
    _LOGGER.debug( "Logger log file: %s", logger.log_file )

    exitCode = 1

    try:
        exitCode = run_app()

    except BaseException:
        _LOGGER.exception("Exception occurred")
        raise

    finally:
        sys.exit(exitCode)

    return exitCode


if __name__ == '__main__':
    main()
