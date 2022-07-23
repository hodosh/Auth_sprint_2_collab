#!/bin/bash

# Trigger an error if non-zero exit code is encountered
set -e

echo "start"
echo "db init"
flask db init
echo "db migrate"
flask db migrate
echo "db upgrade"
flask db upgrade
echo "create roles"
flask roles create

echo "stop"