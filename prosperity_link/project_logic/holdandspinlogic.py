import random

from global_variables import GlobalConfig as GV
import numpy as np
from global_variables import BonusNames as BN
from prosperity_link.project_logic.gamepartlogic_template import \
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
        parameters = kwargs["parameters"]
        self.speed_up_sim = kwargs["speed_up_sim"]

        self.current_coinpicture = parameters["current_coinpicture"]
        self.current_coinpicture = parameters["current_coinpicture"]
        self.reelpicture_enum = np.zeros_like(self.current_coinpicture)  # will store integer keys for symbols
        self.reelpicture = np.empty_like(self.current_coinpicture, dtype=object)  # will store strings for symbols
        self.reelpicture_enum[:, :] = GV.STE["_BLN_2_"]
        self.reelpicture_enum[np.where(self.current_coinpicture)] = GV.STE["_COI_1_"]
        self.reelpicture[:, :] = "_BLN_2_"
        self.reelpicture[np.where(self.current_coinpicture)] = "_COI_1_"

        self.unlocked_levels = [True, False, False, False]
        self.coin_positions = self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"])

        self.num_locked_coins = len(self.coin_positions)

        mode = self.data["feat_mode_selector"].draw_random()
        if mode in [1, 2, 3]:
            table = self.data["hns_table_1"]
        else:
            table = self.data["hns_table_2"]

        self.meters[MC.SPIN_COUNTER].set_value(3)
        self.refresh()

        while self.meters[MC.SPIN_COUNTER].value > 0:

            self.update_unlocks()

            new_coin_landed = False
            all_blanks = []
            for level in range(4):

                #if level ==0 (first interface), rows are 9,10,11

                blanks = self.places_in_matrix(self.reelpicture_enum[(3-level)*3:((3-level)+1)*3,:], ["_BLN_2_"])
                all_blanks.extend(blanks)
                # if not blanks:
                #     self.meters[MC.SPIN_COUNTER].set_value(0)
                #     break

                random.shuffle(blanks)

                special_positions = blanks[:2]
                normal_positions = blanks[2:]


                for pos in special_positions:
                    rs_choice = self.data["stopper_selector"].draw_random()
                    rs_id = rs_choice

                    symbol = self.data["rs_tables"][rs_id].draw_random()

                    if symbol == "_COI_1_":
                        self.lock_coin(level, pos, table)
                        new_coin_landed = True

                for pos in normal_positions:
                    coins_in_interface = len(self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"]))

                    if coins_in_interface <= 5:
                        z = 0
                    elif coins_in_interface <= 8:
                        z = 1
                    else:
                        z = 2

                    rs_id = self.data["feature_tables"][mode][level + 1][z].draw_random()
                    symbol = self.data["rs_tables"][rs_id].draw_random()

                    if symbol == "_COI_1_":
                        self.lock_coin(level, pos, table)
                        new_coin_landed = True

            # if new_coin_landed:
            #     self.meters[MC.SPIN_COUNTER].set_value(3)
            #
            # else:
            #     self.meters[MC.SPIN_COUNTER].increase_value(-1)

            self.meters[MC.SPIN_COUNTER].increase_value(-1)
            info_dict = {
                                "reelpicture": self.reelpicture,
                                "current_coinpicture": self.current_coinpicture,
                                "places_to_spin": all_blanks,
                            }

            self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)
            #self.meters[MC.SPIN_COUNTER].set_value(3)
            self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
            self.refresh()
            # blanks = self.places_in_matrix(self.reelpicture_enum[:], ["_BLN_2_"])
            # all_blanks.extend(blanks)
            # if not blanks:
            #     self.meters[MC.SPIN_COUNTER].set_value(0)
            #     break
            #self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE", "sound": "line_win"})


        for place in self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"]):
            self.send_wininfo("GAME_SPECIFIC", "collect_coin", {"coin_place": place, "num_of_reels": GV.HNS_COLS})
            self.send_wininfo("GAME_SPECIFIC", "", {"sound": "line_win"})
            self.send_wininfo("CREDIT_WIN", f"coin_win", credit_win=self.current_coinpicture[place],
                              bonus_payloading="HnS")
        self.send_wininfo("BONUS_TRIGGER", "HnS")

        return self.sib

    def update_unlocks(self):
        if self.num_locked_coins >= 9:
            self.unlocked_levels[1] = True
        if self.num_locked_coins >= 18:
            self.unlocked_levels[2] = True
        if self.num_locked_coins >= 32:
            self.unlocked_levels[3] = True

    def lock_coin(self, level, pos, table): #need to rework with no reelpicture[level]
        self.reelpicture_enum[pos] = GV.STE["_COI_1_"]
        self.reelpicture[pos] = "_COI_1_"
        value = table[level + 1].draw_random()

        self.current_coinpicture[pos] = value
        #self.current_coinpicture[level][pos] = value
        self.num_locked_coins += 1

        # class HoldAndSpinLogic(GamePartLogicTemplate):
