#!/bin/bash
source .venv/bin/activate
streamlit run --serverAddress 0.0.0.0 --serverPort 8080 piframe/app/configurator.py