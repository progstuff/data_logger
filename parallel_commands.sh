#!/bin/bash
for cmd in "$@"; do {
  echo "Process \"$cmd\" started";
  $cmd & pid=$!
  PID_LIST+=" $pid";
} done
wait $PID_LIST
trap "kill $PID_LIST" SIGINT


