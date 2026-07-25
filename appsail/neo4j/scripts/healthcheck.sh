#!/bin/sh
set -eu

: "${NEO4J_AUTH:?NEO4J_AUTH must be set as neo4j/<password>}"
user=${NEO4J_AUTH%%/*}
password=${NEO4J_AUTH#*/}
[ -n "$user" ] && [ -n "$password" ]

cypher-shell --address bolt://127.0.0.1:7687 \
  --username "$user" \
  --password "$password" \
  --format plain \
  'RETURN 1 AS health' >/dev/null
