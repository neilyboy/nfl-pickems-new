#!/bin/bash

# Kill any running Flask servers
pkill -f "flask run"

# Deactivate virtual environment if it's active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    deactivate
fi
