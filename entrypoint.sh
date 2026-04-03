#!/bin/sh
set -e

cd /app
exec python src/server.py
