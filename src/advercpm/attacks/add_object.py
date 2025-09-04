import math


class AddObjectAttack:
    def __init__(self, params):
        self.ego_id = params.get("ego_id")
        self.object_id = params.get("object_id", 9999)
        self.distance_ahead = params.get("distance_ahead", 10.0)
        self.vel = params.get("vel", 0.0)
        self.extent = params.get("extent", [4.0, 2.0, 1.5])
        self.malicious_id = params.get("malicious_id")  # 👈 NEW

    def apply(self, cpm: dict) -> dict:
        vehicles = cpm.get("vehicles", {})

        if self.ego_id not in vehicles or self.malicious_id not in vehicles:
            return cpm  # only apply if both ego + malicious exist

        ego = vehicles[self.ego_id]

        # Place fake object in front of ego
        x, y, _ = ego["location"]
        yaw = ego["angle"][1]
        dx = self.distance_ahead * math.cos(yaw)
        dy = self.distance_ahead * math.sin(yaw)

        fake_obj = {
            "angle": ego["angle"].copy(),  # inherit orientation
            "center": ego["center"].copy(),
            "extent": self.extent,
            "location": [x + dx, y + dy, ego["location"][2]],
            "speed": self.vel,
        }

        vehicles[self.object_id] = fake_obj
        cpm["vehicles"] = vehicles
        return cpm
