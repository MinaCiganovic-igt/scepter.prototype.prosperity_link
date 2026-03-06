import random

from global_variables import GlobalConfig as GV
import numpy as np
from global_variables import BonusNames as BN
from prototype_vibe.project_logic.gamepartlogic_template import \
    GamePartLogicTemplate
from scepter.common.constants import MeterConstants as MC
from scepter.core.logic.scepterinfo import ScepterInfoBlock


class HoldAndSpinLogic(GamePartLogicTemplate):
    def refresh(self):
        info_dict = {
            "reelpicture": self.reelpicture,
            "current_coinpicture": self.current_coinpicture,
            "jackpots": GV.PROG_JACKPOT_ETV
        }
        self.send_wininfo("GAME_SPECIFIC", "refresh", info_dict)
        
    def play(self, **kwargs):
        self.sib = ScepterInfoBlock(BN.HOLDANDSPIN)
        selected_bet_multiplier = kwargs["stake_options"].selection["Bet Multiplier"]
        selected_total_bet = selected_bet_multiplier * kwargs["stake_options"].selection["Line Credits"]

        parameters = kwargs["parameters"]
        self.speed_up_sim = kwargs["speed_up_sim"]

        self.meters[MC.SPIN_COUNTER].set_value(3)
        
        coins_has = self.data["coins_has"]
        num_new_coins_drawn_dg = self.data["num_new_coins_drawn_dg"]
        num_spins_dg = self.data["num_spins_dg"]

        self.current_coinpicture = parameters["current_coinpicture"]
        self.reelpicture = np.zeros_like(self.current_coinpicture)
        self.reelpicture[:, :] = GV.STE["_BLN_2_"]
        self.reelpicture[np.where(self.current_coinpicture)] = GV.STE["_COI_1_"]
        

        self.meters[MC.SPIN_COUNTER].set_value(3)
        self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
        self.refresh()
        self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})
        
        while True:
            num_coins = len(self.places_in_matrix(self.reelpicture, ["_COI_1_"]))
            dep = num_coins - 6
            dep = min(dep,8)
            bln_places = self.places_in_matrix(self.reelpicture, ["_BLN_2_"])
            if not bln_places:
                self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})
                self.send_wininfo("GAME_SPECIFIC", f"full_grid_has")
                break
            random.shuffle(bln_places)
            num_new_coins = num_new_coins_drawn_dg[dep].draw_random()
            if not num_new_coins:
                for _ in range(3):
                    self.send_wininfo("WAIT_FOR_USER_INPUT")
                    info_dict = {
                        "reelpicture": self.reelpicture,
                        "current_coinpicture": self.current_coinpicture,
                        "places_to_spin": bln_places,
                    }
                    self.meters[MC.SPIN_COUNTER].increase_value(-1)
                    self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)
                    self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
                    self.refresh()
                    self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE", "sound": "no_coin"})
                break
            else:
                num_spins = num_spins_dg[dep].draw_random()
                for _ in range(num_spins-1):
                    self.send_wininfo("WAIT_FOR_USER_INPUT")
                    info_dict = {
                        "reelpicture": self.reelpicture,
                        "current_coinpicture": self.current_coinpicture,
                        "places_to_spin": bln_places,
                    }
                    self.meters[MC.SPIN_COUNTER].increase_value(-1)
                    self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)
                    self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
                    self.refresh()
                    self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE", "sound": "no_coin"})
                self.send_wininfo("WAIT_FOR_USER_INPUT")
                landing_places = []
                for _ in range(num_new_coins):
                    place = bln_places.pop(0)
                    landing_places.append(place)
                    self.reelpicture[place] = GV.STE["_COI_1_"]
                    self.current_coinpicture[place] = coins_has.draw_random()
                info_dict = {
                    "reelpicture": self.reelpicture,
                    "current_coinpicture": self.current_coinpicture,
                    "places_to_spin": bln_places + landing_places,
                }
                self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)
                self.meters[MC.SPIN_COUNTER].set_value(3)
                self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
                self.refresh()
                self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE", "sound": "line_win"})

        for place in self.places_in_matrix(self.reelpicture, ["_COI_1_"]):
            self.send_wininfo("GAME_SPECIFIC", "collect_coin", {"coin_place": place, "num_of_reels": GV.HNS_COLS})
            self.send_wininfo("GAME_SPECIFIC", "", {"sound": "line_win"})
            self.send_wininfo("CREDIT_WIN", f"coin_win", credit_win = self.current_coinpicture[place],bonus_payloading="HnS")
        #self.send_wininfo("BONUS_TRIGGER", "HnS")

        return self.sib
