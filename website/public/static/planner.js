(function () {
  const { createElement: h, useEffect, useRef, useState } = React;
  const stops = JSON.parse(document.getElementById("planner-stops").textContent);
  const initial = JSON.parse(document.getElementById("planner-initial").textContent);

  const minutes = seconds => seconds < 60 ? "< 1 min" : `${Math.round(seconds / 60)} min`;
  const miles = meters => `${(meters / 1609.344).toFixed(2)} mi`;
  const iconPaths = {
    map: [h("path", { d: "m9 18-6 3V6l6-3 6 3 6-3v15l-6 3-6-3Z" }), h("path", { d: "M9 3v15M15 6v15" })],
    route: [h("circle", { cx: "6", cy: "5", r: "2.5" }), h("circle", { cx: "18", cy: "19", r: "2.5" }), h("path", { d: "M6 7.5v2a3 3 0 0 0 3 3h3a3 3 0 0 1 3 3v1M15 16.5l2 2 2-2" })],
    arrow: [h("path", { d: "M5 12h13M13 6l6 6-6 6" })]
  };
  function Icon({ name }) {
    return h("svg", { className: "ui-icon", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true" }, iconPaths[name]);
  }

  function MapView({ route }) {
    const target = useRef(null);
    const map = useRef(null);
    const layer = useRef(null);
    useEffect(() => {
      map.current = L.map(target.current, { zoomControl: false }).setView([37.3612, -120.4324], 13);
      L.control.zoom({ position: "bottomright" }).addTo(map.current);
      const streetBase = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 19 }
      );
      const streetLabels = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 19 }
      );
      const streets = L.layerGroup([streetBase, streetLabels]).addTo(map.current);
      const satellite = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 19, attribution: "Tiles &copy; Esri" }
      );
      L.control.layers({ "Clean street map": streets, "Satellite": satellite }, null, {
        position: "topright",
        collapsed: true
      }).addTo(map.current);
      return () => map.current.remove();
    }, []);
    useEffect(() => {
      if (!map.current || !route) return;
      if (layer.current) layer.current.remove();
      const points = route.geometry.coordinates.map(point => [point[1], point[0]]);
      const routeLayers = [
        L.polyline(points, { color: "#075985", weight: 6, opacity: 0.9 })
      ];
      const stopPoints = route.points || [];
      const pointByName = new Map(stopPoints.map(point => [point.name, point]));
      const boardingNames = new Set(
        (route.segments || [])
          .filter(segment => segment.mode === "bus")
          .map(segment => segment.from)
      );
      const alightingNames = new Set(
        (route.segments || [])
          .filter(segment => segment.mode === "bus")
          .map(segment => segment.to)
      );
      const poiSteps = (route.segments || []).map((segment, index) => ({
        name: segment.from,
        number: index + 1
      }));
      const locations = new Map();
      poiSteps.forEach(({ name, number }) => {
        const point = pointByName.get(name);
        if (!point) return;
        const locationKey = `${point.latitude}|${point.longitude}`;
        const overlapCount = locations.get(locationKey) || 0;
        locations.set(locationKey, overlapCount + 1);
        const position = [Number(point.latitude), Number(point.longitude)];
        const isFirst = number === 1;
        const stepNumber = number;
        const role = isFirst
          ? "Starting point"
          : boardingNames.has(point.name)
            ? "Board here"
            : alightingNames.has(point.name)
              ? "Get off here"
              : "Transfer stop";
        const poi = L.marker(position, {
          icon: L.divIcon({
            className: "route-poi-icon",
            html: `<span aria-label="Route step ${stepNumber}" style="display:grid;place-items:center;width:28px;height:28px;border:3px solid #002147;border-radius:50%;background:#ffd700;color:#002147;font-size:12px;font-weight:900;box-shadow:0 2px 8px rgba(15,23,42,.3);transform:translateX(${(overlapCount - 0.5) * 18}px);">${stepNumber}</span>`,
            iconSize: [30, 30],
            iconAnchor: [15, 15]
          }),
          title: `${stepNumber}. ${point.name}`
        });
        poi.bindTooltip(point.name, { direction: "top", offset: [0, -8] });
        poi.bindPopup(`<strong>Step ${stepNumber} · ${role}</strong><br>${point.name}<br><small>${Number(point.latitude).toFixed(5)}, ${Number(point.longitude).toFixed(5)}</small>`);
        routeLayers.push(poi);
      });
      layer.current = L.layerGroup(routeLayers).addTo(map.current);
      map.current.fitBounds(L.latLngBounds(points), { padding: [28, 28] });
    }, [route]);
    return h("div", { ref: target, className: "route-map", "aria-label": "Map showing the selected route" });
  }

  function Segment({ segment, index }) {
    const labels = { bus: "Bus", walk: "Walk", drive: "Drive", transfer: "Transfer" };
    return h("li", { className: `route-step route-step-${segment.mode}` },
      h("span", { className: "step-number" }, index + 1),
      h("div", { className: "step-content" },
        h("strong", null, `${labels[segment.mode] || segment.mode} · ${segment.route}`),
        h("span", null, `${segment.from} → ${segment.to}`),
        h("small", null, `${minutes(segment.travel_time)} · ${miles(segment.distance_meters)}`)
      )
    );
  }

  function Directions({ directions }) {
    if (!directions || !directions.length) return null;
    return h("details", { className: "route-directions" },
      h("summary", null, "Turn-by-turn road directions"),
      h("ol", null, directions.map((direction, index) =>
        h("li", { key: `${direction.instruction}-${index}` },
          h("span", null, direction.instruction),
          h("small", null, `${minutes(direction.duration_seconds)} · ${miles(direction.distance_meters)}`)
        )
      ))
    );
  }

  function Planner() {
    const [from, setFrom] = useState(initial.from || "");
    const [to, setTo] = useState(initial.to || "");
    const [departureTime, setDepartureTime] = useState(initial.departure_time || "");
    const [route, setRoute] = useState(initial.route || null);
    const [status, setStatus] = useState(initial.route ? "success" : initial.message ? "error" : "idle");
    const [message, setMessage] = useState(initial.message || "");
    async function submit(event) {
      event.preventDefault();
      if (!from.trim() || !to.trim()) return setMessage("Enter both a departure and destination.");
      setStatus("loading"); setMessage("");
      try {
        const response = await fetch("/api/route", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            from: from.trim(),
            to: to.trim(),
            departure_time: departureTime
          })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.message || "No route was found.");
        setRoute(result); setStatus("success");
      } catch (error) {
        setRoute(null); setStatus("error"); setMessage(error.message);
      }
    }
    return h("div", { className: "react-planner" },
      h("section", { className: "planner-hero" },
        h("div", null, h("p", { className: "eyebrow" }, "Door-to-door planning"),
          h("h1", null, "Move through Merced with confidence."),
          h("p", { className: "planner-subtitle" }, "Enter an address, landmark, or CatTracks stop. We connect walking, driving, transfers, and transit.")
        ),
        h("div", { className: "planner-status" }, h("span", { className: `status-dot status-${status}${initial.network_online === false ? " status-offline" : ""}` }), status === "loading" ? "Finding your route" : initial.network_online === false ? "CatTracks network offline" : "CatTracks network online")
      ),
      h("section", { className: "planner-workspace" },
        h("form", { className: "planner-card reactive-form", onSubmit: submit },
          h("div", { className: "card-heading" }, h("span", { className: "feature-icon" }, h(Icon, { name: "route" })), h("span", null, "Plan a journey")),
          h("label", { htmlFor: "from-stops" }, "Starting point"),
          h("input", { id: "from-stops", list: "stop-list", value: from, onChange: e => setFrom(e.target.value), placeholder: "Address or CatTracks stop", required: true }),
          h("label", { htmlFor: "to-stops" }, "Destination"),
          h("input", { id: "to-stops", list: "stop-list", value: to, onChange: e => setTo(e.target.value), placeholder: "Address or CatTracks stop", required: true }),
          h("label", { htmlFor: "departure-time" }, "Departure time"),
          h("input", { id: "departure-time", type: "time", value: departureTime, onChange: e => setDepartureTime(e.target.value), required: true }),
          h("datalist", { id: "stop-list" }, stops.map(stop => h("option", { key: stop, value: stop }))),
          h("button", { className: "button button-primary", disabled: status === "loading" }, status === "loading" ? "Planning route…" : h(React.Fragment, null, "Find my route ", h(Icon, { name: "arrow" }))),
          message && h("p", { className: "planner-message" }, message)
        ),
        h("div", { className: "route-panel reactive-results", "aria-live": "polite" },
          route ? h("div", null,
            h("div", { className: "result-heading" }, h("div", null, h("p", { className: "eyebrow" }, "Route found"), h("h2", null, minutes(route.duration_seconds)), route.departure_time && h("small", null, `Leaving at ${route.departure_time}`)), h("strong", { className: "distance-pill" }, miles(route.distance_meters))),
            route.access_stops && h("p", { className: "route-access" }, `Board at ${route.access_stops.from} · Get off at ${route.access_stops.to}`),
            route.schedule_message && h("p", { className: "planner-schedule-message" }, route.schedule_message),
            h(Directions, { directions: route.directions }),
            h("ol", { className: "route-results" }, route.segments.map((segment, index) => h(Segment, { segment, index, key: `${segment.from}-${segment.to}-${index}` })))
          ) : h("div", { className: "empty-results" }, h("span", { className: "feature-icon" }, h(Icon, { name: "map" })), h("h2", null, "Your route will appear here"), h("p", null, "Search for a trip to see the best way across the CatTracks network."))
        )
      ),
      h("section", { className: "map-section" }, h(MapView, { route }))
    );
  }
  ReactDOM.createRoot(document.getElementById("planner-app")).render(h(Planner));
})();
