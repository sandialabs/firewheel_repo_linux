#!/bin/bash

# Take in debconf lines and apply them

while read line
do
    debconf-set-selections <<< $line
done < $1
