"""Gets app configuration from environment variables, and defines
default values if environment variable not available.
"""
import os

try:
    REDIS_HOST = os.environ["REDIS_HOST"]
except KeyError:
    REDIS_HOST = "0.0.0.0"

try:
    REDIS_PORT = os.environ["REDIS_PORT"]
except KeyError:
    REDIS_PORT = "6379"

try:
    REDIS_QUEUE = os.environ["REDIS_QUEUE"]
except KeyError:
    REDIS_QUEUE = "default"

try:
    FLASK_HOST = os.environ["FLASK_HOST"]
except KeyError:
    FLASK_HOST = "0.0.0.0"

try:
    FLASK_PORT = os.environ["FLASK_PORT"]
except KeyError:
    FLASK_PORT = "5000"
