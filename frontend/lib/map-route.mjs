const UNNAMED_OSM_BUS_STOP_NAME = "Unnamed OSM bus stop near campus";

const LEGACY_TRANSIT_FIELDS = [
  {
    id: "railway_local",
    kind: "railway_local",
    label: "Local Railway",
    nameKey: "nearest_railway_station",
    latKey: "nearest_railway_station_latitude",
    lngKey: "nearest_railway_station_longitude",
    distanceKey: "nearest_railway_distance_km",
  },
  {
    id: "railway_express",
    kind: "railway_express",
    label: "Express Railway",
    nameKey: "nearest_express_station",
    latKey: "nearest_express_station_latitude",
    lngKey: "nearest_express_station_longitude",
    distanceKey: "nearest_express_station_distance_km",
  },
  {
    id: "bus_terminus",
    kind: "bus_terminus",
    label: "Bus Terminus",
    nameKey: "nearest_bus_station",
    latKey: "nearest_bus_station_latitude",
    lngKey: "nearest_bus_station_longitude",
    distanceKey: "nearest_bus_station_distance_km",
  },
  {
    id: "bus_stop",
    kind: "bus_stop",
    label: "Local Bus Stop",
    nameKey: "nearest_bus_stop",
    latKey: "nearest_bus_stop_latitude",
    lngKey: "nearest_bus_stop_longitude",
    distanceKey: "nearest_bus_stop_distance_km",
  },
];

function hasNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function isSyntheticBypassStop(point) {
  return point?.kind === "bus_stop" && typeof point.name === "string" && point.name.trim().endsWith("Bypass Bus Stop");
}

function isInventedUnnamedStop(point, collegeName = "") {
  return point?.kind === "bus_stop" && collegeName && point.name === `${collegeName} Bus Stop`;
}

function normalizePoint(point, collegeName = "") {
  if (isSyntheticBypassStop(point)) return null;
  const latitude = hasNumber(point.latitude) ? point.latitude : null;
  const longitude = hasNumber(point.longitude) ? point.longitude : null;
  const distanceKm = hasNumber(point.distance_km)
    ? point.distance_km
    : hasNumber(point.distanceKm)
      ? point.distanceKm
      : null;

  return {
    id: point.id,
    kind: point.kind || point.id,
    label: point.label,
    name: isInventedUnnamedStop(point, collegeName) ? UNNAMED_OSM_BUS_STOP_NAME : point.name,
    latitude,
    longitude,
    distanceKm,
    hasCoordinates: latitude !== null && longitude !== null,
    available: Boolean(point.available ?? point.name),
  };
}

export function normalizeTransitPoints(college = {}) {
  if (Array.isArray(college.transit_points) && college.transit_points.length > 0) {
    return college.transit_points
      .filter((point) => point?.name)
      .map((point) => normalizePoint(point, college.name || ""))
      .filter(Boolean);
  }

  return LEGACY_TRANSIT_FIELDS.flatMap((field) => {
    const name = college[field.nameKey];
    if (!name) return [];

    return normalizePoint({
      id: field.id,
      kind: field.kind,
      label: field.label,
      name,
      latitude: college[field.latKey],
      longitude: college[field.lngKey],
      distance_km: college[field.distanceKey],
      available: true,
    }, college.name || "") || [];
  });
}

function queryFromPlace(place, fallbackLabel = "") {
  const name = place?.name || fallbackLabel;
  const lat = place?.latitude;
  const lng = place?.longitude;

  if (name && hasNumber(lat) && hasNumber(lng)) {
    return `${name} @ ${lat},${lng}`;
  }

  if (hasNumber(lat) && hasNumber(lng)) {
    return `${lat},${lng}`;
  }

  return [place?.name, fallbackLabel, "Tamil Nadu"].filter(Boolean).join(", ");
}

export function buildPointSearchUrl(point) {
  const query = queryFromPlace(point, point?.label || "");
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

export function buildCollegeDirectionsUrl(college, point) {
  const origin = queryFromPlace(college, "College");
  const destination = queryFromPlace(point, point?.label || "");
  const params = new URLSearchParams({
    api: "1",
    origin,
    destination,
  });
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export function buildUserDirectionsUrl(point) {
  const destination = queryFromPlace(point, point?.label || "");
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(destination)}`;
}
