# WLP Database Migrations

## What is this?
SQL scripts to update the SQLite database schema used by WaterLevel.Pro.

## When to use
- When you update the application code and a migration is documented here.
- Before starting the app after pulling changes that alter the database schema.

## How to use
1. Back up your database: `cp database.db database.db.bak`
2. Run the migration script:

   ```sh
   sqlite3 database.db < scripts/migrate_add_liters_per_cm_to_sensor_settings.sql
   ```

3. Verify the new column exists:

   ```sh
   sqlite3 database.db ".schema sensor_settings"
   ```

## Version applicability
- This migration should be applied only to instances running versions <= 1.0.3.
- Do NOT apply this migration to databases already upgraded by versions > 1.0.3.

## Included migrations
- `migrate_add_liters_per_cm_to_sensor_settings.sql`: adds `liters_per_cm` (REAL, default 10.0) to the `sensor_settings` table. If a legacy `litros_por_cm` column is present, its data will be migrated to `liters_per_cm`.
