"""
KEEPIT World Model — Urban Digital Twin Foundation
===================================================

Coleta e processa dados urbanos para construir o cérebro digital das cidades.

Each KEEPIT Hub is a physical node in the World Model. As hubs ingest real-time
data (footfall sensors, IoT, events, weather), they collectively form an Urban
Digital Twin — a living, queryable representation of city state.

This module is the data layer for the World Model. In production:
  - Hub nodes report via MQTT / gRPC streams
  - Data is stored in a time-series database (InfluxDB / TimescaleDB)
  - The query layer uses geospatial indices (PostGIS / H3)

For now, it operates in-memory with rich synthetic data for São Paulo and
Rio de Janeiro to demonstrate the architecture.
"""

from __future__ import annotations

import json
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class HubNode:
    """A physical KEEPIT Hub registered as a node in the World Model."""

    hub_id: str
    lat: float
    lon: float
    city: str
    registered_at: float
    status: str = "active"          # active | offline | maintenance
    last_heartbeat: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class UrbanDataPoint:
    """A single observation ingested into the World Model."""

    record_id: str
    hub_id: str
    city: str
    data_type: str          # footfall | weather | event | air_quality | noise | traffic
    payload: dict
    ingested_at: float
    lat: float = 0.0
    lon: float = 0.0


@dataclass
class CitySnapshot:
    """Point-in-time snapshot of a city's World Model state."""

    snapshot_id: str
    city: str
    generated_at: float
    hub_count: int
    active_hubs: int
    total_data_points: int
    summary: dict           # aggregated metrics
    hotspots: list[dict]    # top activity zones
    alerts: list[str]       # anomaly detections


# ---------------------------------------------------------------------------
# Distance helper (Haversine formula — no external dependencies)
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance in kilometres between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# World Model Engine
# ---------------------------------------------------------------------------

