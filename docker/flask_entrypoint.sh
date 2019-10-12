#!/bin/bash

echo "Starting nest_flask..."
echo "Project: ${PROJECT_ENV:-knoweng}"
echo "Run Level: ${NEST_RUNLEVEL:-development}"

# Unset UWSGI environment variables set by base image; we want to rely entirely on our own config
unset -v UWSGI_INI
unset -v UWSGI_CHEAPER
unset -v UWSGI_PROCESSES

# Copy appropriate index.html to the foreground
cp client/index.${PROJECT_ENV}.html client/index.html
if [ -z "$GOOGLE_ANALYTICS_ID" ]
  then
    echo "Warning: GOOGLE_ANALYTICS_ID not set."
  else
    sed -i "s/UA-XXXXX-Y/${GOOGLE_ANALYTICS_ID}/" client/index.html
fi

/usr/bin/supervisord -c /etc/supervisor/supervisord.conf
