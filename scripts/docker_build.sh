valhalla_build_tiles -c valhalla.json /data/openstreetmap/*.osm.pbf; valhalla_export_edges --config valhalla.json > /data/polylines/pbf_extract.polyline;
