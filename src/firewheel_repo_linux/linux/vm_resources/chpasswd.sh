#!/bin/bash

USERNAME=$1
PASSWORD=$2

echo "${USERNAME}:${PASSWORD}" | chpasswd
