import math, random, time
# GPSSimulator provides standalone simulated coordinates that move slightly each update.

def haversine(coord1, coord2):
    lat1, lon1 = coord1; lat2, lon2 = coord2
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    R = 6371000.0
    return R * c

class GPSSimulator:
    def __init__(self, start_coord=(7.0731,125.6131)):
        self.lat, self.lon = start_coord
        self.last_time = time.time()

    def _move(self, meters, bearing_deg):
        # Move from current coordinate by meters along bearing (approximate)
        R = 6378137.0
        lat1 = math.radians(self.lat); lon1 = math.radians(self.lon)
        d_div_r = meters / R
        brng = math.radians(bearing_deg)
        lat2 = math.asin(math.sin(lat1) * math.cos(d_div_r) + math.cos(lat1) * math.sin(d_div_r) * math.cos(brng))
        lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d_div_r) * math.cos(lat1), math.cos(d_div_r) - math.sin(lat1) * math.sin(lat2))
        self.lat = math.degrees(lat2); self.lon = math.degrees(lon2)
        return (self.lat, self.lon)

    def next_coord(self):
        # simulate a small random movement between 0.5m and 2.0m each tick (walking pace)
        meters = random.uniform(0.5, 2.0)
        bearing = random.uniform(0, 360)
        return self._move(meters, bearing)
