#!/usr/bin/env bash
sudo gunicorn -w 4 -b 0.0.0.0:80 app:app
