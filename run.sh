#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Start the API
python main.py &

# Start the Streamlit app on port 8051
streamlit run app.py --server.port 8051