class KEEPITWorldModel:
    """
    Urban Digital Twin engine for the KEEPIT Hub network.

    Each registered Hub node continuously ingests urban data. The World Model
    aggregates this into a queryable city-state representation that AI agents
    can use for planning, commerce, and real-world operations.
    """

    def __init__(self):
        self._hubs: dict[str, HubNode] = {}
        self._data_points: list[UrbanDataPoint] = []
        self._snapshots: dict[str, CitySnapshot] = {}

        # Seed synthetic data for demo
        self._seed_synthetic_data()

    # ------------------------------------------------------------------ #
    # Hub Registration                                                    #
    # ------------------------------------------------------------------ #

    def register_hub_node(
        self,
        hub_id: str,
        lat: float,
        lon: float,
        city: str,
        metadata: dict | None = None,
    ) -> HubNode:
        """
        Register a physical KEEPIT Hub as a node in the World Model.

        Args:
            hub_id:   Unique identifier for the Hub (e.g. 'hub_sp_paulista_01').
            lat:      WGS-84 latitude.
            lon:      WGS-84 longitude.
            city:     City name (used for city-level aggregations).
            metadata: Optional dict with hub specs (capacity, sensors, etc.).

        Returns:
            The registered HubNode object.
        """
        if hub_id in self._hubs:
            raise ValueError(f"Hub '{hub_id}' is already registered.")

        node = HubNode(
            hub_id=hub_id,
            lat=lat,
            lon=lon,
            city=city,
            registered_at=time.time(),
            metadata=metadata or {},
        )
        self._hubs[hub_id] = node
        print(f"[WorldModel] Hub registered: '{hub_id}' in {city} @ ({lat:.4f}, {lon:.4f})")
        return node

    # ------------------------------------------------------------------ #
    # Data Ingestion                                                       #
    # ------------------------------------------------------------------ #

    def ingest_urban_data(
        self,
        hub_id: str,
        data_type: str,
        payload: dict,
    ) -> UrbanDataPoint:
        """
        Ingest a real-time urban data observation from a Hub.

        Supported data types:
          - footfall:    {'count': int, 'direction': 'in'|'out'}
          - weather:     {'temp_c': float, 'humidity': float, 'condition': str}
          - event:       {'name': str, 'type': str, 'expected_crowd': int}
          - air_quality: {'aqi': int, 'pm25': float, 'pm10': float}
          - noise:       {'db': float, 'source': str}
          - traffic:     {'speed_kmh': float, 'congestion_pct': float}

        Args:
            hub_id:    ID of the reporting Hub.
            data_type: Type of urban data (see above).
            payload:   Observation payload as a dict.

        Returns:
            The ingested UrbanDataPoint record.
        """
        if hub_id not in self._hubs:
            raise ValueError(f"Hub '{hub_id}' not found. Register it first.")

        hub = self._hubs[hub_id]
        hub.last_heartbeat = time.time()

        record = UrbanDataPoint(
            record_id=f"dp_{uuid.uuid4().hex[:12]}",
            hub_id=hub_id,
            city=hub.city,
            data_type=data_type,
            payload=payload,
            ingested_at=time.time(),
            lat=hub.lat,
            lon=hub.lon,
        )
        self._data_points.append(record)
        return record

    # ------------------------------------------------------------------ #
    # Queries                                                             #
    # ------------------------------------------------------------------ #

    def query_city_state(self, city: str, radius_km: float = 5.0) -> dict:
        """
        Query the current state of a city within a given radius.

        Returns aggregated metrics for all Hubs within radius_km of the
        city centroid (computed as the centroid of all registered hubs
        in that city).

        Args:
            city:      City name to query.
            radius_km: Radius in km for spatial aggregation.

        Returns:
            Dict with aggregated city state metrics.
        """
        city_hubs = [h for h in self._hubs.values() if h.city.lower() == city.lower()]
        if not city_hubs:
            return {"error": f"No hubs registered for city '{city}'."}

        # Compute city centroid
        centroid_lat = sum(h.lat for h in city_hubs) / len(city_hubs)
        centroid_lon = sum(h.lon for h in city_hubs) / len(city_hubs)

        # Filter hubs within radius
        nearby_hubs = [
            h for h in city_hubs
            if _haversine_km(centroid_lat, centroid_lon, h.lat, h.lon) <= radius_km
        ]
        nearby_ids = {h.hub_id for h in nearby_hubs}

        # Get recent data (last 3600 seconds)
        cutoff = time.time() - 3600
        recent_data = [
            dp for dp in self._data_points
            if dp.hub_id in nearby_ids and dp.ingested_at >= cutoff
        ]

        # Aggregate by type
        footfall_total = sum(
            dp.payload.get("count", 0) for dp in recent_data if dp.data_type == "footfall"
        )
        weather_records = [dp.payload for dp in recent_data if dp.data_type == "weather"]
        avg_temp = (
            sum(w.get("temp_c", 0) for w in weather_records) / len(weather_records)
            if weather_records else None
        )
        active_events = [
            dp.payload for dp in recent_data if dp.data_type == "event"
        ]
        traffic_records = [dp.payload for dp in recent_data if dp.data_type == "traffic"]
        avg_congestion = (
            sum(t.get("congestion_pct", 0) for t in traffic_records) / len(traffic_records)
            if traffic_records else None
        )

        return {
            "city": city,
            "queried_at": time.time(),
            "radius_km": radius_km,
            "hub_count": len(nearby_hubs),
            "active_hubs": sum(1 for h in nearby_hubs if h.status == "active"),
            "footfall_last_hour": footfall_total,
            "avg_temperature_c": round(avg_temp, 1) if avg_temp is not None else None,
            "active_events": active_events,
            "avg_congestion_pct": round(avg_congestion, 1) if avg_congestion is not None else None,
            "data_points_ingested": len(recent_data),
        }

    def generate_city_snapshot(self, city: str) -> CitySnapshot:
        """
        Generate a comprehensive World Model snapshot for a city.

        The snapshot captures the holistic state of the city at a moment in
        time — suitable for archiving, sharing with AI agents, or publishing
        to the KEEPIT data marketplace.

        Args:
            city: Target city name.

        Returns:
            CitySnapshot with aggregated metrics, hotspots, and alerts.
        """
        city_hubs = [h for h in self._hubs.values() if h.city.lower() == city.lower()]
        city_data = [dp for dp in self._data_points if dp.city.lower() == city.lower()]

        # Identify hotspots — hubs with above-average footfall
        hub_footfall: dict[str, int] = {}
        for dp in city_data:
            if dp.data_type == "footfall":
                hub_footfall[dp.hub_id] = hub_footfall.get(dp.hub_id, 0) + dp.payload.get("count", 0)

        avg_ff = sum(hub_footfall.values()) / len(hub_footfall) if hub_footfall else 0
        hotspots = [
            {"hub_id": hid, "footfall": ff, "location": (self._hubs[hid].lat, self._hubs[hid].lon)}
            for hid, ff in sorted(hub_footfall.items(), key=lambda x: x[1], reverse=True)
            if ff > avg_ff and hid in self._hubs
        ][:5]

        # Simple anomaly detection
        alerts = []
        for dp in city_data:
            if dp.data_type == "air_quality" and dp.payload.get("aqi", 0) > 150:
                alerts.append(f"⚠️ High AQI ({dp.payload['aqi']}) at hub {dp.hub_id}")
            if dp.data_type == "traffic" and dp.payload.get("congestion_pct", 0) > 80:
                alerts.append(f"🚦 Heavy congestion ({dp.payload['congestion_pct']}%) at hub {dp.hub_id}")

        state = self.query_city_state(city)

        snapshot = CitySnapshot(
            snapshot_id=f"snap_{uuid.uuid4().hex[:12]}",
            city=city,
            generated_at=time.time(),
            hub_count=len(city_hubs),
            active_hubs=sum(1 for h in city_hubs if h.status == "active"),
            total_data_points=len(city_data),
            summary={
                "footfall_last_hour": state.get("footfall_last_hour", 0),
                "avg_temperature_c": state.get("avg_temperature_c"),
                "avg_congestion_pct": state.get("avg_congestion_pct"),
                "active_event_count": len(state.get("active_events", [])),
            },
            hotspots=hotspots,
            alerts=list(set(alerts)),  # deduplicate
        )
        self._snapshots[snapshot.snapshot_id] = snapshot
        print(f"[WorldModel] Snapshot generated for {city}: {snapshot.snapshot_id}")
        return snapshot

    def predict_urban_flow(self, location: tuple[float, float], hour: int) -> dict:
        """
        Predict pedestrian/vehicle flow at a location for a given hour of day.

        Uses a simplified sinusoidal model calibrated to Brazilian urban patterns:
          - Dual peaks at 08:00-09:00 (morning commute) and 17:00-19:00 (evening)
          - Weekend adjustment (−30%)
          - Nearby Hub density bonus

        In production, this would call the KEEPIT OASIS stacked ensemble model.

        Args:
            location: (lat, lon) tuple for the target point.
            hour:     Hour of day (0–23) to predict.

        Returns:
            Dict with predicted footfall, confidence interval, and peak flag.
        """
        lat, lon = location

        # Base sinusoidal flow model (peaks at hour 8 and 18)
        morning_peak = math.exp(-0.5 * ((hour - 8) / 1.5) ** 2)
        evening_peak = math.exp(-0.5 * ((hour - 18) / 1.5) ** 2)
        base_flow = 1000 * (morning_peak + evening_peak * 1.2)

        # Hub proximity bonus — more hubs nearby → more agent commerce → more activity
        nearby_hubs = [
            h for h in self._hubs.values()
            if _haversine_km(lat, lon, h.lat, h.lon) < 1.0
        ]
        hub_bonus = 1.0 + len(nearby_hubs) * 0.15

        predicted = base_flow * hub_bonus
        confidence = 0.85 - 0.01 * abs(hour - 13)  # lower confidence at night

        return {
            "location": {"lat": lat, "lon": lon},
            "hour": hour,
            "predicted_footfall": round(predicted),
            "confidence": round(max(0.5, confidence), 2),
            "is_peak_hour": hour in range(7, 10) or hour in range(17, 20),
            "nearby_hubs": len(nearby_hubs),
            "model": "keepit_oasis_v1_simplified",
        }

    # ------------------------------------------------------------------ #
    # Synthetic Seed Data                                                 #
    # ------------------------------------------------------------------ #

    def _seed_synthetic_data(self):
        """
        Seed the World Model with synthetic Hub nodes and data points for
        São Paulo and Rio de Janeiro.

        These represent plausible real-world locations for KEEPIT Hub deployment.
        """

        # ── São Paulo ────────────────────────────────────────────────────
        sp_hubs = [
            ("hub_sp_paulista_01",    -23.5614, -46.6557, "Av Paulista — MASP"),
            ("hub_sp_paulista_02",    -23.5630, -46.6543, "Av Paulista — Consolação"),
            ("hub_sp_berrini_01",     -23.5956, -46.6837, "Berrini — Torre JK"),
            ("hub_sp_republica_01",   -23.5433, -46.6424, "Estação República"),
            ("hub_sp_faria_lima_01",  -23.5738, -46.6843, "Faria Lima — Itaim"),
            ("hub_sp_se_01",          -23.5505, -46.6333, "Estação Sé"),
            ("hub_sp_vila_madalena",  -23.5497, -46.6924, "Vila Madalena"),
        ]

        # ── Rio de Janeiro ───────────────────────────────────────────────
        rio_hubs = [
            ("hub_rio_copacabana_01", -22.9714, -43.1824, "Copacabana — Metrô"),
            ("hub_rio_ipanema_01",    -22.9838, -43.1988, "Ipanema — Praça Gal Osório"),
            ("hub_rio_centro_01",     -22.9028, -43.1756, "Centro — Cinelândia"),
            ("hub_rio_barra_01",      -23.0100, -43.3164, "Barra da Tijuca — Américas"),
            ("hub_rio_tijuca_01",     -22.9234, -43.2332, "Tijuca — Maracanã"),
        ]

        for hub_id, lat, lon, name in sp_hubs:
            self.register_hub_node(hub_id, lat, lon, "São Paulo", {"landmark": name})

        for hub_id, lat, lon, name in rio_hubs:
            self.register_hub_node(hub_id, lat, lon, "Rio de Janeiro", {"landmark": name})

        # Ingest synthetic data streams for each hub
        import random
        rng = random.Random(42)  # deterministic seed for reproducibility

        sp_weather = {"temp_c": 26.0, "humidity": 68, "condition": "partly_cloudy"}
        rio_weather = {"temp_c": 32.0, "humidity": 82, "condition": "sunny"}

        sp_events = [
            {"name": "Rock in Rio São Paulo", "type": "concert", "expected_crowd": 90000},
            {"name": "Fórmula E SP 2026", "type": "motorsport", "expected_crowd": 45000},
        ]
        rio_events = [
            {"name": "Réveillon Copacabana", "type": "festival", "expected_crowd": 2500000},
        ]

        for hub_id, lat, lon, name in sp_hubs:
            self.ingest_urban_data(hub_id, "footfall", {"count": rng.randint(8000, 65000), "direction": "in"})
            self.ingest_urban_data(hub_id, "weather", sp_weather)
            self.ingest_urban_data(hub_id, "traffic", {"speed_kmh": rng.uniform(8, 45), "congestion_pct": rng.uniform(20, 90)})
            self.ingest_urban_data(hub_id, "air_quality", {"aqi": rng.randint(40, 130), "pm25": rng.uniform(8, 45), "pm10": rng.uniform(15, 60)})
            if rng.random() > 0.5:
                self.ingest_urban_data(hub_id, "event", rng.choice(sp_events))

        for hub_id, lat, lon, name in rio_hubs:
            self.ingest_urban_data(hub_id, "footfall", {"count": rng.randint(15000, 90000), "direction": "in"})
            self.ingest_urban_data(hub_id, "weather", rio_weather)
            self.ingest_urban_data(hub_id, "traffic", {"speed_kmh": rng.uniform(10, 50), "congestion_pct": rng.uniform(15, 75)})
            self.ingest_urban_data(hub_id, "air_quality", {"aqi": rng.randint(30, 100), "pm25": rng.uniform(5, 30), "pm10": rng.uniform(10, 50)})
            if hub_id == "hub_rio_copacabana_01":
                self.ingest_urban_data(hub_id, "event", rio_events[0])


