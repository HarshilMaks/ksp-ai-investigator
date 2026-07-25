#!/bin/sh
set -eu

: "${NEO4J_AUTH:?NEO4J_AUTH must be set as neo4j/<password>}"
user=${NEO4J_AUTH%%/*}
password=${NEO4J_AUTH#*/}
[ -f /var/lib/neo4j/import/schema.cypher ]

cypher-shell --address bolt://127.0.0.1:7687 \
  --username "$user" \
  --password "$password" \
  --file /var/lib/neo4j/import/schema.cypher
