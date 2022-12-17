#!/usr/bin/env bash

USER=`whoami`
echo -n "Enter username used to run XmasShowPi [$USER]: "
read IN_USER
if [ -n "$IN_USER" ]; then
	USER=$IN_USER
fi
EXEC_DIR="/home/$USER/XmasShowPi"
if [ ! -d "$EXEC_DIR" ]; then
	echo "User $USER directory doesnt exist: $EXEC_DIR"
	exit -1
fi
if [ ! -f "$EXEC_DIR/XmasShowPi.py" ]; then
	echo "XmasShowPi.py doesnt exist: $EXEC_DIR/XmasShowPi.py"
	exit -1
fi

EXEC="sudo -u $USER /usr/bin/python3 -u $EXEC_DIR/XmasShowPi.py"

SERVICE_SH="$EXEC_DIR/xmasshowpi_service.sh"
echo '#!/usr/bin/env bash' >> $SERVICE_SH
echo "EXEC_DIR='$EXEC_DIR'" >> $SERVICE_SH
echo "EXEC='$EXEC'" >> $SERVICE_SH
echo 'Starting XmasShowPi' >> $SERVICE_SH
echo 'cd $EXEC_DIR && $EXEC' >> $SERVICE_SH

INSTALL_SERVICE_SH="/usr/local/bin/xmasshowpi_service.sh"
sudo cp $SERVICE_SH $INSTALL_SERVICE_SH
sudo chmod 755 $INSTALL_SERVICE_SH
sudo cp $EXEC_DIR/xmasshowpi.service /lib/systemd/system
sudo cp $EXEC_DIR/xmasshowpi.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/xmasshowpi.service
sudo systemctl daemon-reload

