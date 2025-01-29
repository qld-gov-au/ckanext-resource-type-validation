#!/usr/bin/env bash
##
# Run tests in CI.
#
set -ex

ahoy lint

ahoy test-unit

ahoy install-site
ahoy test-bdd
