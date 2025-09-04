# src/advercpm/attacks/remove_object.py
from .attack import Attack
import random


class RemoveObjectAttack(Attack):
    """
    Remove an object from the CPM:
    - Targeted mode: remove a specific vehicle ID
    - Random mode: remove one randomly chosen vehicle (not ego)
    """

    def __init__(self, params):
        super().__init__(params)
        self.omitted_id = params.get("omitted_id", None)
        self.mode = params.get("mode", "targeted")

    def apply(self, cpm: dict) -> dict:
        vehicles = cpm.get("vehicles", {})

        if not vehicles:
            return cpm

        removed_id = None
        if self.mode == "targeted" and self.omitted_id in vehicles:
            removed_id = self.omitted_id
            vehicles.pop(removed_id, None)
        elif self.mode == "random":
            choices = list(vehicles.keys())
            if choices:
                removed_id = random.choice(choices)
                vehicles.pop(removed_id, None)

        # keep metadata about what was removed for visualization
        if removed_id is not None:
            cpm.setdefault("_removed", []).append(removed_id)

        return cpm
