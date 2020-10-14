#!/bin/bash


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


## add udev rule
AUTOSTART_FILE=~/.local/share/applications/menulibre-worklog.desktop


cat > $AUTOSTART_FILE << EOL
[Desktop Entry]
Name=Work Log
GenericName=Work Log
Comment=Track Your work sessions.
Version=1.1
Type=Application
Exec=$SCRIPT_DIR/startworklog
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/worklog/gui/img/worklog-black.png
Actions=
Categories=Office;
StartupNotify=true
Terminal=false

EOL


echo "File created in: $AUTOSTART_FILE"
