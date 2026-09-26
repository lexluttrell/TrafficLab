# Additional weekday intake — September 26, 2026

Received September 17, 22 and 23 District 4 Station 5-Minute archives. Each gzip was read through its trailer successfully; its first record timestamp matches the requested date. Source SHA-256 hashes and preassigned roles are recorded in `scenarios/data-split.json`.

September 22 is the new development day. Imported 8,064 observations across 28 corridor stations, with no missing station/time intervals and no identical duplicates removed. All required flow inputs for 07:30–08:30 are available; 24 of the 144 required input rows are partly observed, and those quality flags remain intact. Mapping uses the existing assumed-merge network and April 8 metadata; it remains provisional. No new simulation or calibration was performed during intake.

September 17 and 23 remain reserved for validation. Only archive integrity, hashes and the first timestamp were inspected; their traffic patterns have not been examined or used to select a model. September 24 remains exploratory development, and September 13 remains the reserved Sunday archive. Freeze the model and evaluation protocol before opening validation traffic patterns.

Original uploads remain unchanged. This intake publishes hashes and quality summaries, not the new raw archives or normalized traffic records. Additional downloads are not needed for this stage.

Reproduce the development import from supplied local files:

```sh
python -m trafficlab.data.pems --metadata /path/to/d04_text_meta_2026_04_08.txt --observations /path/to/d04_text_station_5min_2026_09_22.txt.gz --date 2026-09-22 --metadata-date 2026-04-08 --scenario scenarios/pinole-merge/scenario.json --output runs/weekday-intake/2026-09-22.json
python -m trafficlab.data.review --input runs/weekday-intake/2026-09-22.json --network scenarios/pinole-merge/network.net.xml --output runs/weekday-intake/2026-09-22-reviewed.json
```
