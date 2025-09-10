[pyDAmonitor Book](https://pyDAmonitor.github.io/docs): showcase plots and results

# pyDAmonitor
Safeguarding invaluable DA investments by vigilantly monitoring DA performance both in real-time and retrospective scenarios.

# Installation
```
git clone https://github.com/pyDAmonitor/pyDAmonitor.git
conda env create -f pyDAmonitor/environment.yaml
conda activate pyDAmonitor
```
Note: The `pyDAmonitor` Python environment is already installed on `Jet/Hera/Ursa/Gaea/Orion/Hercules/Derecho` and can be loaded with `source pyDAmonitor/ush/load_pyDAmonitor.sh`.  
Sample data is also staged on these machines for a quick start. If you need the sample data on other platforms, feel free to reach out.

# Details
Data assimilation (DA) is a critical component of modern weather forecasting and earth system modeling, it enables the integration of atmospheric observations into models to increase forecast accuracy. 

pyDAmonitor automatically reads JEDI (or GSI) diagnostic files and create a comprehensive set of statistics, plots, and maps of key assimilation metrics like OmB (Observation minus Background) and OmA (Observation minus Analysis), innovation distribution, etc. It aims to facilitate and speed up analysis of DA performance in both real-time and retrospective scenarios.

# Links:
[pyDAmonitor Book](https://pyDAmonitor.github.io/docs): showcase plots and results

[work with pyDAmonitor](https://github.com/pyDAmonitor/pyDAmonitor/wiki/work-with-pyDAmonitor)  

Check [wiki](https://github.com/pyDAmonitor/pyDAmonitor/wiki) for more information
