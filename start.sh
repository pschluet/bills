#!/usr/bin/env bash
sudo venv/bin/gunicorn -w 4 -b 0.0.0.0:80 app:app
