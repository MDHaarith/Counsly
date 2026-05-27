"use client";

import { useCallback, useEffect, useState, useMemo, useRef } from "react";
import {
  AlertCircle,
  Globe,
  MapPin,
  Navigation,
  Search,
  TrainFront,
  ExternalLink,
  Compass,
  Building2,
  Phone,
} from "lucide-react";
import Script from "next/script";

import { Badge, PageHeader, Surface } from "@/components/ui";
import { fetchMapColleges, fetchTfcLocations } from "@/lib/api.mjs";
import { cleanCollegeName } from "@/lib/product";

type TabId = "colleges" | "tfc";
type MapViewMode = "map" | "route";

const TABS: { id: TabId; label: string }[] = [
  { id: "colleges", label: "College Directory & Live Map" },
  { id: "tfc", label: "TFC Centres" },
];

type LocationRow = {
  code: string;
  name: string;
  district: string;
  type: string;
  latitude?: number;
  longitude?: number;
  hostel_available?: boolean;
  boys_hostel_available?: boolean;
  girls_hostel_available?: boolean;
  transport_available?: boolean;
  website?: string;
  nearest_railway_station?: string | null;
  nearest_railway_station_latitude?: number | null;
  nearest_railway_station_longitude?: number | null;
  nearest_railway_distance_km?: number | null;
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

function TravelRouteSVG({
  collegeName,
  railwayName,
  distanceKm,
}: {
  collegeName: string;
  railwayName: string;
  distanceKm: number;
}) {
  return (
    <div className="relative rounded-2xl border border-counsly-line bg-counsly-soft p-6 overflow-hidden flex flex-col items-center justify-center min-h-[320px] shadow-inner animate-fade-in">      
      <svg className="w-full max-w-sm h-36 mt-4" viewBox="0 0 400 150" fill="none" xmlns="http://www.w3.org/2000/svg">
        <style>{`
          @keyframes dash {
            to {
              stroke-dashoffset: -100;
            }
          }
          @keyframes pulse-pin {
            0% { r: 6; opacity: 1; }
            50% { r: 12; opacity: 0.4; }
            100% { r: 6; opacity: 0; }
          }
        `}</style>
        
        <path
          d="M 60,75 C 160,20 240,130 340,75"
          stroke="#1d4ed8"
          strokeWidth="4"
          strokeLinecap="round"
        />
        
        <g className="cursor-pointer">
          <circle cx="60" cy="75" r="10" fill="#e06a4e" className="animate-[pulse-pin_2s_infinite]" />
          <circle cx="60" cy="75" r="6" fill="#e06a4e" />
          <text x="60" y="105" textAnchor="middle" className="text-[10px] font-extrabold fill-counsly-ink font-sans">
            College
          </text>
        </g>
        
        <g className="cursor-pointer">
          <circle cx="340" cy="75" r="10" fill="#4fa59d" className="animate-[pulse-pin_2.5s_infinite]" />
          <circle cx="340" cy="75" r="6" fill="#4fa59d" />
          <text x="340" y="105" textAnchor="middle" className="text-[10px] font-extrabold fill-counsly-ink font-sans">
            Railway Station
          </text>
        </g>
      </svg>
      
      <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
        <div className="flex items-center gap-2 bg-white px-4 py-1.5 rounded-full shadow border border-counsly-line text-xs font-semibold text-counsly-body">
          <Building2 className="w-3.5 h-3.5 text-counsly-coral" />
          <span className="truncate max-w-[120px]">{cleanCollegeName(collegeName)}</span>
        </div>
        <div className="h-4 w-px bg-counsly-line hidden sm:block" />
        <div className="flex items-center gap-2 bg-white px-4 py-1.5 rounded-full shadow border border-counsly-line text-xs font-semibold text-counsly-body">
          <TrainFront className="w-3.5 h-3.5 text-counsly-teal" />
          <span className="truncate max-w-[120px]">{railwayName}</span>
        </div>
        <div className="h-4 w-px bg-counsly-line hidden sm:block" />
        <div className="flex items-center gap-2 bg-counsly-coral/10 px-4 py-1.5 rounded-full border border-counsly-coral/20 text-xs font-bold text-counsly-ink">
          <span>Route:</span>
          <span className="font-mono">{distanceKm ? `${distanceKm.toFixed(1)} km` : "Pending km"}</span>
        </div>
      </div>
    </div>
  );
}

export default function MapsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("colleges");
  const [viewMode, setViewMode] = useState<MapViewMode>("map");
  const [collegeRows, setCollegeRows] = useState<LocationRow[]>([]);
  const [tfcRows, setTfcRows] = useState<TfcLocationRow[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCollegeCode, setSelectedCollegeCode] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Leaflet Dynamic Loading states
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapInstance, setMapInstance] = useState<any>(null);
  const markersRef = useRef<any[]>([]);
  const routePolylineRef = useRef<any>(null);
  const stationMarkersRef = useRef<any[]>([]);
  const [routingStatus, setRoutingStatus] = useState("");
  // Check if Leaflet global L is already defined on mount or poll until it is
  useEffect(() => {
    if (typeof window !== "undefined") {
      if ((window as any).L) {
        setMapLoaded(true);
        return;
      }

      const interval = setInterval(() => {
        if ((window as any).L) {
          setMapLoaded(true);
          clearInterval(interval);
        }
      }, 100);

      return () => clearInterval(interval);
    }
  }, []);

  // Fetch college and TFC locations
  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchMapColleges({ limit: "500" }).catch(() => []),
      fetchTfcLocations({ limit: "500" }).catch(() => []),
    ])
      .then(([clgs, tfcs]) => {
        const sortedColleges = Array.isArray(clgs) ? clgs : [];
        setCollegeRows(sortedColleges);
        setTfcRows(Array.isArray(tfcs) ? tfcs : []);
        
        if (sortedColleges.length > 0) {
          setSelectedCollegeCode(sortedColleges[0].code);
        }
        setLoading(false);
      })
      .catch(() => {
        setError("Could not load maps data from workspace API.");
        setLoading(false);
      });
  }, []);

  // Filtered College List
  const filteredColleges = useMemo(() => {
    if (!searchQuery) return collegeRows;
    const lowerQuery = searchQuery.toLowerCase();
    return collegeRows.filter(
      (c) =>
        c.name.toLowerCase().includes(lowerQuery) ||
        c.code.includes(lowerQuery) ||
        c.district.toLowerCase().includes(lowerQuery)
    );
  }, [collegeRows, searchQuery]);

  // Filtered TFC List
  const filteredTfcs = useMemo(() => {
    if (!searchQuery) return tfcRows;
    const lowerQuery = searchQuery.toLowerCase();
    return tfcRows.filter(
      (t) =>
        t.centre_name.toLowerCase().includes(lowerQuery) ||
        t.district.toLowerCase().includes(lowerQuery) ||
        t.address.toLowerCase().includes(lowerQuery)
    );
  }, [tfcRows, searchQuery]);

  // Currently Selected College details
  const selectedCollege = useMemo(() => {
    return collegeRows.find((c) => c.code === selectedCollegeCode) || null;
  }, [collegeRows, selectedCollegeCode]);

  // Initialize Leaflet Map with OpenStreetMap tiles (always mounted for both map and routing)
  useEffect(() => {
    if (!mapLoaded || typeof window === "undefined" || activeTab !== "colleges") return;
    const L = (window as any).L;
    if (!L) return;

    // Fix default marker icon 404 issue in Leaflet Next.js loading
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });

    const mapContainer = document.getElementById("leaflet-map-canvas");
    if (!mapContainer) return;

    // Initialize Leaflet Map centered on Tamil Nadu without copyright/attribution controls
    const map = L.map("leaflet-map-canvas", { attributionControl: false }).setView([11.1271, 78.6569], 7);

    // Add OpenStreetMap Tile Layer
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19
    }).addTo(map);

    setMapInstance(map);

    return () => {
      map.remove();
      setMapInstance(null);
    };
  }, [mapLoaded, activeTab]);

  // Plot and update pins on the Leaflet OpenStreetMap dynamically
  useEffect(() => {
    if (!mapInstance || typeof window === "undefined") return;
    const L = (window as any).L;
    if (!L) return;

    // Clear old markers
    markersRef.current.forEach((m) => mapInstance.removeLayer(m));
    markersRef.current = [];

    if (viewMode !== "map") return; // Skip showing all pins when focusing on a specific station route

    // Plot pins for each filtered college
    const nextMarkers = filteredColleges
      .map((c) => {
        if (c.latitude == null || c.longitude == null) return null;
        
        const isSelected = selectedCollegeCode === c.code;

        // Custom divIcon styled with inline styles to be completely immune to Tailwind class purging
        const icon = L.divIcon({
          className: "custom-leaflet-icon",
          html: `<div class="rounded-full cursor-pointer transition-all duration-300 flex items-center justify-center" style="
            position: relative;
            border: 1px solid white;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            width: ${isSelected ? '20px' : '12px'};
            height: ${isSelected ? '20px' : '12px'};
            background-color: ${isSelected ? '#cc785c' : '#4fa59d'};
            z-index: ${isSelected ? '1000' : '10'};
            transform: ${isSelected ? 'scale(1.2)' : 'scale(1)'};
          ">
            ${isSelected ? '<span class="animate-ping" style="position: absolute; inset: 0; border-radius: 9999px; background-color: #cc785c; opacity: 0.75;"></span>' : ''}
            <div style="width: ${isSelected ? '6px' : '4px'}; height: ${isSelected ? '6px' : '4px'}; background-color: white; border-radius: 9999px;"></div>
          </div>`,
          iconSize: isSelected ? [24, 24] : [12, 12],
          iconAnchor: isSelected ? [12, 12] : [6, 6]
        });

        const marker = L.marker([c.latitude, c.longitude], { icon })
          .addTo(mapInstance)
          .on("click", () => {
            setSelectedCollegeCode(c.code);
          });

        return marker;
      })
      .filter(Boolean);

    markersRef.current = nextMarkers;

    // Pan to centered view if selected college changes
    if (selectedCollege && selectedCollege.latitude != null && selectedCollege.longitude != null) {
      mapInstance.setView([selectedCollege.latitude, selectedCollege.longitude], 10, {
        animate: true,
        duration: 1.0,
      });
    }
  }, [mapInstance, filteredColleges, selectedCollegeCode, selectedCollege]);
  // Highly Accurate Geolocation Trigger: plots high-precision user coordinates on the Leaflet OSM
  const handleFindMyLocation = () => {
    if (!mapInstance || typeof window === "undefined") return;
    const L = (window as any).L;
    if (!L) return;

    setError("");
    setRoutingStatus("Acquiring high-accuracy GPS coordinates...");

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          const accuracy = position.coords.accuracy;

          // Strict boundary check: User must be in Tamil Nadu to avoid VPN or fake location issues
          const inTN = (8.0 <= lat && lat <= 14.0 && 75.0 <= lng && lng <= 81.0);
          if (!inTN) {
            setError(`Location acquired (${lat.toFixed(4)}, ${lng.toFixed(4)}) is outside Tamil Nadu bounds.`);
            return;
          }

          // Smoothly pan and zoom map to user's location
          mapInstance.setView([lat, lng], 15, {
            animate: true,
            duration: 1.5,
          });

          // Plot a pulsing Blue Pin representing the user
          const userIcon = L.divIcon({
            className: "custom-user-location-pin",
            html: `<div class="rounded-full cursor-pointer flex items-center justify-center border-2 border-white shadow-xl" style="
              position: relative;
              width: 24px;
              height: 24px;
              background-color: #1d4ed8;
            ">
              <span class="animate-ping" style="position: absolute; inset: 0; border-radius: 9999px; background-color: #1d4ed8; opacity: 0.75;"></span>
              <div style="width: 8px; height: 8px; background-color: white; border-radius: 9999px;"></div>
            </div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });

          const marker = L.marker([lat, lng], { icon: userIcon })
            .addTo(mapInstance)
            .bindPopup(`<strong>Accurate Location Pin</strong><br/>Precision: ±${accuracy.toFixed(0)} meters.<br/>Coordinates: ${lat.toFixed(5)}, ${lng.toFixed(5)}`)
            .openPopup();
            
          markersRef.current.push(marker);
        },
        (err) => {
          console.error("Geolocation Error:", err);
          setError("Failed to acquire high-accuracy location. Please enable GPS and allow location access.");
        },
        options
      );
    } else {
      setError("Geolocation is not supported by this browser.");
    }
  };


  // Live Railway Station Geocoding & OSRM Routing Effect
  useEffect(() => {
    if (!mapInstance || typeof window === "undefined") return;
    const L = (window as any).L;
    if (!L) return;

    // Clear old route polyline
    if (routePolylineRef.current) {
      mapInstance.removeLayer(routePolylineRef.current);
      routePolylineRef.current = null;
    }
    // Clear old station markers
    stationMarkersRef.current.forEach((m) => mapInstance.removeLayer(m));
    stationMarkersRef.current = [];

    if (viewMode !== "route" || !selectedCollege) {
      setRoutingStatus("");
      return;
    }

    const collegeLat = selectedCollege.latitude;
    const collegeLng = selectedCollege.longitude;
    const stationName = selectedCollege.nearest_railway_station;

    if (collegeLat == null || collegeLng == null || !stationName) {
      setRoutingStatus("No coordinates or nearest station details available for this college.");
      return;
    }

    const startRouting = (stationLat: number, stationLng: number) => {
      setRoutingStatus("Generating exact route directions via OSRM...");
      const routeUrl = `https://router.project-osrm.org/route/v1/driving/${collegeLng},${collegeLat};${stationLng},${stationLat}?overview=full&geometries=geojson`;

      fetch(routeUrl)
        .then((res) => res.json())
        .then((routeData) => {
          let coords = [
            [collegeLat, collegeLng],
            [stationLat, stationLng]
          ];

          if (routeData && routeData.routes && routeData.routes.length > 0) {
            const routeCoords = routeData.routes[0].geometry.coordinates;
            coords = routeCoords.map((coord: any) => [coord[1], coord[0]]);
            setRoutingStatus(`Exact station route generated: ${(routeData.routes[0].distance / 1000).toFixed(1)} km by road.`);
          } else {
            setRoutingStatus("Calculated direct railway line (OSRM routing busy).");
          }

          // Draw route polyline as Deep Blue and continuous
          const polyline = L.polyline(coords, {
            color: "#1d4ed8",
            weight: 5,
            opacity: 0.9,
          }).addTo(mapInstance);

          routePolylineRef.current = polyline;

          // Plot station pin
          const stationIcon = L.divIcon({
            className: "custom-station-icon",
            html: `<div class="rounded-full cursor-pointer flex items-center justify-center border-2 border-white shadow-lg" style="
              width: 24px;
              height: 24px;
              background-color: #4fa59d;
              position: relative;
            ">
              <span class="animate-ping" style="position: absolute; inset: 0; border-radius: 9999px; background-color: #4fa59d; opacity: 0.75;"></span>
              <div style="width: 8px; height: 8px; background-color: white; border-radius: 9999px;"></div>
            </div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });

          const stationMarker = L.marker([stationLat, stationLng], { icon: stationIcon })
            .addTo(mapInstance)
            .bindPopup(`<strong>${stationName} Railway Station</strong><br/>Nearest transport link.`)
            .openPopup();

          stationMarkersRef.current.push(stationMarker);

          // Plot college pin
          const collegeIcon = L.divIcon({
            className: "custom-college-route-icon",
            html: `<div class="rounded-full cursor-pointer flex items-center justify-center border border-white shadow-md" style="
              width: 20px;
              height: 20px;
              background-color: #cc785c;
              position: relative;
            ">
              <span class="animate-ping" style="position: absolute; inset: 0; border-radius: 9999px; background-color: #cc785c; opacity: 0.75;"></span>
              <div style="width: 6px; height: 6px; background-color: white; border-radius: 9999px;"></div>
            </div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          });

          const collegeMarker = L.marker([collegeLat, collegeLng], { icon: collegeIcon })
            .addTo(mapInstance)
            .bindPopup(`<strong>${cleanCollegeName(selectedCollege.name)}</strong><br/>College campus.`);

          stationMarkersRef.current.push(collegeMarker);

          // Auto fit bounds to show both college and station
          const bounds = L.latLngBounds([
            [collegeLat, collegeLng],
            [stationLat, stationLng]
          ]);
          mapInstance.fitBounds(bounds, { padding: [50, 50] });
        })
        .catch((err) => {
          console.error("OSRM Routing error:", err);
          setRoutingStatus("Route generated using direct line approximation.");

          // Draw direct line fallback as Deep Blue and continuous
          const polyline = L.polyline([[collegeLat, collegeLng], [stationLat, stationLng]], {
            color: "#1d4ed8",
            weight: 4,
            opacity: 0.8,
          }).addTo(mapInstance);
          routePolylineRef.current = polyline;
        });
    };

    // If coordinates are pre-geocoded in database, bypass Nominatim completely!
    if (selectedCollege.nearest_railway_station_latitude != null && selectedCollege.nearest_railway_station_longitude != null) {
      console.log("Using pre-geocoded station coordinates from database:", selectedCollege.nearest_railway_station_latitude, selectedCollege.nearest_railway_station_longitude);
      startRouting(selectedCollege.nearest_railway_station_latitude, selectedCollege.nearest_railway_station_longitude);
    } else {
      setRoutingStatus(`Geocoding nearest station: ${stationName}...`);
      // 1. Geocode the station using Nominatim
      const geocodeUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(stationName + " Railway Station, Tamil Nadu")}&format=json&limit=1`;

      fetch(geocodeUrl)
        .then((res) => res.json())
        .then((results) => {
          let stationLat = collegeLat + 0.02; // fallback offset
          let stationLng = collegeLng + 0.02;

          if (Array.isArray(results) && results.length > 0) {
            stationLat = parseFloat(results[0].lat);
            stationLng = parseFloat(results[0].lon);
          }
          startRouting(stationLat, stationLng);
        })
        .catch((err) => {
          console.error("Nominatim Geocoding Error:", err);
          setRoutingStatus("Route generated using direct line approximation.");

          // Draw direct line fallback
          const stationLat = collegeLat + 0.02;
          const stationLng = collegeLng + 0.02;
          const polyline = L.polyline([[collegeLat, collegeLng], [stationLat, stationLng]], {
            color: "#1d4ed8",
            weight: 4,
            opacity: 0.8,
          }).addTo(mapInstance);
          routePolylineRef.current = polyline;
        });
    }
  }, [mapInstance, selectedCollege, viewMode]);

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        description="Search TNEA colleges, plot real-time positions on OpenStreetMap via Leaflet, retrieve user geolocation, and check travel routes."
        eyebrow="Geographic Routing"
        title="OpenStreetMap Live TN Hub"
      />

      {/* Tabs */}
      <Surface className="p-3" tone="soft">
        <nav className="flex flex-wrap gap-1">
          {TABS.map((tab) => (
            <button
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition-colors ${
                activeTab === tab.id
                  ? "bg-counsly-ink text-counsly-canvas"
                  : "text-counsly-body hover:bg-counsly-card"
              }`}
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setSearchQuery("");
              }}
            >
              <Compass className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </Surface>

      {loading && (
        <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">
          Fetching geographic maps data...
        </p>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-counsly-line bg-counsly-soft px-4 py-3 text-sm text-counsly-coral animate-slide-up">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {activeTab === "colleges" && (
            <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
              {/* Left Panel: College Directory */}
              <div className="space-y-4">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-counsly-muted" />
                  <input
                    className="field pl-9 bg-white"
                    placeholder="Search college name or code..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>

                <Surface className="max-h-[640px] overflow-y-auto divide-y divide-counsly-line" tone="paper">
                  {filteredColleges.length === 0 ? (
                    <p className="p-6 text-center text-sm text-counsly-muted">
                      No colleges match your search parameters.
                    </p>
                  ) : (
                    filteredColleges.map((c) => (
                      <button
                        key={c.code}
                        onClick={() => {
                          setSelectedCollegeCode(c.code);
                        }}
                        className={`w-full text-left p-4 hover:bg-counsly-soft transition-all flex items-start gap-3 ${
                          selectedCollegeCode === c.code ? "bg-counsly-soft ring-2 ring-inset ring-counsly-coral/40" : ""
                        }`}
                      >
                        <MapPin className={`w-4 h-4 mt-1 shrink-0 ${selectedCollegeCode === c.code ? "text-counsly-coral" : "text-counsly-muted"}`} />
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-counsly-canvas border border-counsly-line text-counsly-ink">{c.code}</span>
                            <span className="text-xs text-counsly-muted">{c.district}</span>
                          </div>
                          <h3 className="mt-1 font-bold text-sm text-counsly-ink truncate">
                            {cleanCollegeName(c.name)}
                          </h3>
                        </div>
                      </button>
                    ))
                  )}
                </Surface>
              </div>

              {/* Right Panel: Interactive TN Map or Station routing */}
              <div className="space-y-4">
                {/* Visual View-Mode Selector */}
                <div className="flex items-center gap-2 bg-counsly-soft p-1.5 rounded-xl border border-counsly-line w-fit">
                  <button
                    onClick={() => setViewMode("map")}
                    className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      viewMode === "map" ? "bg-white text-counsly-ink shadow-sm" : "text-counsly-muted hover:text-counsly-ink"
                    }`}
                  >
                    <Compass className="w-3.5 h-3.5 text-counsly-coral" />
                    OpenStreetMap Live Map
                  </button>
                  <button
                    onClick={() => setViewMode("route")}
                    className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      viewMode === "route" ? "bg-white text-counsly-ink shadow-sm" : "text-counsly-muted hover:text-counsly-ink"
                    }`}
                  >
                    <TrainFront className="w-3.5 h-3.5 text-counsly-teal" />
                    Detailed Station Route Path
                  </button>
                </div>

                <div className="relative w-full h-[520px] rounded-2xl border border-counsly-line overflow-hidden shadow-inner bg-counsly-soft animate-fade-in">
                  {/* Leaflet Map Canvas */}
                  <div id="leaflet-map-canvas" className="w-full h-full z-10" />

                  {/* Floating High-Accuracy GPS Geolocation Button */}
                  {viewMode === "map" && (
                    <button
                      onClick={handleFindMyLocation}
                      className="absolute bottom-4 left-4 bg-white hover:bg-counsly-soft px-3 py-2 rounded-xl border border-counsly-line text-counsly-ink shadow-lg flex items-center gap-1.5 z-[1000] text-xs font-bold transition-all animate-fade-in"
                      title="Acquire exact GPS location"
                      type="button"
                    >
                      <Compass className="w-4 h-4 text-counsly-coral animate-pulse" />
                      Locate Me (High-Accuracy GPS)
                    </button>
                  )}
                </div>



                {selectedCollege ? (
                  <Surface className="p-6 space-y-6 animate-fade-in" tone="paper">
                    <div>
                      <Badge tone="coral">{selectedCollege.code}</Badge>
                      <h2 className="mt-2 font-display text-3xl text-counsly-ink">
                        {cleanCollegeName(selectedCollege.name)}
                      </h2>
                      <p className="mt-1 text-sm text-counsly-body">
                        {selectedCollege.district} • {selectedCollege.type}
                      </p>
                      {selectedCollege.address && (
                        <p className="mt-2 text-xs text-counsly-muted bg-counsly-soft p-3 rounded-lg border border-counsly-line italic">
                          {selectedCollege.address}
                        </p>
                      )}
                    </div>

                    {/* Routing & Facilities Details Grid */}
                    <div className="grid gap-4 md:grid-cols-2 w-full animate-fade-in">
                      {/* Railway Station Card */}
                      <div className="border border-counsly-line rounded-xl p-4 space-y-2">
                        <div className="flex items-center gap-2">
                          <TrainFront className="w-4 h-4 text-counsly-coral" />
                          <h4 className="font-bold text-sm text-counsly-ink">Nearest Railway Station</h4>
                        </div>
                        <p className="text-sm font-semibold text-counsly-body">
                          {selectedCollege.nearest_railway_station || "Context pending"} 
                          {selectedCollege.nearest_railway_distance_km != null && ` (${selectedCollege.nearest_railway_distance_km.toFixed(1)} km away)`}
                        </p>
                        {selectedCollege.nearest_railway_station && (
                          <a
                            href={selectedCollege.nearest_railway_station_latitude && selectedCollege.nearest_railway_station_longitude
                              ? `https://www.google.com/maps/search/?api=1&query=${selectedCollege.nearest_railway_station_latitude},${selectedCollege.nearest_railway_station_longitude}`
                              : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selectedCollege.nearest_railway_station + " Railway Station, Tamil Nadu")}`
                            }
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-bold text-counsly-coral underline hover:text-counsly-ink inline-flex items-center gap-1 mt-1"
                          >
                            Find Station on Google Maps <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>


                    </div>

                    {/* Navigation CTA Buttons */}
                    <div className="flex flex-wrap gap-3 pt-3 border-t border-counsly-line">
                      {selectedCollege.latitude && selectedCollege.longitude ? (
                        <a
                          href={`https://www.google.com/maps/dir/?api=1&destination=${selectedCollege.latitude},${selectedCollege.longitude}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="button-primary inline-flex items-center gap-2"
                        >
                          <Navigation className="w-4 h-4" />
                          Launch Route Navigation
                        </a>
                      ) : (
                        <a
                          href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selectedCollege.name)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="button-primary inline-flex items-center gap-2"
                        >
                          <Compass className="w-4 h-4" />
                          Search on Google Maps
                        </a>
                      )}

                      {selectedCollege.website && (
                        <a
                          href={selectedCollege.website.startsWith("http") ? selectedCollege.website : `https://${selectedCollege.website}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="button-secondary inline-flex items-center gap-2"
                        >
                          <Globe className="w-4 h-4" />
                          Official Website
                        </a>
                      )}
                    </div>
                  </Surface>
                ) : (
                  <Surface className="p-12 text-center text-counsly-muted" tone="paper">
                    Select a college from the left-hand directory to display travel routes and dynamic navigation links.
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
                  className="field pl-9 bg-white"
                  placeholder="Search TFC centers by name or district..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {filteredTfcs.length === 0 ? (
                <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-8 text-center text-sm text-counsly-muted">
                  No TFC centers match your search parameters.
                </p>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {filteredTfcs.map((tfc) => (
                    <Surface className="p-5 flex flex-col justify-between" key={tfc.centre_name} tone="paper">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <Badge tone="neutral">{tfc.district}</Badge>
                          <Compass className="w-4 h-4 text-counsly-coral" />
                        </div>
                        <h3 className="font-display text-xl text-counsly-ink">{tfc.centre_name}</h3>
                        <p className="text-xs text-counsly-body leading-relaxed">{tfc.address}</p>
                        {tfc.phone && (
                          <p className="text-xs text-counsly-muted flex items-center gap-1">
                            <Phone className="w-3.5 h-3.5" />
                            <span>{tfc.phone}</span>
                          </p>
                        )}
                      </div>

                      <div className="mt-4 pt-3 border-t border-counsly-line flex items-center justify-between">
                        {tfc.latitude && tfc.longitude ? (
                          <span className="font-mono text-[10px] text-counsly-muted">
                            Coords: {tfc.latitude.toFixed(4)}, {tfc.longitude.toFixed(4)}
                          </span>
                        ) : (
                          <span className="text-[10px] text-counsly-muted">Coords pending</span>
                        )}

                        <a
                          href={tfc.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(tfc.centre_name + ", " + tfc.district)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-bold text-counsly-coral underline hover:text-counsly-ink inline-flex items-center gap-1"
                        >
                          Navigate <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </Surface>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
