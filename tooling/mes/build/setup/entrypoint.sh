#!/bin/bash

if [ -z "${INSTALL_PATH}" ]; then
  echo "Error: INSTALL_PATH environment variable not set"
  exit 1
fi

source "${INSTALL_PATH}/venv/bin/activate"

# Run as the same PID as this script (-u). Must be PID 1 for docker stop to trigger signals
exec python3 -u "${INSTALL_PATH}/src/main.py" replay --dir /datasets/ --host broker --port 1883

exit $?
