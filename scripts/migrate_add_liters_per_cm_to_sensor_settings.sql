-- Migration: Add liters_per_cm to sensor_settings
-- Adds a new column to store how many liters per cm for each tank (default 10.0)
-- Safe to run multiple times (IF NOT EXISTS pattern)

ALTER TABLE sensor_settings ADD COLUMN liters_per_cm REAL NOT NULL DEFAULT 10.0;
