import random

from pyglet.window.key import PRINT

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
                    "jackpots": GV.PROG_JACKPOT_ETV,
                }
        self.send_wininfo("GAME_SPECIFIC", "refresh", info_dict)

    def play(self, **kwargs):
        print("HNS start\n")
        self.sib = ScepterInfoBlock(BN.HOLDANDSPIN)
        parameters = kwargs["parameters"]
        self.speed_up_sim = kwargs["speed_up_sim"]

        self.current_coinpicture = parameters["current_coinpicture"]

        self.reelpicture_enum = np.zeros_like(self.current_coinpicture)  # will store integer keys for symbols
        self.reelpicture = np.empty_like(self.current_coinpicture, dtype=object)  # will store strings for symbols
        self.reelpicture_enum[:, :] = GV.STE["_BLN_2_"]
        self.reelpicture_enum[np.where(self.current_coinpicture)] = GV.STE["_COI_1_"]
        self.reelpicture[:, :] = "_BLN_2_"
        self.reelpicture[np.where(self.current_coinpicture)] = "_COI_1_"
        self.spins_played = 0

        self.unlocked_levels = [True, False, False, False]
        self.num_coins_per_level = [0, 0, 0, 0]
        self.dim_step = 0

        print("Matrix: ", self.reelpicture_enum)
        print("Coin positions:", self.get_all_coin_positions())

        for pos in self.get_active_coin_positions():
            level = self.get_level(pos)
            self.num_coins_per_level[level] += 1
        print("Initial coins per level:", self.num_coins_per_level)
        #self.coin_positions = self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"])
        #self.num_locked_coins = len(self.coin_positions)

        mode = self.data["feat_mode_selector"].draw_random()
        if mode in [1, 2, 3]:
            table = self.data["hns_table_1"]
        else:
            table = self.data["hns_table_2"]

        self.meters[MC.SPIN_COUNTER].set_value(3)
        self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
        self.refresh()
        self.show_status()
        while self.meters[MC.SPIN_COUNTER].value > 0:

            self.spin_coins_before = list(self.num_coins_per_level)
            new_coin_landed = False
            all_blanks = self.places_in_matrix(self.reelpicture_enum, ["_BLN_2_"])

            for level in range(4):

                #if level ==0 (first interface), rows are 9,10,11

                blanks = [a for a in all_blanks if (a[1]>=(3-level)*3 and a[1]<(3-level+1)*3)]
                coins_in_interface = 15 - len(blanks)

                random.shuffle(blanks)

                special_positions = blanks[:2]
                normal_positions = blanks[2:]

                for pos in special_positions:
                    rs_choice = self.data["stopper_selector"].draw_random()
                    rs_id = rs_choice

                    symbol = self.data["rs_tables"][rs_id].draw_random()

                    if symbol == "_COI_1_":
                        print("If statement triggered")
                        self.lock_coin(level, pos, table)
                        new_coin_landed = True

                if coins_in_interface <= 5:
                    z = 0
                elif coins_in_interface <= 8:
                    z = 1
                else:
                    z = 2
                for pos in normal_positions:

                    rs_id = self.data["feature_tables"][mode][level + 1][z].draw_random()
                    symbol = self.data["rs_tables"][rs_id].draw_random()

                    if symbol == "_COI_1_":
                        self.lock_coin(level, pos, table)
                        new_coin_landed = True

            if new_coin_landed:
                self.meters[MC.SPIN_COUNTER].set_value(3)
            else:
                 self.meters[MC.SPIN_COUNTER].increase_value(-1)

            print("End spin summary")
            print("Coins per level: ",self.num_coins_per_level)
            print("Unlocked levels: ",self.unlocked_levels)
            print("Active coins: ", len(self.get_active_coin_positions()))

            # if self.unlocked_levels[1]: # bad practice by David
            #     if self.unlocked_levels[2]:
            #         if self.unlocked_levels[3]:
            #             dimmed = []
            #         else:
            #             dimmed = [0,1,2]
            #     else:
            #         dimmed = [0,1,2,3,4,5]
            # else:
            #     dimmed = [0,1,2,3,4,5,6,7,8]
            self.update_unlocks()
            self.update_multipliers()
            self.update_dimmed_reels()

            dimmed = GV.DIMMED_REELS
            counter = GV.LRS_COUNTERS

            self.send_wininfo("WAIT_FOR_USER_INPUT")
            info_dict = {
                                "reelpicture": self.reelpicture,
                                "current_coinpicture": self.current_coinpicture,
                                "places_to_spin": all_blanks,
                                "dimmed_reels": dimmed,
                                "counters": counter,
                                "unlocked_levels": self.unlocked_levels,
                            }

            self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)

            #self.meters[MC.SPIN_COUNTER].set_value(3)
            self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
            self.refresh()
            #self.send_wininfo("GAME_SPECIFIC", "unlock", info_dict)  # don't need to call it every spin
            #self.refresh()

            self.spins_played += 1
            self.show_status()

        for place in self.get_active_coin_positions():
            self.send_wininfo("GAME_SPECIFIC", "collect_coin", {
                "coin_place": place,
                "num_of_reels": GV.HNS_COLS
            })
            self.send_wininfo("GAME_SPECIFIC", "", {"sound": "line_win"})
            self.send_wininfo("CREDIT_WIN", f"coin_win",
                              credit_win=self.current_coinpicture[place],
                              bonus_payloading="HnS")

        self.send_wininfo("BONUS_TRIGGER", "HnS")

        return self.sib

    def get_level(self, pos):
        col, row = pos

        if row in [9, 10, 11]:
            return 0
        elif row in [6, 7, 8]:
            return 1
        elif row in [3, 4, 5]:
            return 2
        else:
            return 3

    def get_all_coin_positions(self):
        return self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"])

    def get_active_coin_positions(self):
        active = []
        for pos in self.get_all_coin_positions():
            level = self.get_level(pos)
            if self.unlocked_levels[level]:
                active.append(pos)
        return active

    def update_unlocks(self):
        # level 1 unlock -> level 0
        if not self.unlocked_levels[1]:
            if self.num_coins_per_level[0] >= 9:
                self.unlocked_levels[1] = True
                self.dim_step = 1
        # level 2 unlock -> level 0 + 1
        if not self.unlocked_levels[2]:
            if sum(self.num_coins_per_level[:2]) >= 18:
                self.unlocked_levels[2] = True
                self.dim_step = 2
        # level 3 unlock -> level 0 + 1 + 2
        if not self.unlocked_levels[3]:
            if sum(self.num_coins_per_level[:3]) >= 32:
                self.unlocked_levels[3] = True
                self.dim_step = 3

        # if a new interface has just been activated, need to add coins in that interface to self.num_locked_coins
        # so we can look at the reel picture at that moment and find all _COI_1_
        # or we can keep a list of the number of coins locked in each interface
        # self.num_coins_per_level = [starting_coins, 0,0,0]

    def lock_coin(self, level, pos, table):
        print(f"Coin landed at {pos}")
        print("Level: ", level)
        print("Before update: ", self.num_coins_per_level)
        self.reelpicture_enum[pos] = GV.STE["_COI_1_"]
        self.reelpicture[pos] = "_COI_1_"
        value = table[level].draw_random()

        self.current_coinpicture[pos] = value
        self.num_coins_per_level[level] += 1
        self.pending_update = True
        print("After update: ",self.num_coins_per_level)

    def update_multipliers(self):
        need_lvl1 = max(0, 9 - self.num_coins_per_level[0])
        need_lvl2 = max(0, 18 - sum(self.num_coins_per_level[:2]))
        need_lvl3 = max(0, 32 - sum(self.num_coins_per_level[:3]))
        GV.LRS_COUNTERS = [need_lvl1, need_lvl2, need_lvl3]
        print("COUNTERS:", GV.LRS_COUNTERS)

    def update_dimmed_reels(self):
        base = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        if self.dim_step == 0:
            GV.DIMMED_REELS = base
        elif self.dim_step == 1:
            GV.DIMMED_REELS = base[:6]
        elif self.dim_step == 2:
            GV.DIMMED_REELS = base[:3]
        else:
            GV.DIMMED_REELS = []

        print(GV.DIMMED_REELS)

    def show_status(self):
        print("\n--------------------------")
        print("Spins played: ", self.spins_played)
        print("Interfaces Active: ", sum(self.unlocked_levels))
        print("Current Coin Picture:")
        print(self.current_coinpicture)# = parameters["current_coinpicture"])
        print("Active coins: ", len(self.get_active_coin_positions()))
        print("--------------------------")
