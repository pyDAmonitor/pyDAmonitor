import os
import sys

def get_run_directory():
    """Get the run directory, handling both scripts and Jupyter Notebooks."""
    if 'ipykernel' in sys.modules:  # Running in a Jupyter Notebook
        return os.getcwd()
    else:  # Running as a script
        return os.path.dirname(os.path.abspath(__file__))
