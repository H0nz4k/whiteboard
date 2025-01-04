#!/bin/bash

function set_time() {
  local DATE
  DATE=$(curl -s time.public.altisima.cz)
  RC=$?
  if [ "$RC" = "0" ]; then
    sudo date -s "$DATE"
  fi
}

function fs_lock() {
  sudo mount -o remount,ro /
}

function fs_unlock() {
  sudo mount -o remount,rw /
}

## vrací rw nebo ro
function fs_lock_status() {
  findmnt -n / | awk '{ print $4 }' | awk 'BEGIN{ FS=","} { print $1 }'
}

function set_time_zone() {
  local LOCKED_STATUS
  if [ "$(cat /etc/timezone)" !=  "Europe/Prague" ] || [ "$(readlink /etc/localtime)" != '/usr/share/zoneinfo/Europe/Prague' ]; then
    LOCKED_STATUS=$(fs_lock_status)
    if [ "$LOCKED_STATUS" = "ro" ]; then
        fs_unlock
    fi

    echo 'Europe/Prague' | sudo tee /etc/timezone
    sudo rm -f /etc/localtime
    sudo ln -s /usr/share/zoneinfo/Europe/Prague /etc/localtime

    if [ "$LOCKED_STATUS" = "ro" ]; then
        fs_lock
    fi
  fi
}

set_time
set_time_zone