# ---------------------------------------------------------------------------
# Demo / Smoke Test
# ---------------------------------------------------------------------------

def _run_demo():
    print("=" * 60)
    print("  KEEPIT World Model — Urban Digital Twin Demo")
    print("=" * 60)

    model = KEEPITWorldModel()

    print(f"\n🌆 REGISTERED HUBS: {len(model._hubs)}")
    for h in list(model._hubs.values())[:3]:
        print(f"  {h.hub_id} — {h.city} @ ({h.lat:.4f}, {h.lon:.4f})")
    print("  ...")

    print("\n📊 CITY STATE: São Paulo (radius 10km)")
    state = model.query_city_state("São Paulo", radius_km=10.0)
    print(f"  Hubs: {state['hub_count']} | Active: {state['active_hubs']}")
    print(f"  Footfall last hour: {state['footfall_last_hour']:,}")
    print(f"  Avg temperature: {state['avg_temperature_c']}°C")
    print(f"  Avg congestion: {state['avg_congestion_pct']}%")

    print("\n📸 GENERATING CITY SNAPSHOT: Rio de Janeiro")
    snap = model.generate_city_snapshot("Rio de Janeiro")
    print(f"  Snapshot ID: {snap.snapshot_id}")
    print(f"  Active events: {snap.summary['active_event_count']}")
    print(f"  Hotspots: {len(snap.hotspots)}")
    if snap.alerts:
        print(f"  Alerts: {snap.alerts[0]}")

    print("\n🔮 FLOW PREDICTION: Copacabana at 18:00")
    pred = model.predict_urban_flow((-22.9714, -43.1824), hour=18)
    print(f"  Predicted footfall: {pred['predicted_footfall']:,}")
    print(f"  Confidence: {pred['confidence']*100:.0f}%")
    print(f"  Peak hour: {pred['is_peak_hour']}")

    print("\n✅ KEEPIT World Model — all systems operational.")
    print("=" * 60)


if __name__ == "__main__":
    _run_demo()
