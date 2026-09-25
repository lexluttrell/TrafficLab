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
The inputs are mapped road geometry, inferred/default network attributes, assumed synthetic demand (1,800 vehicles/hour/direction for 10 minutes), and SUMO Krauss driver defaults explicitly set in the demand file. Ramps are shown but receive no external demand. Traffic is through-only. Lane restrictions, geometry, connection shapes and speed limits have not been field-audited. HOV behavior is not calibrated. There is no PeMS data, historical replay, fitted driver population, empirical validation or counterfactual experiment yet.

The initial OSM conversion emits warnings about removed public-transport stops, incomplete out-of-scope restrictions, and some junction geometry. Passing routes and zero teleports do not establish geometric or behavioral accuracy. Review these before calibration.

## Sources and licensing
Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Source and derived network are distributed with provenance; attribution applies to display context too. SUMO is an external dependency with its own license; see [SUMO](https://sumo.dlr.de/docs/). Relevant documentation: [OSM import](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html), [FCD output](https://sumo.dlr.de/docs/Simulation/Output/FCDOutput.html).

## Repository and access

Source: https://github.com/lexluttrell/TrafficLab. Public visibility supports sharing; it does not grant visitors write access. Only the owner and authorized collaborators/integrations can push changes. The connected assistant acts through the owner's authorized GitHub connection, not a separate GitHub identity.

The initial local work had three commits, ending at `3e279f2`. The connector migration creates its own commit IDs; the original history is retained in the Mission 001 downloadable bundle. Current project work continues in this repository.

The frozen OSM extract and hosted replay are stored with lossless gzip compression. The CLI accepts the compressed extract directly; the hosted browser viewer decompresses the replay. No geometry or simulation states are discarded.

## Mission 002 — historical observations (in progress)

[Open the observations viewer](https://lexluttrell.github.io/TrafficLab/observations.html). It accepts a local normalized JSON file without uploading it. No historical data is bundled yet. Caltrans PeMS access or authorized downloaded source files are required to complete this mission.

See [Mission 002 plan and import command](docs/MISSION-002-PLAN.md). Run parser checks with `python -m unittest discover -s tests -p test_pems.py -v`. Tests use explicitly fabricated rows, never a substitute for empirical validation. Missing intervals remain gaps, zero counts remain zero, and percent-observed flags remain visible. Source speed estimates are not presented as individually measured vehicle speeds.
