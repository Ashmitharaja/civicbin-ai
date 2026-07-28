-- Run once to set up the analytics table.
-- e.g. bq query --use_legacy_sql=false < data/bigquery_schema.sql

CREATE SCHEMA IF NOT EXISTS `civicbin`;

CREATE TABLE IF NOT EXISTS `civicbin.overflow_reports` (
  id STRING,
  lat FLOAT64,
  lng FLOAT64,
  status STRING,
  confidence FLOAT64,
  logged_at TIMESTAMP
);
