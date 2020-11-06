# Work Log

Track Your work sessions. Simply mark working time periods. 


## Features

- read activity from kern.log
- handle screensaver signals


## Screens

[![Stock table](doc/mainwindow-month-small.png "Month view")](doc/mainwindow-month-big.png)
[![Stock chart](doc/mainwindow-day-small.png "Day view")](doc/mainwindow-day-big.png)


### Examples of not obvious Python mechanisms

- processing data in background thread preventing GUI blockage
- loading of UI files and inheriting from it
- properly killing (Ctrl+C) PyQt (*sigint.py*)
- persisting and versioning classes (*persist.py*)
