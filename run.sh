#!/bin/bash
# Simple script to run CHRplunk without installing

cd "$(dirname "$0")"
python3 chrplunk-app.py "$@"
