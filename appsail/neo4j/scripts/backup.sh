#!/bin/sh
set -eu

# This script is an operator boundary, not an HTTP route. The caller must provide
# an explicit local destination; no cloud credentials or network destinations are accepted.
output_dir=${1:-}
if [ -z "$output_dir" ] || [ "${output_dir#/}" = "$output_dir" ]; then
  echo 'usage: backup.sh /var/lib/neo4j/backups' >&2
  exit 2
fi
mkdir -p -- "$output_dir"
neo4j-admin database dump neo4j --to-path="$output_dir"
