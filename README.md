# spatial-inequality

Repository for the [Spatial Inequality in the Smart City](https://www.turing.ac.uk/research/research-projects/spatial-inequality-and-smart-city) project.

## API

### Start the API

```bash
docker build .
docker-compose up
```

Should then be available on `0.0.0.0:5000`

### WebSockets

* Submit an optimisation job:
  - Client emits event `submitJob` with data `{"n_sensors": 10, "theta": 500}`
  - Server emits event `job` with job data.
  
* Retrieve the result/status of a job:
  - Client emits event `getJob` with data `<the_job_id>`
  - Server emits event `job` with job data.

* Get a list of available job IDs:
  - Client emits event `getQueue`
  - Server emits event `queue` with queue data.
  
* Remove a job from the queue:
  - Client emits event `deleteJob` with data `<the_job_id>`
  - Server emits event `message` with deletion result.
  
* Remove all jobs from the queue (including completed jobs!):
  - Client emits event `deleteQueue`
  - Server emits event `message` with deletion result.

## Notebooks

Depdencies for this project are managed with [conda](https://docs.conda.io/en/latest/) and listed in the `environment.yml` file. To create a virtual environment  with all dependencies installed clone this repo and from the parent `spatial-inequality` directory run:
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
