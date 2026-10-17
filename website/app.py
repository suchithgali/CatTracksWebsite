from pathlib import Path
import csv

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os

from src.route_service import RouteError, find_route_request, get_graph

PROJECT_ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__, static_folder="public/static", static_url_path="/public/static")

# Database config. SQLite is the local default; production can provide DATABASE_URL.
db_url = os.environ.get("DATABASE_URL")
if db_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = Path(app.instance_path) / "cattracks.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

db = SQLAlchemy(app)
GTFS_STOPS = PROJECT_ROOT / "data" / "gtfs" / "stops.txt"
GTFS_ROUTES = PROJECT_ROOT / "data" / "gtfs" / "routes.txt"
OFFICIAL_ROUTES_URL = (
    "https://taps.ucmerced.edu/transportation/cattracks-and-route-uc/routes"
)

OFFICIAL_SCHEDULES = [
    ("Bobcat Express", "Campus, Bellevue & R Street", "Mon - Fri | 6:29 AM - 9:20 PM", "https://taps.ucmerced.edu/node/4711"),
    ("C-1 Line", "Campus, G Street & Granville Apartments", "Mon - Fri | 6:20 AM - 10:28 PM", "https://taps.ucmerced.edu/node/4816"),
    ("C-2 Line", "Campus & Village Apartments", "Mon - Fri | 6:20 AM - 10:07 PM", "https://taps.ucmerced.edu/node/4821"),
    ("E-1 Line", "Campus, Moraga & Downtown", "Sat - Sun | 8:30 AM - 11:06 PM", "https://taps.ucmerced.edu/node/4826"),
    ("E-2 Line", "Yosemite Avenue & Park and Ride Bellevue Road", "Sat - Sun | 11:05 AM - 9:56 PM", "https://taps.ucmerced.edu/node/4851"),
    ("FastCat", "Park and Ride Bellevue Road & R Street", "Mon - Fri | 6:35 AM - 10:25 PM", "https://taps.ucmerced.edu/node/4831"),
    ("FastCat 2", "Park and Ride Bellevue Road & R Street", "Mon - Fri | 8:30 AM - 9:45 PM", "https://taps.ucmerced.edu/node/4836"),
    ("G Line", "R Street, El Redondo & Village Apartments", "Mon - Fri | 6:30 AM - 10:03 PM", "https://taps.ucmerced.edu/node/4841"),
    ("Yosemite Express", "Campus & Moraga, G Street", "Mon - Fri | 9:00 AM - 10:09 PM", "https://taps.ucmerced.edu/node/4846"),
    ("Route UC", "Paulson Avenue & Olive Avenue", "Mon - Fri | 6:00 AM - 8:00 PM", "https://taps.ucmerced.edu/sites/g/files/ufvvjh1811/f/documents/Fall/2025/route_uc_fall_2025_8_18_25.pdf"),
    ("M-1", "Grocery Outlet & T Street, 3rd Street", "Mon - Fri | 6:00 AM - 8:00 PM · Sat - Sun | 8:00 AM - 6:00 PM", "https://taps.ucmerced.edu/sites/g/files/ufvvjh1811/f/documents/Fall/2025/m-1_fall_2025_8_18_2025.pdf"),
    ("M-2", "Best Buy & Walmart", "Mon - Fri | 6:00 AM - 8:00 PM · Sat - Sun | 8:30 AM - 6:00 PM", "https://taps.ucmerced.edu/sites/g/files/ufvvjh1811/f/documents/Fall/2025/m-2_fall_2025_8_18_2025.pdf"),
    ("M-3", "County Admin & West Avenue, 1st Avenue", "Mon - Fri | 6:00 AM - 8:00 PM · Sat - Sun | 8:00 AM - 6:00 PM", "https://taps.ucmerced.edu/sites/g/files/ufvvjh1811/f/documents/Fall/2025/m-3_fall_2025_8_18_2025.pdf"),
    ("M-4", "Yosemite High School & Park and Ride Bellevue Road", "Mon - Fri | 6:00 AM - 8:30 PM · Sat - Sun | 8:00 AM - 6:00 PM", "https://taps.ucmerced.edu/sites/g/files/ufvvjh1811/f/documents/Fall/2025/m-4_fall_2025_8_18_2025pdf.pdf"),
    ("M-5", "Amtrak & Rancho San Miguel", "Mon - Fri | 6:00 AM - 8:00 PM · Sat - Sun | 8:00 AM - 6:00 PM", "https://taps.ucmerced.edu/sites/g/files/ufvvjh1811/f/documents/Fall/2025/m-5_fall_2025_8_18_2025.pdf"),
    ("M-6", "Santa Fe & SaveMart", "Mon - Fri | 7:00 AM - 8:00 PM · Sat - Sun | 8:00 AM - 6:00 PM", "https://taps.ucmerced.edu/sites/g/files/ufvvjh1811/f/documents/Fall/2025/m-6_fall_2025_8_18_2025.pdf"),
    ("M-7", "B Street & Rescue Mission", "Mon - Fri | 6:00 AM - 8:00 PM · Sat - Sun | 8:00 AM - 6:00 PM", "https://taps.ucmerced.edu/sites/g/files/ufvvjh1811/f/documents/Fall/2025/m-7_fall_2025_8_18_2025.pdf"),
]


