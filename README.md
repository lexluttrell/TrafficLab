# TrafficLab · Mission 001 — Make Pinole Move

Real I-80 geometry around Pinole, actual SUMO microscopic vehicle dynamics, and an interactive vehicle inspector. **Synthetic demand, uncalibrated. No claims about real-world traffic performance.**

## Shareable browser demo

GitHub Pages target: https://lexluttrell.github.io/TrafficLab/

Publish from branch `main`, folder `/docs` in repository Settings → Pages. After regenerating a run, use `python scripts/export-pages.py`, commit the docs changes and push. Pages serves the same real SUMO replay; it does not execute Python or SUMO on GitHub’s web server.

## Open the delivered demo immediately
In the release ZIP, open `Open-TrafficLab.html` in Chrome, Edge or Firefox. No installation, network access or server is needed for this bundled replay. Click **Pick a car**, check **Follow selected vehicle**, and zoom in. You can also click vehicles directly, drag the map, pause, change playback speed, or scrub the timeline.

The replay contains an actual SUMO run: 600 cars on two approximately 3.6–3.8 km mainline routes. It is not a live simulation engine inside the browser. States are sampled at 1 second; displayed positions are interpolated. Inspector values refer to the preceding sample. Streets drawn faintly are display context and do not carry simulated traffic.

## Regenerate the simulation
Python 3.11+ with a compatible SUMO wheel is required. Linux x86-64/Python 3.12 was tested; Windows commands are provided but Windows was not tested here.

Windows PowerShell (from this project directory):

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m trafficlab demo
```

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m trafficlab demo
```

Open **http://localhost:8765** after the run finishes. Stop the server with Ctrl+C. `runs/pinole/Open-TrafficLab.html` is also generated for standalone viewing. In all later examples, use the Python executable from your virtual environment.

```sh
python -m trafficlab run --seed 42      # regenerate; no server
python -m trafficlab serve             # serve existing output
python -m trafficlab build             # reconvert the bundled OSM extract
python -m unittest discover -s tests -v # two genuine SUMO runs; reproducibility/drain checks
```

A frozen raw map extract and converted network are included, so no map download is needed to run or rebuild. If the source file is missing, `build` fetches its configured URL. Initial dependency installation needs internet access. If port 8765 is occupied, add `--port 8766`.

## Layout and reproducibility

- `scenarios/pinole/`: frozen raw OSM, converted SUMO network, configuration and source hashes.
- `trafficlab/network.py`: geometry source adapter and netconvert invocation.
- `trafficlab/demand.py`: connected mainline routes and deterministic synthetic flows.
- `trafficlab/simulation.py`: SUMO execution, recorded states, manifests and replay export.
- `trafficlab/context.py`: display-only surrounding roads.
- `viewer/`: framework-free Canvas viewer.
- `tests/`: real engine integration test.
- `docs/PROJECT.md`: plan, decisions, scientific limits, verification, next milestone.
- `runs/` (generated): demand, raw FCD/trip/summary output, log, manifest and viewer.

Scenario-specific geography is data, not hardcoded in the engine. Context-road labels also live in scenario configuration. Route discovery currently assumes two disjoint motorway through-paths: it is a Mission 001 demand adapter, not a universal demand model.

Pin SUMO 1.27.1 and seed 42 to reproduce this run. The manifest records network/demand hashes, SUMO version, run command and trip accounting. Exact trajectory equality was verified on the same platform, not across operating systems or future SUMO versions.

## Scientific limits
The inputs are mapped road geometry, inferred/default network attributes, assumed synthetic demand (1,800 vehicles/hour/direction for 10 minutes), and SUMO Krauss driver defaults explicitly set in the demand file. Ramps are shown but receive no external demand. Traffic is through-only. Lane restrictions, geometry, connection shapes and speed limits have not been field-audited. HOV behavior is not calibrated. These limits describe Mission 001. Subsequent observation, historical-count and ramp experiments are linked below; none is calibrated or validated for counterfactual conclusions.

