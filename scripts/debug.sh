#!/bin/bash
#
# Quick database debug wrapper script for Hippo Bot
#

# Set the database path to the mounted volume
export DATABASE_PATH="./data/hippo.db"

# Run the debug script
python scripts/debug_database.py "$@"