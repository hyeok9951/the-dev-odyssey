#!/bin/bash
curl -X POST http://localhost:8083/connectors -H "Content-Type: application/json" -d '{
  "name": "debezium-postgres-source",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres-source",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "dbz",
    "database.dbname": "sourcedb",
    "database.server.name": "pgsrc",
    "publication.autocreate.mode": "filtered",
    "table.include.list": "public.mytable",
    "plugin.name": "pgoutput"
  }
}'
