FROM python:3.12-slim

ARG CONFIGS_BASE=.

WORKDIR /app

COPY jobaman /app/jobaman
COPY ${CONFIGS_BASE}/jobaman.ini /app/jobaman.ini
COPY ${CONFIGS_BASE}/job.sh /app/job.sh

ENV PYTHONUNBUFFERED=1 \
    JOBAMAN_LOG_LEVEL=INFO \
    JOBAMAN_INI_PATH=/app/jobaman.ini \
    JOBAMAN_INI_SECTION=default \
    JOBAMAN_SERVER_LISTEN_HOST=0.0.0.0 \
    JOBAMAN_SERVER_LISTEN_PORT=1954 \
    JOBAMAN_SERVER_BASE_URL=http://localhost:11954 \
    JOBAMAN_ENTRYPOINT=/app/job.sh

CMD [ \
    "python", \
    "-m", \
    "jobaman.main", \
    "--ini-path", \
    "/app/jobaman.ini" \
]