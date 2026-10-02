"""Populate the shared static volume, then replace this process with Gunicorn."""
import os
import subprocess
import sys

if sys.argv[1:2] == ['gunicorn']:
    subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], check=True)
os.execvp(sys.argv[1], sys.argv[1:])
