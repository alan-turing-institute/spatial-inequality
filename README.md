# spatial-inequality

Repository for the [Spatial Inequality in the Smart City](https://www.turing.ac.uk/research/research-projects/spatial-inequality-and-smart-city) project.

## Papers and Publications

If you're looking for the scripts used to generate the figures in the paper "Optimising for equity: Sensor coverage, networks and the responsive city", please go to the [OptimisingForEquity](publications/OptimisingForEquity) directory.

## Pre-requisites

1. [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
2. [Conda](https://docs.conda.io/en/latest/miniconda.html)

## Setup

1. Clone the repo:
   ```shell
   git clone https://github.com/alan-turing-institute/spatial-inequality.git
   ```

2. Change to the `spatial-inequality` directory:
   ```shell
   cd spatial-inequality
   ```

3. Create the conda environment:
   ```
   conda env create
   ```  

4. Activate the environment:
   ```
   conda activate spatial-inequality
   ```
 
## API

### Start the API

```bash
docker-compose up
```

Should then be available on `0.0.0.0:5000`

Command to force a rebuild if something hasn't udpated correctly:
```bash
docker-compose up --build --force-recreate
```

### Submitting Optimisation Jobs with SocketIO

Generate a pseudo-optimised network of sensors with a greedy algorithm. See `scripts/client.py` for an example.

* Submit an optimisation job:
  - Client emits event `submitJob` with data `{"n_sensors": 10, "theta": 500}`
  - Server emits event `job` with job data.
  - On job completion, server emits `jobFinished` with job_id and result.
  - Optionally can give the following parameters with `submitJob`:
    - `min_age`: Minimum age to include for population coverage (default: 0)
    - `max_age`: Maximum age to include for population coverage (default: 90)
    - `population_weight`: Weight for population coverage (default: 1)
    - `workplace_weight`: Weight for place of work coverage (default: 0)
  
* Retrieve the result/status of a job:
  - Client emits event `getJob` with data `<the_job_id>`
  - Server emits event `job` with job data.

* Get a list of available job IDs:
  - Client emits event `getQueue`
  - Server emits event `queue` with queue data.
  
* Remove a job from the queue:
  - Client emits event `deleteJob` with data `<the_job_id>`
  - Server emits event `message` with deletion result.
  
* Remove all jobs from the queue:
  - Client emits event `deleteQueue`
  - Server emits event `message` with deletion result.

### Coverage Endpoint

The `/coverage` endpoint computes coverage for a user-defined network (set of sensors placed at output area centroids), and takes a JSON with the following format:
```json
{
   "sensors": ["E00042671","E00042803"],
   "theta": 500,
   "lad20cd": "E08000021"
}
```
where `theta` and `lad20cd` are optional and take the values above by default, but sensors must be defined and takes a list of `oa11cd` codes that have sensors in them.

It should return a JSON with this structure:
```json
{
   "oa_coverage":[
      {"coverage":0.6431659719289781,"oa11cd":"E00042665"}, 
      ...,
    ],
   "total_coverage": {
      "pop_children":0.0396946631327479,
      "pop_elderly":0.024591629984248815,
      "pop_total":0.059299090984356984,
      "workplace":0.0947448314996531
   }
}
```

### Dependencies

The dockerised version of the code used for the API uses only `pip` and the packages in `requirements.txt`. This doesn't include some plotting and optimisation libraries included in the `conda` environment.
