#!/bin/bash
source .venv/bin/activate
streamlit run piframe/app/configurator.py --server.headless=true --server.address=0.0.0.0 --server.port=8080 --browser.gatherUsageStats=false