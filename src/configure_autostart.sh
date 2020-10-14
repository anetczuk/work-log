#!/bin/bash


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


## add udev rule
AUTOSTART_FILE=~/.config/autostart/worklog.desktop


cat > $AUTOSTART_FILE << EOL
[Desktop Entry]
Name=Work Log
GenericName=Work Log
Comment=Track Your work sessions.
Type=Application
Categories=Office;
Exec=$SCRIPT_DIR/startworklog --minimized
Icon=$SCRIPT_DIR/worklog/gui/img/worklog-black.png
Terminal=false
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOL


echo "File created in: $AUTOSTART_FILE"
