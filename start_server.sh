#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Export Flask environment variables
export FLASK_APP=app
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start the Flask server
flask run