#     def refresh(self):
#         info_dict = {
#             "reelpicture": self.reelpicture,
#             "current_coinpicture": self.current_coinpicture,
#             "jackpots": GV.PROG_JACKPOT_ETV
#         }
#         self.send_wininfo("GAME_SPECIFIC", "refresh", info_dict)
#
#     def update_unlocks(self):
#         if self.total_coins >= 9:
#             self.unlocked_levels[1] = True
#         if self.total_coins >= 18:
#             self.unlocked_levels[2] = True
#         if self.total_coins >= 32:
#             self.unlocked_levels[3] = True
#
#     def play(self, **kwargs):
#         self.sib = ScepterInfoBlock(BN.HOLDANDSPIN)
#         #MULTI GRID INIT
#         self.total_coins = 0 #ukljuci pocetan broj novcica
#         self.unlocked_levels = [True, False, False, False]
#         #self.reelpictures = [np.zeros((3, 5)) for _ in range(4)]
#         #self.current_coinpictures = [np.zeros((3, 5)) for _ in range(4)]
#
#         selected_bet_multiplier = kwargs["stake_options"].selection["Bet Multiplier"]
#         selected_total_bet = selected_bet_multiplier * kwargs["stake_options"].selection["Line Credits"]
#
#         parameters = kwargs["parameters"]
#         self.speed_up_sim = kwargs["speed_up_sim"]
#
#         self.meters[MC.SPIN_COUNTER].set_value(3)
#
#         coins_has = self.data["coins_has"]
#         num_new_coins_drawn_dg = self.data["num_new_coins_drawn_dg"]
#         num_spins_dg = self.data["num_spins_dg"]
#
#         #BASED ON MODE CHOOSE TABLE
#         mode = self.data["feat_mode_selector"].draw_random()
#         if mode in [1, 2, 3]:
#             table = self.data["hns_table_1"]
#         else:
#             table = self.data["hns_table_2"]
#
#         self.current_coinpicture = parameters["current_coinpicture"]
#         self.reelpicture = np.zeros_like(self.current_coinpicture)
#         self.reelpicture[:, :] = GV.STE["_BLN_2_"]
#         self.reelpicture[np.where(self.current_coinpicture)] = GV.STE["_COI_1_"]
#
#
#         self.meters[MC.SPIN_COUNTER].set_value(3)
#         self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
#         self.refresh()
#         self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})
#         #odavde na dole obrisi i zameni
#         while True:
#             num_coins = len(self.places_in_matrix(self.reelpicture, ["_COI_1_"]))
#             dep = num_coins - 6
#             dep = min(dep,8)
#             #bln_places = self.places_in_matrix(self.reelpicture, ["_BLN_2_"])
#             #prvi element ce biti oznaka koji je interfejs tj nivo, a drugi pozicija u tom interfejsu
#             bln_places = []
#             for level in range(4):
#                 if self.unlocked_levels[level]:
#                     places = self.places_in_matrix(self.reelpictures[level], ["_BLN_2_"])
#                     bln_places.extend([(level, p) for p in places])
#
#             if not bln_places:
#                 self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})
#                 self.send_wininfo("GAME_SPECIFIC", f"full_grid_has")
#                 break
#             random.shuffle(bln_places)
#             num_new_coins = num_new_coins_drawn_dg[dep].draw_random()
#             if not num_new_coins:
#                 for _ in range(3):
#                     self.send_wininfo("WAIT_FOR_USER_INPUT")
#                     info_dict = {
#                         "reelpicture": self.reelpicture,
#                         "current_coinpicture": self.current_coinpicture,
#                         "places_to_spin": bln_places,
#                     }
#                     self.meters[MC.SPIN_COUNTER].increase_value(-1)
#                     self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)
#                     self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
#                     self.refresh()
#                     self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE", "sound": "no_coin"})
#                 break
#             else:
#                 num_spins = num_spins_dg[dep].draw_random()
#                 for _ in range(num_spins-1):
#                     self.send_wininfo("WAIT_FOR_USER_INPUT")
#                     info_dict = {
#                         "reelpicture": self.reelpicture,
#                         "current_coinpicture": self.current_coinpicture,
#                         "places_to_spin": bln_places,
#                     }
#                     self.meters[MC.SPIN_COUNTER].increase_value(-1)
#                     self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)
#                     self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
#                     self.refresh()
#                     self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE", "sound": "no_coin"})
#                 self.send_wininfo("WAIT_FOR_USER_INPUT")
#                 landing_places = []
#                 for _ in range(num_new_coins):
#                     place = bln_places.pop(0)
#                     level, pos = place
#                     #jos izmmena ovde
#                     landing_places.append(place)
#                     #self.reelpicture[place] = GV.STE["_COI_1_"]
#                     self.reelpicture[level][pos] = GV.STE["_COI_1_"]
#                     #self.current_coinpicture[place] = coins_has.draw_random()
#
#                     #weightset (po broju coin-a)
#                     if num_coins <= 5:
#                         ws = 0
#                     elif num_coins < 9:
#                         ws = 1
#                     else:
#                         ws = 2
#                     #interface (level 0-3 → interface 1-4)
#                     interface = level + 1
#                     #RS izbor
#                     rs_id = self.data["feature_tables"][mode][interface][ws].draw()
#                     #iz RS tabele dobijam simbol
#                     symbol = self.data["rs_tables"][rs_id].draw()
#                     #PROVERA — da li je MB (coinRS)
#                     if symbol == "_COI_1_":
#                         #DODAJEM COIN na grid
#                         self.reelpicture[level][pos] = GV.STE["_COI_1_"]
#                         value = table[level].draw_random()
#                         self.current_coinpicture[level][pos] = value
#                         self.total_coins += 1
#                 self.update_unlocks()
#
#                 info_dict = {
#                     "reelpicture": self.reelpicture,
#                     "current_coinpicture": self.current_coinpicture,
#                     "places_to_spin": bln_places + landing_places,
#                 }
#                 self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)
#                 self.meters[MC.SPIN_COUNTER].set_value(3)
#                 self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
#                 self.refresh()
#                 self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE", "sound": "line_win"})
#

#         return self.sib
