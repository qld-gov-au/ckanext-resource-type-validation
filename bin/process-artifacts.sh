#!/usr/bin/env bash
##
# Process test artifacts.
#
set -ex

# Create screenshots directory in case it was not created before. This is to
# avoid this script to fail when copying artifacts.
ahoy cli "mkdir -p test/screenshots test/junit"
# Copy from the app container to the build host for storage.
mkdir -p /tmp/artifacts/behave /tmp/artifacts/junit
docker cp "$(sh bin/docker-compose.sh ps -q ckan)":/srv/app/test/screenshots /tmp/artifacts/behave/
docker cp "$(sh bin/docker-compose.sh ps -q ckan)":/srv/app/test/junit /tmp/artifacts/

echo "make html junit/coverage reports next"
ahoy cli "junit2html test/junit/results.xml test/junit/pytest-results.html"
ahoy cli "coverage html -d test/junit/coverage_html"

ahoy cli "coverage xml -o test/junit/coverage.xml"

docker cp "$(sh bin/docker-compose.sh ps -q ckan)":/srv/app/test/junit /tmp/artifacts/
