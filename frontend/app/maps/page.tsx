"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  Bus,
  Compass,
  ExternalLink,
  Globe,
  Layers,
  MapPin,
  Navigation,
  Phone,
  Search,
  TrainFront,
} from "lucide-react";
import Script from "next/script";

import { Badge, PageHeader, Surface } from "@/components/ui";
import { FeatureGate } from "@/components/feature-gate";
import { fetchMapColleges, fetchTfcLocations } from "@/lib/api.mjs";
import {
  buildCollegeDirectionsUrl,
  buildPointSearchUrl,
  buildUserDirectionsUrl,
  normalizeTransitPoints,
} from "@/lib/map-route.mjs";
import { cleanCollegeName } from "@/lib/product";

type TabId = "colleges" | "tfc";
type MapViewMode = "map" | "route";
type TransitKind = "railway_local" | "railway_express" | "bus_terminus" | "bus_stop";

type TransitPoint = {
  id: string;
  kind: TransitKind;
  label: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  distanceKm: number | null;
  hasCoordinates: boolean;
  available: boolean;
};

const TABS: { id: TabId; label: string }[] = [
  { id: "colleges", label: "College Route Inspector" },
  { id: "tfc", label: "TFC Centres" },
];

const TRANSIT_STYLE: Record<TransitKind, { color: string; icon: "train" | "bus"; tone: "neutral" | "coral" | "safe" }> = {
  railway_local: { color: "#1d4ed8", icon: "train", tone: "neutral" },
  railway_express: { color: "#7c3aed", icon: "train", tone: "coral" },
  bus_terminus: { color: "#15803d", icon: "bus", tone: "safe" },
  bus_stop: { color: "#16a34a", icon: "bus", tone: "neutral" },
};

type LocationRow = {
  code: string;
  name: string;
  district: string;
  type: string;
  latitude?: number | null;
  longitude?: number | null;
  hostel_available?: boolean;
  boys_hostel_available?: boolean;
  girls_hostel_available?: boolean;
  transport_available?: boolean;
  website?: string;
  nearest_railway_station?: string | null;
  nearest_railway_station_latitude?: number | null;
  nearest_railway_station_longitude?: number | null;
  nearest_railway_distance_km?: number | null;
  nearest_express_station?: string | null;
  nearest_express_station_latitude?: number | null;
  nearest_express_station_longitude?: number | null;
  nearest_express_station_distance_km?: number | null;
  nearest_bus_station?: string | null;
  nearest_bus_station_latitude?: number | null;
  nearest_bus_station_longitude?: number | null;
  nearest_bus_station_distance_km?: number | null;
  nearest_bus_stop?: string | null;
  nearest_bus_stop_latitude?: number | null;
  nearest_bus_stop_longitude?: number | null;
  nearest_bus_stop_distance_km?: number | null;
  transit_points?: unknown[];
  address?: string;
};

type TfcLocationRow = {
  centre_name: string;
  district: string;
  address: string;
  phone: string;
  latitude?: number;
  longitude?: number;
  google_maps_url?: string;
};

type UserLocation = {
  latitude: number;
  longitude: number;
  accuracy: number;
};

function hasCoordinates<T extends { latitude?: number | null; longitude?: number | null }>(
  item: T,
): item is T & { latitude: number; longitude: number } {
  return typeof item.latitude === "number" && typeof item.longitude === "number";
}

