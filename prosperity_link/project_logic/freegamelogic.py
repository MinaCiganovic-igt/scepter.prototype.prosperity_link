import random
from global_variables import GlobalConfig as GV
import numpy as np
from global_variables import BonusNames as BN
from prosperity_link.project_logic.gamepartlogic_template import \
    GamePartLogicTemplate
from scepter.common.constants import MeterConstants as MC
from scepter.core.logic.scepterinfo import ScepterInfoBlock

from .basegamelogic import BaseGameLogic

class FreeGameLogic(BaseGameLogic):
    def play(self, **kwargs):
        #GV.FREE_GAMES_PLAYED += 1

        self.sib = ScepterInfoBlock(BN.FREEGAME)
        self.kwargs = kwargs
        parameters = kwargs["parameters"]

        self.setup_game_state()
        self.send_wininfo("GAME_SPECIFIC", "reset_scene", {})
        self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
        #while self.meters[MC.FREE_GAMES].value:
        self.send_wininfo("GAME_SPECIFIC", "fg_spin")
        self.send_wininfo("WAIT_FOR_USER_INPUT")
        self.spin_reels(BN.FREEGAME)
        self.apply_random_wild_feature()
        self.pp_pots(BN.FREEGAME)
        line_infos = self.evaluate_ways()
        self.send_payouts_ways(line_infos,"FreeGame")
        self.check_triggers(6, 3, float("inf"), mode="fg", enable_wheel=False, has_delay=False)
        GV.FREE_GAMES_PLAYED += 1
        #self.meters[MC.FREE_GAMES].increase_value(-1)
        self.meters[MC.FREE_GAMES].set_value(max(0,self.meters[MC.FREE_GAMES].value - 1))
        self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
        self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})
        self.send_wininfo("STATS_EVENT", "trigger_fg")
        return self.sib

