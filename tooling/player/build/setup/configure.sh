#!/bin/bash

if [ -z "${INSTALL_PATH}" ]; then
  echo "Error: INSTALL_PATH environment variable not set"
  exit 1
fi

# Install Python Dependencies
python3 -m venv "${INSTALL_PATH}/venv"
source "${INSTALL_PATH}/venv/bin/activate"
pip install -r "${INSTALL_PATH}/requirements.txt"
deactivate

