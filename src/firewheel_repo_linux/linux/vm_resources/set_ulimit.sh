#!/bin/bash

#######################################
# Set's the limit for the number of open files
#######################################

# Check to see if a reboot file exists and if it does
# that means we have set the ulimit and can complete
if [ -e has_rebooted ]
then
    exit 0
fi

FD_LIMIT=$1

# Set the default limit for systemd processes
echo -e "DefaultLimitNOFILE=${FD_LIMIT}" >> /etc/systemd/user.conf
echo -e "DefaultLimitNOFILE=${FD_LIMIT}" >> /etc/systemd/system.conf

# Set the default limit for PAM logged in users
echo -e "* soft nofile ${FD_LIMIT}\n" >> /etc/security/limits.conf
echo -e "* hard nofile ${FD_LIMIT}\n" >> /etc/security/limits.conf
echo -e "root soft nofile ${FD_LIMIT}\n" >> /etc/security/limits.conf
echo -e "root hard nofile ${FD_LIMIT}\n" >> /etc/security/limits.conf

# Set the number of open file max
echo -e "fs.file-max = ${FD_LIMIT}" >> /etc/sysctl.conf

touch reboot
touch has_rebooted
