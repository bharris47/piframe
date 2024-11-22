#!/bin/bash
source .venv/bin/activate
streamlit run --server.address, 0.0.0.0 --server.headless true --serverPort 8080 piframe/app/configurator.py