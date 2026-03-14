-- Migration: Add cost and energy fields to relay_settings
-- Safe to run once on SQLite databases that do not yet have these columns.

ALTER TABLE relay_settings ADD COLUMN WATER_COST_PER_M3 REAL NOT NULL DEFAULT 1.5;
ALTER TABLE relay_settings ADD COLUMN RELAY_POWER_WATTS REAL NOT NULL DEFAULT 750;
ALTER TABLE relay_settings ADD COLUMN ENERGY_COST_PER_KWH REAL NOT NULL DEFAULT 0.17;