def load_stop_names() -> list[str]:
    if not GTFS_STOPS.exists():
        app.logger.error("GTFS stops file is missing: %s", GTFS_STOPS)
        return []
    with GTFS_STOPS.open(newline="", encoding="utf-8") as source:
        stops = csv.DictReader(source)
        if "stop_name" not in (stops.fieldnames or []):
            app.logger.error("GTFS stops file has no stop_name column")
            return []
        names = [row["stop_name"].strip() for row in stops if row.get("stop_name", "").strip()]
    return sorted(set(names))


def load_routes() -> list[dict[str, str]]:
    if not GTFS_ROUTES.exists():
        app.logger.error("GTFS routes file is missing: %s", GTFS_ROUTES)
        return []
    with GTFS_ROUTES.open(newline="", encoding="utf-8") as source:
        routes = csv.DictReader(source)
        return [
            {
                "name": row["route_short_name"].strip(),
                "description": row["route_long_name"].strip(),
            }
            for row in routes
            if row.get("route_short_name", "").strip()
        ]

class Stops(db.Model):
    stop_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


with app.app_context():
    db.create_all()
    if not Stops.query.first():
        db.session.add_all(Stops(name=name) for name in load_stop_names())
        db.session.commit()


def available_stops() -> list[str]:
    return [stop.name for stop in Stops.query.order_by(Stops.name).all()]


@app.route('/', methods=['GET'])
def index():
    return render_template("index.html", stops=available_stops())

@app.route("/plan", methods=["GET", "POST"])
def plan():
    message = None
    route = None
    if request.method == "POST":
        from_stop = request.form.get("from-stops", "").strip()
        to_stop = request.form.get("to-stops", "").strip()
        try:
            route = find_route_request(from_stop, to_stop)
        except RouteError as error:
            message = str(error)

    return render_template(
        "liveroutes.html",
        message=message,
        route=route,
        from_stop=request.form.get("from-stops", ""),
        to_stop=request.form.get("to-stops", ""),
        stops=available_stops(),
    )

@app.route("/schedules")
def schedules():
    routes = [
        {"name": name, "description": description, "hours": hours, "schedule_url": url}
        for name, description, hours, url in OFFICIAL_SCHEDULES
    ]
    return render_template(
        "schedules.html",
        routes=routes,
        official_routes_url=OFFICIAL_ROUTES_URL,
    )

@app.route("/planner")
def planner():
    return render_template("live.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/health")
def health():
    try:
        graph = get_graph()
        return jsonify({
            "status": "ok",
            "service": "cattracks-web",
            "routing_engine": True,
            "graph_nodes": graph.number_of_nodes(),
            "graph_edges": graph.number_of_edges(),
        })
    except Exception:
        app.logger.exception("Routing graph failed health check")
        return jsonify({
            "status": "error",
            "service": "cattracks-web",
            "routing_engine": False,
        }), 503


@app.route("/api/route", methods=["POST"])
def api_route():
    payload = request.get_json(silent=True) or {}
    from_stop = str(payload.get("from", "")).strip()
    to_stop = str(payload.get("to", "")).strip()

    if not from_stop or not to_stop:
        return jsonify({"status": "error", "message": "Both stops are required."}), 400

    try:
        return jsonify(find_route_request(from_stop, to_stop))
    except RouteError as error:
        return jsonify({"status": "error", "message": str(error)}), 400

if __name__ == '__main__':
    app.run()