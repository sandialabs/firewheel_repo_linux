#!/bin/sh

# Reference: https://gist.github.com/noromanba/6e062d38fd7fd2cd609a6ef1c26ea7bc
# Accessed January 18, 2018
echo "Disabling apt-daily.service and apt-daily.timer"
systemctl stop apt-daily.service
systemctl stop apt-daily.timer
systemctl disable apt-daily.timer
systemctl mask apt-daily.service
systemctl daemon-reload

echo "Checking apt-daily status"
systemctl status apt-daily.service
systemctl status apt-daily.timer

echo "Killing running apt processes"
pkill -f -9 '/apt/apt.systemd' -e
pkill -f -9 '/usr/bin/unattended-upgrade' -e
