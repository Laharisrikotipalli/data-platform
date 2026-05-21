# tests/conftest.py
"""
Shared pytest fixtures for the data-platform test suite.
"""
import os
import sys

import pytest

# Ensure both source directories are on the path
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "data_api"))
sys.path.insert(0, os.path.join(ROOT, "airflow", "dags"))