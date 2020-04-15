# Data

## Data Sources

### Local Authority Boundaries
- **Link:** http://geoportal.statistics.gov.uk/datasets/local-authority-districts-december-2018-boundaries-gb-bfe
- **API Available**: Yes
- **Used For:** Defining area of interest (so far: Newcastle-upon-Tyne local authority). 

### Output Area Boundaries
- **Link**: http://geoportal1-ons.opendata.arcgis.com/datasets/ff8151d927974f349de240e7c8f6c140_0
- **API Available:** Yes
- **Used For:** Extracting IDs of output areas that are (at least partly) in the local authority. And for visualisations.

### Output Area Population Weighted Centroids
- **Link:** http://geoportal.statistics.gov.uk/datasets/output-areas-december-2011-population-weighted-centroids
- **API Available:** Yes
- **Used For:** Representative location for output area in optimisation (i.e. all residents/workers are treated as being at the centroid). We also currently use the centroids as the set of possible sensor sites.

### Output Area Population Estimates
- **Link:** https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/censusoutputareaestimatesinthenortheastregionofengland
- **API Available:** Yes
- **Used For:** Weight for each output area for residential population coverage (including residents by age, which is provided by the same source).

### Output Area Place of Work
- **Link:** https://www.nomisweb.co.uk/query/construct/summary.asp?reset=yes&mode=construct&dataset=1228&version=0&anal=1&initsel=
- **API Available:** No
- **Used For:** Weight for each output area for place of work coverage.

No API and the interace to get the data is a bit clunky. 

1) **Place of work:** Choose _"Select Area Within"_ (at top), then: Type of area to select: _2011 Output Areas_, Select All Areas Within: _2011 Census Merged Local Authority Districts_, List Local Authority Districts Within: _North East_, Select all the local authorities.
2) **Usual Residence:** Choose _"Select From List"_ (at top), then: Countries: _Some_, Select _England and Wales_.
3) **Format/Layout:** Select _Comma Separated Values (.csv)_.
4) **Download Data:** Wait for extraction process to finish (takes 5 minutes).
5) Download the file when it is ready.

I then just manually renamed the file `raw/workplace.csv`, removed the headers, and left just two columns: `oa11cd` and `workers` (number of workers in the OA, originally labelled "England and Wales"). The result is a count of workers from anywhere in England or Wales will their place of work registered in the OA.

## Data Processing

`spineq/data_fetcher.py` has functions to:

- Download the datasets above from their APIs (where available) and save the files to `data/raw`. These are currently hardcoded to get the area relevant for Newcastle upon Tyne (shouldn't be much work to modify this to get any area).
  
- Process the files:
  - Remove unneccessary columns and sanitise names (e.g. convert to lowercase).
  - Filter out all output areas that aren't in the local authority.
  - Save output to the `data/processed` directory. These have also been added to the repo so it's quick to spin up the docker containers and have the data available (but see future work below).

- Load the files and convert them into the formats needed for optimisation inputs (`spineq/optimise:get_optimisation_inputs`).

Data is processed with `pandas` and `geopandas` with a preference for either shape files or csv files.

**All location data should be obtained in or converted to the British National Grid Coordinate System (https://epsg.io/27700).**


## Possible Future Work

### Additional Datasets

**Pollution Sources**

We need datasets that inform where pollution is likely to be bad (and maybe good too).

The most obvious source is **traffic**. One source is counts from the Department for Transport (https://roadtraffic.dft.gov.uk/downloads), but this is much lower granularity than we'd like. We may be able to extract more from the Urban Observatory. Alternatively, it may be possible to scrape something from Google Maps, or there also seems to be some kind of traffic data available from Azure Maps (https://azure.microsoft.com/en-gb/services/azure-maps/), which we could pay to get access to as part of the Azure subscription (though we may be unlikely to exceed the free allowance in any case). Note that we'd prefer data on traffic _congestion_ rather than traffic _flow_.

Other ideas for air quality-relevant data include:
- Land use datasets (https://catalogue.ceh.ac.uk/documents/6c6c9203-7333-4d96-88ab-78925e7a4e73)
- Scenicness datasets (e.g. http://scenicornot.datasciencelab.co.uk/)
- Use pre-existing air quality sensors, e.g. from Urban Observatory.

**Vulnerable Populations**

We'd like to give increased weighting to places with increased density of vulnerable people. We already have data for residential population by age in each OA. In addition datasets including the following would be benefitial:

- Children: Schools, nurseries...
- Ill: Hospitals, ...
- Elderly: Care homes, ...
- OA health metrics (e.g. asthma, ...)


**Road Network**

The road network could be used to:
- Estimate residential population density at a higher granularity (e.g. divide output area population along roads in OA).
- Estimate the street canyon effect (e.g. have sensor coverage extending along roads rather than as straightline distances).

**Movement of People Data**

Data on where people actually are during the day and in particular where there's a high density of people outside.

### Database

Ideally the backend (optimisation code) and frontend (user interface) would pull data from the same common database, rather than the backend using a local copy of the files as is the case currently.