function createDotIcon(L: any, color: string, size = 18, pulse = false) {
  const dot = Math.max(5, Math.round(size / 3));
  return L.divIcon({
    className: "custom-leaflet-icon",
    html: `<div style="position: relative; width: ${size}px; height: ${size}px; border-radius: 9999px; background: ${color}; border: 2px solid white; box-shadow: 0 10px 20px rgba(15, 23, 42, 0.22); display: flex; align-items: center; justify-content: center;">${
      pulse
        ? `<span style="position:absolute; inset:0; border-radius:9999px; background:${color}; opacity:.42; animation: ping 1.8s cubic-bezier(0,0,.2,1) infinite;"></span>`
        : ""
    }<span style="position: relative; width: ${dot}px; height: ${dot}px; border-radius: 9999px; background: white;"></span></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function TransitIcon({ kind }: { kind: TransitKind }) {
  const style = TRANSIT_STYLE[kind];
  
  const colorClasses: Record<TransitKind, string> = {
    railway_local: "bg-blue-50 text-blue-600 border border-blue-100/50",
    railway_express: "bg-purple-50 text-purple-600 border border-purple-100/50",
    bus_terminus: "bg-emerald-50 text-emerald-600 border border-emerald-100/50",
    bus_stop: "bg-green-50 text-green-600 border border-green-100/50",
  };

  return (
    <div className={`p-2.5 rounded-xl flex items-center justify-center shrink-0 shadow-sm transition-all duration-300 ${colorClasses[kind]}`}>
      {style.icon === "train" ? (
        <TrainFront className="h-4.5 w-4.5 transition-transform duration-300 group-hover:scale-110" />
      ) : (
        <Bus className="h-4.5 w-4.5 transition-transform duration-300 group-hover:scale-110" />
      )}
    </div>
  );
}

function TransitPointCard({
  college,
  point,
}: {
  college: LocationRow;
  point: TransitPoint;
}) {
  const style = TRANSIT_STYLE[point.kind];
  
  const borderHighlight: Record<TransitKind, string> = {
    railway_local: "hover:border-blue-300",
    railway_express: "hover:border-purple-300",
    bus_terminus: "hover:border-emerald-300",
    bus_stop: "hover:border-green-300",
  };

  return (
    <div className={`group rounded-2xl border border-counsly-line bg-white/70 backdrop-blur-sm p-5 shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1 relative overflow-hidden flex flex-col justify-between min-h-[190px] ${borderHighlight[point.kind]}`}>
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-transparent to-counsly-soft/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

      <div className="space-y-3 relative z-10">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3 pr-16">
            <TransitIcon kind={point.kind} />
            <div className="min-w-0">
              <p className="text-[9px] font-extrabold uppercase tracking-widest text-counsly-muted leading-none">{point.label}</p>
              <h3 className="mt-1.5 text-sm font-extrabold leading-snug text-counsly-ink truncate" title={point.name}>{point.name}</h3>
            </div>
          </div>
          <div className="absolute top-5 right-5">
            <Badge tone={style.tone}>
              {point.distanceKm != null ? `${point.distanceKm.toFixed(0)} km` : "Distance pending"}
            </Badge>
          </div>
        </div>

        <p className="text-[11px] leading-relaxed text-counsly-muted">
          {point.hasCoordinates
            ? `Coordinates verified at ${point.latitude?.toFixed(4)}, ${point.longitude?.toFixed(4)}.`
            : "Coordinates pending; search direct on Google Maps."}
        </p>
      </div>

      <div className="mt-4 flex gap-2 relative z-10 pt-3 border-t border-counsly-line/40">
        <a className="button-secondary flex-1 inline-flex items-center justify-center gap-1 px-2 py-2 text-[11px] font-extrabold shadow-sm transition-all duration-300 hover:bg-counsly-soft" href={buildPointSearchUrl(point)} rel="noopener noreferrer" target="_blank">
          <MapPin className="h-3.5 w-3.5 text-counsly-coral" />
          <span>Open Card</span>
        </a>
        <a className="button-secondary flex-1 inline-flex items-center justify-center gap-1 px-2 py-2 text-[11px] font-extrabold shadow-sm transition-all duration-300 hover:bg-counsly-soft" href={buildCollegeDirectionsUrl(college, point)} rel="noopener noreferrer" target="_blank">
          <Navigation className="h-3.5 w-3.5 text-counsly-teal animate-pulse" />
          <span>Directions</span>
        </a>
      </div>
    </div>
  );
}

function MapsContent() {
  const [activeTab, setActiveTab] = useState<TabId>("colleges");
  const [viewMode, setViewMode] = useState<MapViewMode>("map");
  const [collegeRows, setCollegeRows] = useState<LocationRow[]>([]);
  const [tfcRows, setTfcRows] = useState<TfcLocationRow[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCollegeCode, setSelectedCollegeCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [routingStatus, setRoutingStatus] = useState("");
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapInstance, setMapInstance] = useState<any>(null);
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
  const [routesData, setRoutesData] = useState<Record<string, [number, number][]>>({});

  const mapLayersRef = useRef<any[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if ((window as any).L) {
      setMapLoaded(true);
      return;
    }

    const interval = window.setInterval(() => {
      if ((window as any).L) {
        setMapLoaded(true);
        window.clearInterval(interval);
      }
    }, 100);

    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    setLoading(true);
    setError("");
    Promise.all([
      fetchMapColleges({ limit: "500" }).catch(() => []),
      fetchTfcLocations({ limit: "500" }).catch(() => []),
    ])
      .then(([colleges, tfcs]) => {
        const nextColleges = Array.isArray(colleges) ? colleges : [];
        setCollegeRows(nextColleges);
        setTfcRows(Array.isArray(tfcs) ? tfcs : []);
        if (nextColleges.length > 0) setSelectedCollegeCode(nextColleges[0].code);
      })
      .catch(() => {
        setError("Could not load maps data from workspace API.");
      })
      .finally(() => setLoading(false));
  }, []);

  const filteredColleges = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return collegeRows;
    return collegeRows.filter((college) =>
      college.name.toLowerCase().includes(query) ||
      college.code.toLowerCase().includes(query) ||
      college.district.toLowerCase().includes(query),
    );
  }, [collegeRows, searchQuery]);

  const filteredTfcs = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return tfcRows;
    return tfcRows.filter((tfc) =>
      tfc.centre_name.toLowerCase().includes(query) ||
      tfc.district.toLowerCase().includes(query) ||
      tfc.address.toLowerCase().includes(query),
    );
  }, [tfcRows, searchQuery]);

  const selectedCollege = useMemo(() => {
    return collegeRows.find((college) => college.code === selectedCollegeCode) || null;
  }, [collegeRows, selectedCollegeCode]);

  const selectedTransitPoints = useMemo<TransitPoint[]>(() => {
    return selectedCollege ? normalizeTransitPoints(selectedCollege) : [];
  }, [selectedCollege]);

  const mappedTransitPoints = useMemo(() => {
    return selectedTransitPoints.filter((point) => point.hasCoordinates);
  }, [selectedTransitPoints]);

  const clearMapLayers = useCallback(() => {
    if (!mapInstance) return;
    mapLayersRef.current.forEach((layer) => {
      try {
        mapInstance.removeLayer(layer);
      } catch {
        // Leaflet may already have removed a layer during map teardown.
      }
    });
    mapLayersRef.current = [];
  }, [mapInstance]);

  useEffect(() => {
    setRoutesData({});
  }, [selectedCollegeCode, viewMode]);

  useEffect(() => {
    if (viewMode !== "route" || !selectedCollege || mappedTransitPoints.length === 0) {
      return;
    }

    const collegeLat = selectedCollege.latitude;
    const collegeLng = selectedCollege.longitude;
    if (collegeLat == null || collegeLng == null) return;

    mappedTransitPoints.forEach((point) => {
      if (routesData[point.id]) return;

      const pointLat = point.latitude;
      const pointLng = point.longitude;
      if (pointLat == null || pointLng == null) return;

      const routeUrl = `https://router.project-osrm.org/route/v1/driving/${collegeLng},${collegeLat};${pointLng},${pointLat}?overview=full&geometries=geojson`;

      fetch(routeUrl)
        .then((res) => {
          if (!res.ok) throw new Error("OSRM error");
          return res.json();
        })
        .then((routeData) => {
          if (routeData && routeData.routes && routeData.routes.length > 0) {
            const routeCoords = routeData.routes[0].geometry.coordinates;
            const coords = routeCoords.map((coord: any) => [coord[1], coord[0]] as [number, number]);
            setRoutesData((prev) => ({ ...prev, [point.id]: coords }));
          }
        })
        .catch((err) => {
          console.error(`OSRM error for point ${point.id}:`, err);
        });
    });
  }, [viewMode, selectedCollege, mappedTransitPoints, routesData]);

  useEffect(() => {
    if (!mapLoaded || typeof window === "undefined" || activeTab !== "colleges") return;
    const L = (window as any).L;
    if (!L) return;

    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });

    const container = document.getElementById("leaflet-map-canvas");
    if (!container) return;

    const map = L.map(container, { attributionControl: false }).setView([11.1271, 78.6569], 7);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);
    setMapInstance(map);

    return () => {
      map.remove();
      setMapInstance(null);
      mapLayersRef.current = [];
    };
  }, [activeTab, mapLoaded]);

  useEffect(() => {
    if (!mapInstance || typeof window === "undefined") return;
    const L = (window as any).L;
    if (!L) return;

    clearMapLayers();
    setRoutingStatus("");

    const nextLayers: any[] = [];
    const boundsPoints: [number, number][] = [];

    if (viewMode === "map") {
      filteredColleges.forEach((college) => {
        if (!hasCoordinates(college)) return;
        const selected = college.code === selectedCollegeCode;
        const marker = L.marker([college.latitude, college.longitude], {
          icon: createDotIcon(L, selected ? "#cc785c" : "#4fa59d", selected ? 24 : 13, selected),
          zIndexOffset: selected ? 1200 : 0,
        })
          .addTo(mapInstance)
          .bindPopup(`<strong>${cleanCollegeName(college.name)}</strong><br/>${college.district}`)
          .on("click", () => {
            setSelectedCollegeCode(college.code);
            setViewMode("route");
          });

        nextLayers.push(marker);
        boundsPoints.push([college.latitude, college.longitude]);
      });

      if (selectedCollege && hasCoordinates(selectedCollege)) {
        mapInstance.setView([selectedCollege.latitude, selectedCollege.longitude], 10, { animate: true, duration: 0.8 });
      } else if (boundsPoints.length > 1) {
        mapInstance.fitBounds(L.latLngBounds(boundsPoints), { padding: [32, 32] });
      }
    }

    if (viewMode === "route" && selectedCollege) {
      if (!hasCoordinates(selectedCollege)) {
        setRoutingStatus("Selected college coordinates are not available yet.");
      } else {
        const collegePoint: [number, number] = [selectedCollege.latitude, selectedCollege.longitude];
        const collegeMarker = L.marker(collegePoint, {
          icon: createDotIcon(L, "#cc785c", 26, true),
          zIndexOffset: 2000,
        })
          .addTo(mapInstance)
          .bindPopup(`<strong>${cleanCollegeName(selectedCollege.name)}</strong><br/>College campus.`)
          .openPopup();
        nextLayers.push(collegeMarker);
        boundsPoints.push(collegePoint);

        const sortedPoints = [...mappedTransitPoints].sort((a, b) => {
          const distA = a.distanceKm ?? 9999;
          const distB = b.distanceKm ?? 9999;
          return distB - distA; // Descending order (longest first, shortest last/on top)
        });

        sortedPoints.forEach((point) => {
          const style = TRANSIT_STYLE[point.kind];
          const transitPoint: [number, number] = [point.latitude as number, point.longitude as number];
          
          const isRoadRoute = !!routesData[point.id];
          const coords = routesData[point.id] || [collegePoint, transitPoint];

          const line = L.polyline(coords, {
            color: style.color,
            dashArray: isRoadRoute ? undefined : "8 8",
            opacity: isRoadRoute ? 0.9 : 0.75,
            weight: isRoadRoute ? 5 : 4,
          }).addTo(mapInstance);

          const marker = L.marker(transitPoint, {
            icon: createDotIcon(L, style.color, 22, false),
            zIndexOffset: 900,
          })
            .addTo(mapInstance)
             .bindPopup(`<strong>${point.name}</strong><br/>${point.label}${point.distanceKm != null ? `<br/>${point.distanceKm.toFixed(0)} km` : ""}`);

          nextLayers.push(line, marker);
          boundsPoints.push(transitPoint);
        });

        if (userLocation) {
          const userPoint: [number, number] = [userLocation.latitude, userLocation.longitude];
          const marker = L.marker(userPoint, {
            icon: createDotIcon(L, "#0f172a", 22, true),
            zIndexOffset: 1800,
          })
            .addTo(mapInstance)
            .bindPopup(`<strong>Your location</strong><br/>Accuracy: +/-${Math.round(userLocation.accuracy)} m`);
          nextLayers.push(marker);
          boundsPoints.push(userPoint);
        }

        setRoutingStatus(
          mappedTransitPoints.length > 0
            ? `${mappedTransitPoints.length} mapped transit point${mappedTransitPoints.length === 1 ? "" : "s"} shown. Open Google Maps for actual navigation.`
            : "No transit coordinates are available yet; use the Google Maps search links below.",
        );

        if (boundsPoints.length > 1) {
          mapInstance.fitBounds(L.latLngBounds(boundsPoints), { padding: [56, 56] });
        } else {
          mapInstance.setView(collegePoint, 13, { animate: true, duration: 0.8 });
        }
      }
    }

    mapLayersRef.current = nextLayers;

    return () => {
      nextLayers.forEach((layer) => {
        try {
          mapInstance.removeLayer(layer);
        } catch {
          // Ignore layer cleanup races during rerenders.
        }
      });
    };
  }, [clearMapLayers, filteredColleges, mappedTransitPoints, mapInstance, selectedCollege, selectedCollegeCode, userLocation, viewMode, routesData]);

  const handleFindMyLocation = () => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      setError("Geolocation is not supported by this browser.");
      return;
    }

    setError("");
    setRoutingStatus("Acquiring GPS location...");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        const inTamilNadu = 8.0 <= latitude && latitude <= 14.0 && 75.0 <= longitude && longitude <= 81.0;
        if (!inTamilNadu) {
          setError(`Location acquired (${latitude.toFixed(4)}, ${longitude.toFixed(4)}) is outside Tamil Nadu bounds.`);
          setRoutingStatus("");
          return;
        }
        setUserLocation({ latitude, longitude, accuracy: position.coords.accuracy });
        setViewMode("route");
      },
      () => {
        setError("Failed to acquire location. Enable GPS/location permission and try again.");
        setRoutingStatus("");
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 },
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <Script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" strategy="afterInteractive" onLoad={() => setMapLoaded(true)} />

      <PageHeader
        description="Explore each college campus on a premium live map alongside nearby railway stations, local bus stands, express transit links, and precise navigation routes."
        eyebrow="TNEA TRAVEL INSPECTOR"
        title="Dynamic College Travel Maps"
      />

      {/* Premium Glassmorphic Tab Navigation */}
      <Surface className="p-2 border border-counsly-line bg-counsly-soft/50 shadow-sm" tone="soft">
        <nav className="flex flex-wrap gap-2">
          {TABS.map((tab) => (
            <button
              className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold tracking-wide transition-all ${
                activeTab === tab.id
                  ? "bg-counsly-ink text-white shadow-md scale-[1.02]"
                  : "text-counsly-body hover:bg-white hover:text-counsly-ink"
              }`}
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setSearchQuery("");
              }}
              type="button"
            >
              <Compass className={`h-4 w-4 transition-transform duration-500 ${activeTab === tab.id ? "rotate-45 text-counsly-coral" : "text-counsly-muted"}`} />
              {tab.label}
            </button>
          ))}
        </nav>
      </Surface>

      {error && (
        <div className="flex items-start gap-3 rounded-2xl border-2 border-counsly-coral/20 bg-counsly-soft px-5 py-4 text-sm font-semibold text-counsly-coral animate-slide-up shadow-sm">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {activeTab === "colleges" && (
        <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
          {/* Left-Hand Interactive College Directory */}
          <div className="space-y-4 flex flex-col">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-counsly-muted" />
              <input
                className="field bg-white pl-10 border border-counsly-line shadow-sm focus:ring-2 focus:ring-counsly-coral/40"
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search college, code, or district..."
                value={searchQuery}
              />
              {filteredColleges.length > 0 && (
                <span className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-counsly-coral/10 border border-counsly-coral/20 px-2 py-0.5 text-[10px] font-extrabold text-counsly-ink">
                  {filteredColleges.length} found
                </span>
              )}
            </div>

            <Surface className="max-h-[600px] divide-y divide-counsly-line overflow-y-auto rounded-2xl border border-counsly-line shadow-lg" tone="paper">
              {loading ? (
                <div className="flex flex-col items-center justify-center gap-3 p-12 text-center text-sm text-counsly-muted">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-counsly-coral border-t-transparent" />
                  <p className="font-semibold text-xs tracking-wide">Loading colleges list...</p>
                </div>
              ) : filteredColleges.length === 0 ? (
                <div className="p-12 text-center text-sm text-counsly-muted leading-relaxed">
                  No colleges match your search parameters.
                </div>
              ) : (
                filteredColleges.map((college) => {
                  const isSelected = selectedCollegeCode === college.code;
                  return (
                    <button
                      className={`flex w-full items-start gap-4 p-4 text-left transition-all duration-300 border-l-4 border-transparent hover:bg-counsly-soft/60 hover:translate-x-1 ${
                        isSelected ? "bg-counsly-soft/90 border-l-counsly-coral font-bold shadow-sm" : ""
                      }`}
                      key={college.code}
                      onClick={() => {
                        setSelectedCollegeCode(college.code);
                        setViewMode("route");
                      }}
                      type="button"
                    >
                      <MapPin className={`mt-0.5 h-4.5 w-4.5 shrink-0 transition-colors duration-300 ${isSelected ? "text-counsly-coral" : "text-counsly-muted"}`} />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-2">
                          <span className="rounded-md border border-counsly-line bg-white px-2 py-0.5 text-[9px] font-extrabold text-counsly-ink shadow-sm">{college.code}</span>
                          <span className="text-[10px] font-semibold text-counsly-muted">{college.district}</span>
                        </div>
                        <h3 className="mt-1.5 truncate text-sm font-extrabold text-counsly-ink leading-snug">{cleanCollegeName(college.name)}</h3>
                      </div>
                    </button>
                  );
                })
              )}
            </Surface>
          </div>

          {/* Right-Hand Premium Interactive Map Workspace */}
          <div className="space-y-6">
            <div className="relative w-full overflow-hidden rounded-3xl border-2 border-counsly-line/60 bg-counsly-soft shadow-2xl transition-all duration-300">
              <div id="leaflet-map-canvas" className="z-10 h-[540px] w-full" />
              
              {/* Floating Glassmorphism Map Mode Selector in Top-Right */}
              <div className="absolute top-4 right-4 z-[1000] flex items-center gap-1 rounded-2xl border border-counsly-line bg-white/80 backdrop-blur-md p-1 shadow-2xl">
                <button
                  className={`inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-[11px] font-extrabold uppercase tracking-wider transition-all ${
                    viewMode === "map" ? "bg-counsly-ink text-white shadow-md scale-[1.02]" : "text-counsly-body hover:bg-white hover:text-counsly-ink"
                  }`}
                  onClick={() => setViewMode("map")}
                  type="button"
                >
                  <Layers className={`h-3.5 w-3.5 ${viewMode === "map" ? "text-counsly-coral" : "text-counsly-muted"}`} />
                  All colleges
                </button>
                <button
                  className={`inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-[11px] font-extrabold uppercase tracking-wider transition-all ${
                    viewMode === "route" ? "bg-counsly-ink text-white shadow-md scale-[1.02]" : "text-counsly-body hover:bg-white hover:text-counsly-ink"
                  }`}
                  onClick={() => setViewMode("route")}
                  type="button"
                >
                  <Navigation className={`h-3.5 w-3.5 ${viewMode === "route" ? "text-counsly-teal animate-pulse" : "text-counsly-muted"}`} />
                  Selected route
                </button>
              </div>

              {(loading || !mapLoaded) && (
                <div className="absolute inset-0 z-[1050] flex flex-col items-center justify-center bg-counsly-canvas/80 backdrop-blur-sm">
                  <div className="h-10 w-10 animate-spin rounded-full border-4 border-counsly-coral border-t-transparent shadow-md" />
                  <p className="mt-4 text-xs font-extrabold tracking-widest uppercase text-counsly-ink">Initializing map layers...</p>
                </div>
              )}

              {/* Floating Action Locate Button */}
              {!loading && (
                <button
                  className="absolute bottom-4 left-4 z-[1000] inline-flex items-center gap-2 rounded-2xl border border-counsly-line bg-white px-4 py-3 text-xs font-bold text-counsly-ink shadow-2xl transition-all duration-300 hover:bg-counsly-soft hover:scale-[1.03] active:scale-[0.98]"
                  onClick={handleFindMyLocation}
                  type="button"
                >
                  <Compass className="h-4.5 w-4.5 text-counsly-coral animate-[spin_4s_linear_infinite]" />
                  Verify my location
                </button>
              )}
            </div>

            {routingStatus && (
              <div className="rounded-2xl border-l-4 border-l-counsly-teal border border-counsly-line bg-counsly-canvas px-5 py-4 text-sm font-semibold text-counsly-body shadow-sm flex items-center gap-2 animate-fade-in">
                <Compass className="h-4 w-4 text-counsly-teal shrink-0 animate-pulse" />
                <span>{routingStatus}</span>
              </div>
            )}

            {/* Selected College Detail luxury Panel */}
            {selectedCollege ? (
              <Surface className="space-y-8 p-8 border border-counsly-line shadow-2xl rounded-3xl overflow-hidden relative" tone="paper">
                {/* Decorative background visual blob */}
                <div className="absolute top-0 right-0 -translate-y-12 translate-x-12 w-64 h-64 bg-gradient-to-br from-counsly-coral/10 to-counsly-teal/5 rounded-full filter blur-3xl pointer-events-none" />

                <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between relative z-10">
                  <div className="min-w-0 max-w-2xl">
                    <Badge tone="coral">{selectedCollege.code}</Badge>
                    <h2 className="mt-3 font-display text-3xl font-extrabold text-counsly-ink tracking-tight leading-tight">{cleanCollegeName(selectedCollege.name)}</h2>
                    <p className="mt-1 text-sm font-bold text-counsly-muted uppercase tracking-wider">
                      {selectedCollege.district} • {selectedCollege.type}
                    </p>
                    {selectedCollege.address && (
                      <p className="mt-4 rounded-2xl border border-counsly-line bg-counsly-soft/50 p-4 text-xs leading-relaxed text-counsly-muted italic shadow-inner">
                        {selectedCollege.address}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-3 sm:justify-end shrink-0">
                    <a className="button-primary inline-flex items-center gap-2 px-5 py-3 shadow-lg hover:shadow-xl transition-all duration-300" href={buildUserDirectionsUrl(selectedCollege)} rel="noopener noreferrer" target="_blank">
                      <Navigation className="h-4.5 w-4.5" />
                      Navigate to college
                    </a>
                    {selectedCollege.website && (
                      <a
                        className="button-secondary inline-flex items-center gap-2 px-5 py-3 shadow-sm hover:shadow-md transition-all duration-300"
                        href={selectedCollege.website.startsWith("http") ? selectedCollege.website : `https://${selectedCollege.website}`}
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        <Globe className="h-4.5 w-4.5 text-counsly-teal" />
                        Official website
                      </a>
                    )}
                  </div>
                </div>

                <div className="border-t border-counsly-line pt-6">
                  <h3 className="font-display text-lg font-bold text-counsly-ink tracking-tight mb-4 flex items-center gap-2">
                    <Layers className="w-5 h-5 text-counsly-coral" />
                    Nearby Public Transit Hubs
                  </h3>
                  <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-3">
                    {selectedTransitPoints.length > 0 ? (
                      selectedTransitPoints.map((point) => <TransitPointCard college={selectedCollege} key={point.id} point={point} />)
                    ) : (
                      <div className="rounded-2xl border border-counsly-line bg-counsly-soft p-8 text-center text-sm font-medium text-counsly-muted sm:col-span-2 xl:col-span-2 2xl:col-span-3">
                        Public transport coordinates and station listings are not available for this college.
                      </div>
                    )}
                  </div>
                </div>
              </Surface>
            ) : (
              <Surface className="p-16 text-center border border-counsly-line shadow-sm rounded-3xl" tone="paper">
                <Compass className="w-10 h-10 text-counsly-muted mx-auto mb-3 animate-[spin_10s_linear_infinite]" />
                <p className="text-sm font-semibold text-counsly-muted max-w-sm mx-auto">
                  Select a college from the left-hand directory to display travel routes, dynamic railway markers, and coordinate navigators.
                </p>
              </Surface>
            )}
          </div>
        </div>
      )}

      {activeTab === "tfc" && (
        <div className="space-y-4">
          <div className="relative max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-counsly-muted" />
            <input
              className="field bg-white pl-9"
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search TFC centres by name or district..."
              value={searchQuery}
            />
          </div>

          {loading ? (
            <div className="flex items-center justify-center gap-2 rounded-2xl border border-counsly-line bg-counsly-soft p-12 text-center text-sm text-counsly-muted">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-counsly-coral border-t-transparent" />
              Loading facilitation centres...
            </div>
          ) : filteredTfcs.length === 0 ? (
            <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-8 text-center text-sm text-counsly-muted">No TFC centres match your search.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredTfcs.map((tfc) => (
                <Surface className="flex flex-col justify-between p-5" key={tfc.centre_name} tone="paper">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <Badge tone="neutral">{tfc.district}</Badge>
                      <Compass className="h-4 w-4 text-counsly-coral" />
                    </div>
                    <h3 className="font-display text-xl text-counsly-ink">{tfc.centre_name}</h3>
                    <p className="text-xs leading-relaxed text-counsly-body">{tfc.address}</p>
                    {tfc.phone && (
                      <p className="flex items-center gap-1 text-xs text-counsly-muted">
                        <Phone className="h-3.5 w-3.5" />
                        <span>{tfc.phone}</span>
                      </p>
                    )}
                  </div>

                  <div className="mt-4 flex items-center justify-between gap-3 border-t border-counsly-line pt-3">
                    {tfc.latitude && tfc.longitude ? (
                      <span className="font-mono text-[10px] text-counsly-muted">
                        {tfc.latitude.toFixed(4)}, {tfc.longitude.toFixed(4)}
                      </span>
                    ) : (
                      <span className="text-[10px] text-counsly-muted">Coords pending</span>
                    )}
                    <a
                      className="inline-flex items-center gap-1 text-xs font-bold text-counsly-coral underline hover:text-counsly-ink"
                      href={tfc.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${tfc.centre_name}, ${tfc.district}`)}`}
                      rel="noopener noreferrer"
                      target="_blank"
                    >
                      Navigate <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </Surface>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function MapsPage() {
  return (
    <FeatureGate>
      <MapsContent />
    </FeatureGate>
  );
}
