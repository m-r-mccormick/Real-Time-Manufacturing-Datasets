#!/bin/bash

if [ -z "${INSTALL_PATH}" ]; then
  echo "Error: INSTALL_PATH environment variable not set"
  exit 1
fi

source "${INSTALL_PATH}/venv/bin/activate"

if [ -z "${MODE}" ]; then
  echo "Error: MODE environment variable must be defined"
  exit 1
fi

if [ -z "${BROKER_HOST}" ]; then
  echo "Error: BROKER_HOST environment variable must be defined"
  exit 1
fi

if [ -z "${BROKER_PORT}" ]; then
  echo "Error: BROKER_PORT environment variable must be defined"
  exit 1
fi

echo "MODE:                ${MODE}"
echo "BROKER_HOST:         ${BROKER_HOST}"
echo "BROKER_PORT:         ${BROKER_PORT}"
echo "BROKER_SUBSCRIPTION: ${BROKER_SUBSCRIPTION}"

if [ "${MODE}" == "capture" ]; then
  if [ -z "${BROKER_SUBSCRIPTION}" ]; then
    echo "Error: BROKER_SUBSCRIPTION environment variable must be defined in 'capture' MODE"
    exit 1
  fi
fi

if [ "${MODE}" == "replay" ]; then
  # Run as the same PID as this script (-u). Must be PID 1 for docker stop to trigger signals
  exec python3 -u "${INSTALL_PATH}/src/main.py" replay --dir /datasets/ --host ${BROKER_HOST} --port ${BROKER_PORT}
elif [ "${MODE}" == "capture" ]; then
  # Run as the same PID as this script (-u). Must be PID 1 for docker stop to trigger signals
  exec python3 -u "${INSTALL_PATH}/src/main.py" capture --dir /datasets/ --host ${BROKER_HOST} --port ${BROKER_PORT} --sub ${BROKER_SUBSCRIPTION}
else
  echo "Error: MODE environment variable must be 'replay' or 'capture'. Specified MODE: '${MODE}'"
  sleep 10
  exit 1
fi

exit $?
