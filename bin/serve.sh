#!/usr/bin/env sh
set -e

dockerize -wait tcp://postgres:5432 -timeout 1m
dockerize -wait tcp://solr:8983 -timeout 1m
dockerize -wait tcp://redis:6379 -timeout 1m

for i in `seq 1 60`; do
    if (PGPASSWORD=pass psql -h postgres -U ckan_default -d ckan_test -c "\q"); then
        echo "Database became ready on attempt $i"
        break
    else
        echo "Database not yet ready, retrying (attempt $i)..."
        sleep 1
    fi
done

. ${APP_DIR}/bin/activate
if (which ckan > /dev/null); then
    ckan -c ${CKAN_INI} run -r
else
    paster serve ${CKAN_INI}
fi
