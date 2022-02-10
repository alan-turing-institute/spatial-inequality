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

### SocketIO

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

### Dependencies

The dockerised version uses only `pip` and the packages in `requirements.txt`.
This doesn't include any plotting libraries.

A [conda](https://docs.conda.io/en/latest/) environment file `environment.yml`
is provided which installs all the pip requirements as well as additional
libraries for plotting, notebooks etc.
To create a virtual environment  with all dependencies installed clone this repo and from the parent `spatial-inequality` directory run:
```bash
> conda env create
```
Then, to use the environment run:
```bash
> conda activate spatial-inequality
```
To stop using the environment and return to default system python run:
```bash
> conda deactivate
```
