(function () {
  const { createElement: h, useEffect, useRef, useState } = React;
  const stops = JSON.parse(document.getElementById("planner-stops").textContent);

  const minutes = seconds => seconds < 60 ? "< 1 min" : `${Math.round(seconds / 60)} min`;
  const miles = meters => `${(meters / 1609.344).toFixed(2)} mi`;

  function MapView({ route }) {
    const target = useRef(null);
    const map = useRef(null);
    const layer = useRef(null);
    useEffect(() => {
      map.current = L.map(target.current, { zoomControl: false }).setView([37.3612, -120.4324], 13);
      L.control.zoom({ position: "bottomright" }).addTo(map.current);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19, attribution: "&copy; OpenStreetMap contributors"
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
    const [from, setFrom] = useState("");
    const [to, setTo] = useState("");
    const [route, setRoute] = useState(null);
    const [status, setStatus] = useState("idle");
    const [message, setMessage] = useState("");
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
          h("div", { className: "card-heading" }, h("span", { className: "feature-icon" }, "↗"), h("span", null, "Plan a journey")),
          h("label", { htmlFor: "from-stops" }, "Starting point"),
          h("input", { id: "from-stops", list: "stop-list", value: from, onChange: e => setFrom(e.target.value), placeholder: "Address or CatTracks stop", required: true }),
          h("label", { htmlFor: "to-stops" }, "Destination"),
          h("input", { id: "to-stops", list: "stop-list", value: to, onChange: e => setTo(e.target.value), placeholder: "Address or CatTracks stop", required: true }),
          h("datalist", { id: "stop-list" }, stops.map(stop => h("option", { key: stop, value: stop }))),
          h("button", { className: "button button-primary", disabled: status === "loading" }, status === "loading" ? "Planning route…" : "Find my route →"),
          message && h("p", { className: "planner-message" }, message)
        ),
        h("div", { className: "route-panel reactive-results", "aria-live": "polite" },
          route ? h("div", null,
            h("div", { className: "result-heading" }, h("div", null, h("p", { className: "eyebrow" }, "Route found"), h("h2", null, minutes(route.duration_seconds))), h("strong", { className: "distance-pill" }, miles(route.distance_meters))),
            route.access_stops && h("p", { className: "route-access" }, `Board at ${route.access_stops.from} · Get off at ${route.access_stops.to}`),
            h("ol", { className: "route-results" }, route.segments.map((segment, index) => h(Segment, { segment, index, key: `${segment.from}-${segment.to}-${index}` })))
          ) : h("div", { className: "empty-results" }, h("span", { className: "feature-icon" }, "⌁"), h("h2", null, "Your route will appear here"), h("p", null, "Search for a trip to see the best way across the CatTracks network."))
        )
      ),
      h("section", { className: "map-section" }, h(MapView, { route }))
    );
  }
  ReactDOM.createRoot(document.getElementById("planner-app")).render(h(Planner));
})();
