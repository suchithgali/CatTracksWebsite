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
      L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
        maxZoom: 20,
        subdomains: "abcd",
        attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
      }).addTo(map.current);
      return () => map.current.remove();
    }, []);
    useEffect(() => {
      if (!map.current || !route) return;
      if (layer.current) layer.current.remove();
      const points = route.geometry.coordinates.map(point => [point[1], point[0]]);
      layer.current = L.layerGroup([
        L.polyline(points, { color: "#075985", weight: 6, opacity: 0.9 }),
        L.marker(points[0]).bindPopup(`<strong>Start</strong><br>${route.from}`),
        L.marker(points[points.length - 1]).bindPopup(`<strong>Destination</strong><br>${route.to}`)
      ]).addTo(map.current);
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

  function Planner() {
    const [from, setFrom] = useState(initial.from || "");
    const [to, setTo] = useState(initial.to || "");
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
          body: JSON.stringify({ from: from.trim(), to: to.trim() })
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
        h("div", { className: "planner-status" }, h("span", { className: `status-dot status-${status}` }), status === "loading" ? "Finding your route" : "CatTracks network online")
      ),
      h("section", { className: "planner-workspace" },
        h("form", { className: "planner-card reactive-form", onSubmit: submit },
          h("div", { className: "card-heading" }, h("span", { className: "feature-icon" }, h(Icon, { name: "route" })), h("span", null, "Plan a journey")),
          h("label", { htmlFor: "from-stops" }, "Starting point"),
          h("input", { id: "from-stops", list: "stop-list", value: from, onChange: e => setFrom(e.target.value), placeholder: "Address or CatTracks stop", required: true }),
          h("label", { htmlFor: "to-stops" }, "Destination"),
          h("input", { id: "to-stops", list: "stop-list", value: to, onChange: e => setTo(e.target.value), placeholder: "Address or CatTracks stop", required: true }),
          h("datalist", { id: "stop-list" }, stops.map(stop => h("option", { key: stop, value: stop }))),
          h("button", { className: "button button-primary", disabled: status === "loading" }, status === "loading" ? "Planning route…" : h(React.Fragment, null, "Find my route ", h(Icon, { name: "arrow" }))),
          message && h("p", { className: "planner-message" }, message)
        ),
        h("div", { className: "route-panel reactive-results", "aria-live": "polite" },
          route ? h("div", null,
            h("div", { className: "result-heading" }, h("div", null, h("p", { className: "eyebrow" }, "Route found"), h("h2", null, minutes(route.duration_seconds))), h("strong", { className: "distance-pill" }, miles(route.distance_meters))),
            route.access_stops && h("p", { className: "route-access" }, `Board at ${route.access_stops.from} · Get off at ${route.access_stops.to}`),
            h("ol", { className: "route-results" }, route.segments.map((segment, index) => h(Segment, { segment, index, key: `${segment.from}-${segment.to}-${index}` })))
          ) : h("div", { className: "empty-results" }, h("span", { className: "feature-icon" }, h(Icon, { name: "map" })), h("h2", null, "Your route will appear here"), h("p", null, "Search for a trip to see the best way across the CatTracks network."))
        )
      ),
      h("section", { className: "map-section" }, h(MapView, { route }))
    );
  }
  ReactDOM.createRoot(document.getElementById("planner-app")).render(h(Planner));
})();
