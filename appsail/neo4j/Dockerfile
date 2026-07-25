FROM neo4j:5.26.0-community

# Bolt is the only published service. Browser/HTTP is loopback-only in neo4j.conf.
ENV NEO4J_ACCEPT_LICENSE_AGREEMENT=yes \
    NEO4J_server_memory_heap_initial__size=256m \
    NEO4J_server_memory_heap_max__size=512m \
    NEO4J_server_memory_pagecache_size=256m \
    NEO4J_server_bolt_listen__address=0.0.0.0:7687 \
    NEO4J_server_http_listen__address=127.0.0.1:7474

COPY neo4j.conf /var/lib/neo4j/conf/neo4j.conf
COPY import/schema.cypher /var/lib/neo4j/import/schema.cypher
COPY scripts/ /opt/neo4j-scripts/

RUN chmod 0550 /opt/neo4j-scripts/*.sh

EXPOSE 7687
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
  CMD ["/opt/neo4j-scripts/healthcheck.sh"]
