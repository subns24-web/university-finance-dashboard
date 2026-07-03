#!/bin/bash
cd "$(dirname "$0")"
export ANTHROPIC_API_KEY=$(grep ANTHROPIC_API_KEY .env | cut -d= -f2)
python3 -m streamlit run app.py --server.port 8501
