#!/bin/bash
source .venv/bin/activate
python -c 'from piframe.hardware.power import is_battery_powered;is_battery_powered() and exit(1);'
exit_code=$?
exit $exit_code
