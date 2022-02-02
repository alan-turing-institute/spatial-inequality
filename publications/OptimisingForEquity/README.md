# Optimising for equity: Sensor coverage, networks and the responsive city

Figures and scripts for our pre-print: [10.21203/rs.3.rs-902765/v1](https://doi.org/10.21203/rs.3.rs-902765/v1)

## Pre-Generated Figures and Data

Pre-generated networks and figures can be found in the `publications/OptimisingForEquity/results` directory in our upload on Zenodo:
https://doi.org/10.5281/zenodo.5950713


## Instructions

To generate the figures:

1. Checkout/download the correct version of the code by doing one of the following:
   - Download the source code from Zenodo: https://doi.org/10.5281/zenodo.5552877
   - Download from GitHub: https://github.com/alan-turing-institute/spatial-inequality/releases/tag/v2.1
   - From a local clone of the repo, checkout tag `v2.1` or commit `8e1cd93`.

2. Follow the setup instructions to create and activate the conda environment in [the repo readme file](../../README.md])

3. Change to the directory this file is in (`cd publications/OptimisingForEquity`).

4. The file `config.yml` defines the properties of the networks and figures that will be generated. You can leave them as the defaults used for the paper or edit the file to try running with different values.

5. Run `python main.py`. This may take a long time (hours) to finish, depending on the values specified in `config.yml`.

6. By default, results will be saved to the `results` directory in a sub-directory with the local authority code (`E08000021` for Newcastle upon Tyne). This should include the reports with figures in Markdown (`report.md`) and HTML (`report.html`) formats, source figures in the `figures` directory, and saved pre-generated networks in the `networks` directory (in Python pickle files).
