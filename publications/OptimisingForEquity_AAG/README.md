# Optimising for equity: Sensor coverage, networks and the responsive city (DRAFT)

To be submitted to Annals of the American Association of Geographers.

## Pre-Generated Figures and Data

TODO - can be found at...

## Instructions

To generate the figures:

1. TODO - checkout/download the relevant commit/tag

2. Follow the setup instructions to create and activate the conda environment in [the repo readme file](../../README.md])

3. Change to the directory this file is in (`cd publications/OptimisingForEquity_AAG`).

4. The file `config.yml` defines the properties of the networks and figures that will be generated. You can leave them as
   the defaults used for the paper or edit the file to try running with different values.

5. Run `python main.py`. This may take a long time (hours) to finish, depending on the values specified in `config.yml`.

6. By default, results will be saved to the `results` directory in a sub-directory with the local authority code (`E08000021` for Newcastle upon Tyne). This should include the reports with figures in Markdown (`report.md`) and HTML (`report.html`) formats, source figures in the `figures` directory, and saved pre-generated networks in the `networks` directory (in Python pickle files).

