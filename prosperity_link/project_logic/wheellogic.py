from typing import Any, Dict

import random

from global_variables import GlobalConfig as GV
from global_variables import BonusNames as BN
from prosperity_link.project_logic.gamepartlogic_template import GamePartLogicTemplate
from scepter.core.logic.scepterinfo import ScepterInfoBlock
from scepter.library.randomizer.random_wrapper import random_integer_n_to_m


class WheelLogic(GamePartLogicTemplate):
    def _angle_per_wedge(self, n_wedges: int) -> float:
        return 360.0 / float(n_wedges) if n_wedges else 0.0

    def _send_wheel_event(self, event: str, payload: Dict[str, Any] | None = None) -> None:
        payload = payload or {}
        
        self.send_wininfo("GAME_SPECIFIC", event, payload)

    def play(self, **kwargs) -> ScepterInfoBlock:

        self.sib = ScepterInfoBlock(BN.WHEEL)
        
        _ = kwargs.get("parameters")
        self.speed_up_sim = kwargs.get("speed_up_sim")

        wheel_wedges = self.data.get("wheel_wedges")
        if wheel_wedges is None:
            return self.sib

        self._send_wheel_event("reset_wheel")

        n_wedges = len(wheel_wedges.results)
        angle = self._angle_per_wedge(n_wedges)

        drawn_wedge = random_integer_n_to_m(0, n_wedges - 1)
        full_rotations = random_integer_n_to_m(3, 6)
        rotation = full_rotations * 360.0 - drawn_wedge * angle

        self._send_wheel_event("wheel_spin_start", {"drawn_wedge": drawn_wedge, "rotation": rotation})

        stop_angle = -drawn_wedge * angle
        self._send_wheel_event("wheel_spin_stop", {"drawn_wedge": drawn_wedge, "stop_angle": stop_angle})

        credit = wheel_wedges.results[drawn_wedge]
        self.send_wininfo("CREDIT_WIN", "wheel_win", credit_win=credit, bonus_payloading="Wheel")

        self._send_wheel_event("wheel_exit", {"drawn_wedge": drawn_wedge})

        return self.sib