The initial OSM conversion emits warnings about removed public-transport stops, incomplete out-of-scope restrictions, and some junction geometry. Passing routes and zero teleports do not establish geometric or behavioral accuracy. Review these before calibration.

## Sources and licensing
Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Source and derived network are distributed with provenance; attribution applies to display context too. SUMO is an external dependency with its own license; see [SUMO](https://sumo.dlr.de/docs/). Relevant documentation: [OSM import](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html), [FCD output](https://sumo.dlr.de/docs/Simulation/Output/FCDOutput.html).

## Repository and access

Source: https://github.com/lexluttrell/TrafficLab. Public visibility supports sharing; it does not grant visitors write access. Only the owner and authorized collaborators/integrations can push changes. The connected assistant acts through the owner's authorized GitHub connection, not a separate GitHub identity.

The initial local work had three commits, ending at `3e279f2`. The connector migration creates its own commit IDs; the original history is retained in the Mission 001 downloadable bundle. Current project work continues in this repository.

The frozen OSM extract and hosted replay are stored with lossless gzip compression. The CLI accepts the compressed extract directly; the hosted browser viewer decompresses the replay. No geometry or simulation states are discarded.

## Mission 002 — historical observations (in progress)

[Open the observations viewer](https://lexluttrell.github.io/TrafficLab/observations.html). It accepts a local normalized JSON file without uploading it. The hosted page loads the September 24 aggregate subset supplied by the user. Caltrans PeMS access or authorized downloaded files are required for additional days.

See [Mission 002 plan and import command](docs/MISSION-002-PLAN.md). Run parser checks with `python -m unittest discover -s tests -p test_pems.py -v`. Tests use explicitly fabricated rows, never a substitute for empirical validation. Missing intervals remain gaps, zero counts remain zero, and percent-observed flags remain visible. Source speed estimates are not presented as individually measured vehicle speeds.

## Mission 003: historical-count baseline

The separate [historical-count replay](https://lexluttrell.github.io/TrafficLab/historical.html) feeds reported Sept 24 entry counts into SUMO and compares downstream detector output. It is explicitly **through-only and uncalibrated**; ramp effects and parameter fitting are future work. The ten-minute visible replay is sampled from a one-hour run, with 15 minutes excluded as warm-up from diagnostics.

After installing `requirements.txt`, reproduce with:

```sh
python -m trafficlab.historical --observations docs/observations-2026-09-24.json.gz --output runs/historical
python scripts/export-historical.py --source runs/historical --destination runs/historical-viewer
python -m http.server 8765 --directory runs/historical-viewer
```

Open `http://localhost:8765/historical.html`. For a complete local multi-page site, export to `docs` and serve `docs` instead. Region/time/entry-station choices live in `scenarios/pinole/historical.json`. Full plan and caveats: `docs/MISSION-003-PLAN.md`. Run scientific-accounting checks with `python -m unittest discover -s tests -p test_comparison.py`.

## Mission 004: ramps and boundaries

[Open the ramp experiment](https://lexluttrell.github.io/TrafficLab/ramps.html): five measured on-ramps, four exits (three explicitly inferred), a same-network control, low/high exit sensitivity and per-origin insertion accounting. Two eastbound ramp queues prevent delivery of all demand, so improved detector errors are not validation. [Run notes, limits and reproduction](docs/MISSION-004.md). More weekdays can follow; first resolve merge geometry and downstream boundary behavior.

## Mission 005: navigation, flow layers and working merges

[Explore the current corridor](https://lexluttrell.github.io/TrafficLab/ramps.html). Zoom at a location, jump to a ramp or detector, color roads by local mean speed, and color cars relative to nearby traffic. Two explicitly assumed acceleration lanes allow all 14,407 cars to enter and complete their trips. The original blocked-ramp replay remains linked. Geometry is not field-verified and the model is uncalibrated. [Definitions, results and reproduction](docs/MISSION-005.md).
