import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCollegeDirectionsUrl,
  buildPointSearchUrl,
  normalizeTransitPoints,
} from "../lib/map-route.mjs";

test("normalizeTransitPoints uses backend transit_points when available", () => {
  const points = normalizeTransitPoints({
    transit_points: [
      {
        id: "railway_local",
        kind: "railway_local",
        label: "Local Railway",
        name: "Coimbatore Junction",
        latitude: 11.0018,
        longitude: 76.9661,
        distance_km: 4.4,
        available: true,
      },
    ],
  });

  assert.deepEqual(points, [
    {
      id: "railway_local",
      kind: "railway_local",
      label: "Local Railway",
      name: "Coimbatore Junction",
      latitude: 11.0018,
      longitude: 76.9661,
      distanceKm: 4.4,
      hasCoordinates: true,
      available: true,
    },
  ]);
});

test("normalizeTransitPoints falls back to legacy flat college fields", () => {
  const points = normalizeTransitPoints({
    nearest_railway_station: "Coimbatore Junction",
    nearest_railway_station_latitude: 11.0018,
    nearest_railway_station_longitude: 76.9661,
    nearest_railway_distance_km: 4.4,
    nearest_bus_station: "Gandhipuram Town Bus Stand",
    nearest_bus_station_latitude: null,
    nearest_bus_station_longitude: null,
    nearest_bus_station_distance_km: 5.1,
  });

  assert.equal(points.length, 2);
  assert.equal(points[0].id, "railway_local");
  assert.equal(points[0].hasCoordinates, true);
  assert.equal(points[1].id, "bus_terminus");
  assert.equal(points[1].hasCoordinates, false);
});

test("Google Maps URLs prefer coordinates with name label and fall back to safe search text", () => {
  assert.equal(
    buildPointSearchUrl({
      name: "Coimbatore Junction",
      latitude: 11.0018,
      longitude: 76.9661,
    }),
    "https://www.google.com/maps/search/?api=1&query=Coimbatore%20Junction%20%40%2011.0018%2C76.9661",
  );

  assert.equal(
    buildPointSearchUrl({
      label: "Bus Terminus",
      name: "Central Bus Stand",
      latitude: null,
      longitude: null,
    }),
    "https://www.google.com/maps/search/?api=1&query=Central%20Bus%20Stand%2C%20Bus%20Terminus%2C%20Tamil%20Nadu",
  );
});

test("college directions URL uses selected college origin and transit point destination with labels", () => {
  const url = buildCollegeDirectionsUrl(
    { name: "Sample Engineering College", latitude: 11.02, longitude: 77.01 },
    { name: "Central Bus Stand", latitude: 11.12, longitude: 77.11 },
  );

  assert.equal(
    url,
    "https://www.google.com/maps/dir/?api=1&origin=Sample+Engineering+College+%40+11.02%2C77.01&destination=Central+Bus+Stand+%40+11.12%2C77.11",
  );
});


test("normalizeTransitPoints omits fabricated bypass bus stop names", () => {
  const points = normalizeTransitPoints({
    name: "Sample Engineering College",
    nearest_bus_station: "Central Bus Stand",
    nearest_bus_station_latitude: 11.1,
    nearest_bus_station_longitude: 77.1,
    nearest_bus_station_distance_km: 4,
    nearest_bus_stop: "Sample Engineering College Bypass Bus Stop",
    nearest_bus_stop_latitude: 11.004,
    nearest_bus_stop_longitude: 77.004,
    nearest_bus_stop_distance_km: 0.65,
  });

  assert.deepEqual(points.map((point) => point.id), ["bus_terminus"]);
});

test("normalizeTransitPoints relabels unnamed OSM bus stops without inventing college names", () => {
  const points = normalizeTransitPoints({
    name: "Sample Engineering College",
    nearest_bus_stop: "Sample Engineering College Bus Stop",
    nearest_bus_stop_latitude: 11.004,
    nearest_bus_stop_longitude: 77.004,
    nearest_bus_stop_distance_km: 0.65,
  });

  assert.equal(points.length, 1);
  assert.equal(points[0].name, "Unnamed OSM bus stop near campus");
  assert.equal(points[0].hasCoordinates, true);
});
