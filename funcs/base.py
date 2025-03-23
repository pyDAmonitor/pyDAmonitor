import os
import sys
import subprocess

def source(bash_file,optional=False):
  """
  Source a Bash file and capture the environment variables
  """
  #check if bash_file exists
  command = f"source {bash_file} && env"
  proc = subprocess.Popen(
    ['bash', '-c', command],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True
  )
  stdout, stderr = proc.communicate()
  if proc.returncode != 0:
    if optional:
      return #do nothing for optional config files
    else:
      raise Exception(f"Error sourcing bash file: {stderr}")
  env_vars = {}
  for line in stdout.splitlines():
    key, _, value = line.partition("=")
    env_vars[key] = value
  # Update the current environment
  os.environ.update(env_vars)
### end of source(bash_file)

def get_run_directory():
    """Get the run directory, handling both scripts and Jupyter Notebooks."""
    if 'ipykernel' in sys.modules:  # Running in a Jupyter Notebook
        return os.getcwd()
    else:  # Running as a script
        return os.path.dirname(os.path.abspath(__file__))
