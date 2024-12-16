#!/bin/bash

if [ -f "done" ] ; then
    exit 0
fi

if [ -f /etc/debian_version ] ; then
    # Put the hostname in the hostname file
    echo $1 > /etc/hostname
    # Add hostname to /etc/hosts so that it can be resolved
    sed -i '/127.0.0.1/c\127.0.0.1\tlocalhost '$1 /etc/hosts
    sed -i '/127.0.1.1*/d' /etc/hosts
    hostname $1
fi

if [ -f /etc/redhat-release ] ; then
    echo $1 > /etc/hostname
    sed -i '/127.0.0.1/c\127.0.0.1\t localhost localhost.localdomain localhost4 localhost4.localdomain4 '$1 /etc/hosts
    hostname $1
fi
