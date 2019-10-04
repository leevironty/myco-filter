#!/usr/bin/env bash
gunicorn --reload --daemon --bind localhost:6789 wsgi:app