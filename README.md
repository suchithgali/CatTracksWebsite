# CatTracks

CatTracks is a Flask web application for multimodal transit route planning in
Merced County. It combines GTFS transit schedules with walking connections,
schedule-aware pathfinding, geocoding, road-route geometry, and a React/Leaflet
planner interface.

## Current architecture

- **Web application:** Flask, served through `api/index.py`
- **Routing graph:** NetworkX graph built from the canonical GTFS feed
- **Routing modes:** walking, bus, and same-stop transfers
- **Schedule routing:** optional departure-time searches select the next valid
  GTFS bus departure and include waiting time
- **Address routing:** Merced-area custom addresses are geocoded and connected
  to the nearest transit stops
- **Road geometry:** OSRM-compatible routing with a direct-line fallback
- **Frontend:** server-rendered Flask templates with a React/Leaflet planner
- **Deployment:** Vercel configuration in `vercel.json`

The repository also contains the original C++ graph and GIS artifacts under
`include/`, `CMAKELists.txt`, and `geopkg/`. They are retained as historical
or data-processing assets; the current website runtime is the Python service.

## Local setup

### Requirements

- Python 3.12 or newer
- Network access for geocoding and, when enabled, OSRM road geometry

Create an environment and install the project dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Start the local Flask application:

```bash
./build_and_run.sh
```

Open <http://127.0.0.1:5000>. The health endpoint is available at
<http://127.0.0.1:5000/health>.

Run the route smoke test:

```bash
.venv/bin/python scripts/smoke_test_route.py \
  --from-stop "University Transit Center" \
  --to-stop "Merced Mall Target"
```

Run the automated tests:

```bash
.venv/bin/python -m pytest -q tests
.venv/bin/python -m compileall -q website
```

## GTFS data

The application reads the canonical feed from `data/gtfs/`. The source feed
is preserved in `data/gtfs_official/`. To regenerate the canonical feed after
the source data changes:

```bash
.venv/bin/python -m src.gtfs_normalize
```

Set `CATTRACKS_GTFS_DIR` to use a different feed directory. The current
schedule-aware implementation reads trip times and service-calendar data from
the feed, but route searches currently select from the loaded trips without
performing a date-specific service-day filter. Results should therefore be
treated as schedule-aware estimates rather than calendar-perfect departures.

## Route behavior

The JSON API accepts stop names or supported custom addresses:

```http
POST /api/route
Content-Type: application/json
```

```json
{
  "from": "University Transit Center",
  "to": "Merced Mall Target",
  "departure_time": "08:00"
}
```

When `departure_time` is provided, valid bus edges use the next departure at
or after the current time. Walking and transfer legs advance immediately.
Malformed bus legs whose arrival precedes departure are ignored. If no valid
scheduled transit path is available, the service reports the routing error
instead of silently labeling a different edge.

Without a departure time, the service uses its static generalized route cost.
Travel time remains primary; walking distance, transit distance, and transfers
receive additional penalties to avoid choosing implausible routes solely
because of a short or malformed feed edge.

The planner requests road geometry for consecutive route waypoints. If the
external routing service fails, the API retains the route and returns fallback
geometry between transit points.

## Network maintenance mode

The schedule-aware network can be disabled without taking the website offline.
Set this Vercel environment variable to `false` and redeploy:

```text
CATTRACKS_NETWORK_ONLINE=false
```

In this mode, the site remains available, displays a
**CatTracks network offline** warning, and uses the legacy static routing
behavior without departure-time schedule calculations. Restore the variable to
`true` or remove it, then redeploy to re-enable schedule-aware routing.

The flag is evaluated at request time, but a Vercel deployment must be
recreated after changing the dashboard environment variable so the deployment
receives the updated value.

Legacy routing also rejects stop-to-stop walking legs longer than 30 minutes.
This prevents stale static data from producing implausible long walking
detours when the schedule-aware network is offline. If no route satisfies that
limit, the API reports that no reasonable route is available instead of
presenting the long walk as a recommendation.

## Configuration

Copy `.env.example` to `.env` for local configuration. Supported deployment
variables include:

- `CATTRACKS_NETWORK_ONLINE` — enables schedule-aware routing unless set to
  `0`, `false`, `no`, or `off`
- `CATTRACKS_GTFS_DIR` — alternate canonical GTFS directory
- `CATTRACKS_ROUTING_URL` — hosted OSRM-compatible routing endpoint
- `DATABASE_URL` — optional SQLAlchemy database URL

The public OSRM demo endpoint is used when `CATTRACKS_ROUTING_URL` is not set.
Do not commit credentials or local `.env` files.

## Deployment

The Vercel entry point is `api/index.py`. Static assets, templates, and the
canonical GTFS feed are included by `vercel.json`.

Deploy from the repository root:

```bash
npx vercel --prod
```

The application also includes `Dockerfile` and `Procfile` configurations for
production-like local or container deployments:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 website.app:app
```

## Repository layout

```text
api/                    Vercel entry point
data/gtfs/              Canonical runtime GTFS feed
data/gtfs_official/     Preserved source GTFS feed
docs/                   Design and API documentation
geopkg/                 GIS source data
scripts/                Developer utilities and smoke tests
src/                    Routing, GTFS, and road-routing services
tests/                  Python regression tests
website/                Flask app, templates, and frontend assets
vercel.json             Vercel build and routing configuration
```

## Contributing

Use a focused branch and run the test and compile commands above before
opening a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for repository
workflow guidance.

## License

This project is licensed under the MIT License; see [LICENSE](LICENSE).
