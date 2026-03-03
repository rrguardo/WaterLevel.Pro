# Sensor stats: ingestion, storage, aggregation, and charting

This document explains how sensor telemetry (fill percent and battery voltage) is collected, stored, aggregated into 24 hourly buckets, and rendered on the device info page charts.

**Relevant files**
- `api.py` - device-facing ingestion endpoint(s) that persist runtime samples.
- `app.py` - web app route `/sensor_stats` that builds 24 hourly buckets for the frontend.
- `templates/sensor_device_info.html` - client-side chart code (ApexCharts) which renders the hourly charts and uses `mapVoltageToPercentage`.

Overview
- Devices push periodic updates (distance, voltage, rssi, timestamps) to the device API.
- Each update is converted to two key numeric values: `percent` (tank fill %) and `voltage` (battery voltage in volts).
- Updates are stored in Redis sorted-sets keyed per device (history key pattern `tin-history/{public_key}`) with the Redis score equal to epoch seconds and the member encoding the sample values (format: `"percent|voltage"`).

Ingestion (what happens on update)
- The device API normalizes incoming numeric fields (voltage normalization, distance → percent using `EMPTY_LEVEL`/`TOP_MARGIN`). See `api.py` for exact calculation points.
- Stored item: member string containing percent and voltage; score is the current epoch time (seconds).
- The ingestion process also trims old history and sets TTLs to keep storage bounded (retention configured in the app).

Storage format
- Redis sorted-set per device: `tin-history/{public_key}`
- Score: integer epoch seconds of the sample
- Member: string containing sample data: `percent|voltage` (example: `72|3.79`)

Aggregation into hourly buckets (server-side, `/sensor_stats`)
- The web route builds 24 buckets for the last 24 hours. Each bucket has an `hour_start` (epoch seconds representing the start of the hour window) and covers a one-hour interval.
- For each bucket the server queries Redis using a score range (zrangebyscore) for samples whose score falls between the bucket start and bucket end (bucket_start .. bucket_start+3600).
- If a bucket contains samples the server computes the average `percent` and average `voltage` across those samples and returns them as that bucket's values.
- If a bucket contains no samples it is marked `offline` (or returned with nulls) so the frontend can render gaps appropriately.
- The server now returns integer percent values for `percent` (the aggregation does `int(round(avg_percent))`) to avoid frontend decimal display mismatches.

Frontend rendering and chart behavior
- The device page (`templates/sensor_device_info.html`) requests `/sensor_stats` and receives an array of 24 `buckets` with fields like `hour_start`, `percent`, `voltage`, `offline`.
- Hour labeling: the template displays hourly labels using the bucket end time (i.e. `new Date((hour_start + 3600) * 1000)`) so the human-readable hour matches the end of that hour window and avoids a perceived -1 hour offset.
- Fill percent chart: the percent series uses the server-provided `percent` (rounded on the server) and the template further ensures integers with `Math.round(b.percent)` before pushing series values.
- Battery chart: the hourly voltage average is converted to a battery charge percentage using the client-side helper `mapVoltageToPercentage(voltage)`. This function maps voltage ranges to coarse percentage buckets (0,10,20,...,100). The computed charge % is also rounded on the client for display.
- Tooltips and display: both charts format percent and battery charge as integers (no decimals) to keep the UI consistent.

Why the hourly label uses bucket end time
- When aggregating samples into hour-long windows, showing the end-of-window hour (hour_start + 3600) makes the label represent the hour that just finished rather than the starting hour. This matches human expectation for "last 24 hours" charts and avoids an off-by-one-hour perception.

How the final value for an hour is determined (summary)
1. Collect all samples whose epoch score falls within the bucket's [hour_start, hour_start+3600] interval.
2. Compute arithmetic mean (average) of `percent` values and arithmetic mean of `voltage` values from the samples.
3. If the bucket has no samples mark it offline/null in the response.
4. The server rounds percent to an integer before returning. The client rounds again for safety and displays integer-only percentages.

Testing and verification
- Quick verification steps:
  - Run the unit/integration tests that target `/sensor_stats` (the repo contains tests under `tests/`). If `pytest` is not available, run a targeted unittest, for example:

    python -m unittest tests.unit.test_app_unit.AppUnitTestCase.test_sensor_stats_endpoint_unit

  - Alternatively, run the application locally (docker compose as documented) and query `/sensor_stats?public_key=<key>` to validate JSON output.

Files to review
- `app.py` — build of the 24 buckets and percent rounding
- `api.py` — ingestion and storage logic
- `templates/sensor_device_info.html` — hourly chart rendering, `mapVoltageToPercentage`, tooltip formatting, and label calculation

Notes and recommendations
- Keep rounding consistent: prefer integer percent at server-side aggregation and also enforce integer display on the client.
- If you need edge-precise aggregation rules (inclusive/exclusive endpoints), document or adjust the zrangebyscore intervals explicitly to avoid overlapping samples at bucket boundaries.
- If stricter battery percentage mapping is required, consider moving `mapVoltageToPercentage` server-side so both the API and charting consume the same canonical mapping.

If you want, I can add a small unit test that asserts returned `percent` values are integers and that buckets with no samples are marked offline.
