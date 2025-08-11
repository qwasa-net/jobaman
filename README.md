# jobaman


A simple service for managing background jobs via an HTTP API.
Not intended for production use. Not secure. Just for fun.


## Requirements

+ python
+ linux

## Install and run

```bash
make tea run
```

or

```bash
make docker-build docker-run
```


## Configuration

see `jobaman.ini`

## API Examples
```
# list running jobs
curl "http://localhost:1954/jobs/"
# start a new job
curl "http://localhost:1954/jobs/run?_0=echo&_1=Hello,_World!"
# stop a job
curl "http://localhost:1954/jobs/kill?__job_id=<job_id>"
# get job output
curl "http://localhost:1954/jobs/output?__job_id=<job_id>"
# Ping
curl http://localhost:1954/ping
```