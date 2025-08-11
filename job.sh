#!/bin/bash
set -exr
trap 'exit' SIGHUP SIGINT
echo "${1}"
sleep 25
