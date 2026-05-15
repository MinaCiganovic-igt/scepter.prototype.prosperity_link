import itertools
import random
from global_variables import GlobalConfig as GV
import numpy as np
from global_variables import BonusNames as BN
from prosperity_link.project_logic.gamepartlogic_template import \
    GamePartLogicTemplate
from scepter.common.constants import MeterConstants as MC
from scepter.core.logic.scepterinfo import ScepterInfoBlock


# noinspection PyAttributeOutsideInit
class BaseGameLogic(GamePartLogicTemplate):
    def refresh(self):
        info_dict = {
            "reelpicture": self.reelpicture_enum,
            "current_coinpicture": self.current_coinpicture,
            "jackpots": GV.PROG_JACKPOT_ETV
        }
        self.send_wininfo("GAME_SPECIFIC", "refresh", info_dict)

    def play(self, **kwargs):
        # GV.RANDOM_SEED = np.random.randint(low=0, high=2 ** 31 - 1)
        # print(GV.RANDOM_SEED)
        # random.seed(GV.RANDOM_SEED)

        self.meters[MC.WIN].set_value(0)
        self.sib = ScepterInfoBlock(BN.BASEGAME)
        self.kwargs = kwargs
        self.setup_game_state()
        self.spin_reels(BN.BASEGAME)
        #self.pp_pots(BN.BASEGAME)

        self.check_triggers(6, 3, 3, mode="bg")


        self.send_payouts_ways(self.evaluate_ways(),"BaseGame")

        return self.sib

    def setup_game_state(self):
        kwargs = self.kwargs
        self.selected_bet_multiplier = kwargs["stake_options"].selection["Bet Multiplier"]
        self.selected_total_bet = self.selected_bet_multiplier * kwargs["stake_options"].selection["Line Credits"]
        self.parameters = kwargs["parameters"]
        self.speed_up_sim = kwargs["speed_up_sim"]
        self.paytable = self.data["paytable"]
        #self.paylines = self.data["paylines"]
        self.reelsets = self.data["reelsets"]
        self.weightsets = self.data["weightsets"]
        self.base_weights = self.data["base_weights"]
        self.coins_bg_fg = self.data["coins_bg_fg"]
        self.coins_has = self.data["coins_has"]
        self.ways = list(itertools.product(range(3), repeat=5))
        self.wilds = {"_JOK_1_"}

    def spin_reels(self,bonus):
        self.meters["RANDOM_SEED"].set_value(GV.RANDOM_SEED)
        self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})

        if bonus == BN.BASEGAME:
            select_reels = self.data["reelset_selection"].draw_random()
            #print("Select reels: ",select_reels)
            #random_base = self.base_weights[bonus].draw_random()
            weightset = self.weightsets[bonus][select_reels]
            reelset = self.reelsets[bonus][select_reels]

        else:
            select_reels = 0
            reelset = self.reelsets[bonus][select_reels]
            weightset = []
            for i in range(0, 5):
                weightset.append(self.weightsets[bonus][select_reels][i])

        stop_positions = [weightset[reel_idx].draw_random() for reel_idx in range(GV.NUM_OF_REELS)]
        self.reelpicture_enum = []
        self.reelpicture = []
        for reel_idx, stop_position in enumerate(stop_positions):
            self.reelpicture.append([reelset[reel_idx][(stop_position - 1 + i) % len(reelset[reel_idx])] for i in range(GV.REEL_HEIGHT)])
            self.reelpicture_enum.append([GV.STE[i] for i in self.reelpicture[reel_idx]])
        self.reelpicture_enum = np.array(self.reelpicture_enum,dtype=np.float64)
        self.reelpicture = np.array(self.reelpicture)
        self.current_coinpicture = np.zeros_like(self.reelpicture_enum)
        self.coin_places = self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"])
        for coin_place in self.coin_places:
            self.current_coinpicture[coin_place] = self.coins_bg_fg.draw_random()
        self.bn_places = self.places_in_matrix(self.reelpicture_enum, ["_BN_"])
        self.sca_places = self.places_in_matrix(self.reelpicture_enum, ["_SCA_1_"])
        banana = len(self.sca_places)
        self.send_wininfo("STATS_EVENT", f"landed_{banana}_scatters")

        # Tension spin
        sca_per_reel = np.zeros(GV.NUM_OF_REELS)
        sca_per_reel[[pos[0] for pos in self.sca_places]] = 1
        self.reels_to_tension_spin = np.zeros(GV.NUM_OF_REELS)
        if np.sum(sca_per_reel[:-1]) >= 2:
            self.send_wininfo("GAME_SPECIFIC", "bg_tension_spin")
            for reel_idx, _ in enumerate(sca_per_reel):
                if np.sum(sca_per_reel[:reel_idx]) == 2:
                    self.reels_to_tension_spin[reel_idx] = 1

        info_dict = {
            "stop_positions": stop_positions,
            "current_reelpicture": self.reelpicture_enum,
            "current_coinpicture": self.current_coinpicture,
            "reelset": reelset,
            "reelset_enum": self.data["reelsets_enum"][bonus][select_reels], #ovde
            "reels_to_tension_spin": self.reels_to_tension_spin,
        }
        self.send_wininfo("GAME_SPECIFIC", "spin_reels", info_dict)
        self.refresh()
        self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})

    def pp_pots(self,trigger,mode=BN.BASEGAME):

        if mode == BN.BASEGAME:
            pots = GV.POTS_BG
            pot_syms = GV.POTS_BG_SYMS
        else:
            pots = GV.POTS_FG
            pot_syms = GV.POTS_FG_SYMS
        for pot in range(pots):
            places = self.places_in_matrix(self.reelpicture_enum, pot_syms[pot]) #symbol_list argument takes strings
            if places and len(places)<6:
                info_dict = {
                    "pot_index": pot,
                    "reelpicture": self.reelpicture_enum,
                    "trigger": trigger,
                    "coords": places
                }
                self.send_wininfo("GAME_SPECIFIC", "pot", info_dict)

    def evaluate_ways(self):
        ways_infos = []
        #convert all wilds to _JOK_1_
        for sym in self.paytable.symbols:
            if sym in self.wilds:#assuming no wilds on reel 1
                continue
            length = 0
            mult = 1
            ways_win_coordinates = []

            for reel_idx, pict in enumerate(self.reelpicture):

                pict = list(pict)
                if sym in pict or "_JOK_1_" or "_JOK_2_" or "_JOK_3_" or "_JOK_4_" or "_JOK_5_" in pict:
                    mult *= (pict.count("_JOK_1_") + 2*pict.count("_JOK_2_") + 3*pict.count("_JOK_3_") + 4*pict.count("_JOK_4_") + 5*pict.count("_JOK_5_") + pict.count(sym))
                    length+=1
                    ways_win_coordinates.extend([(reel_idx, i) for i in range(len(pict)) if pict[i] in [sym,"_JOK_1_"]])
                else:
                    break

            if length>=2:
                pay = self.paytable.get_win((sym, length)) * mult  * self.selected_bet_multiplier
                if pay>0:
                    info_dict = {
                        "sound": "line_win",
                        "ways_win_coordinates": ways_win_coordinates,
                        "length": length,
                        "reelpicture": self.reelpicture_enum,
                    }
                    ways_infos.append([pay, info_dict])

        return ways_infos

    def send_payouts(self, line_infos,bonus_payloading):
        for credit_win, info_dict in line_infos:
            self.send_wininfo("GAME_SPECIFIC", f"line_win_single_bg")
            self.send_wininfo("GAME_SPECIFIC", "line_win", info_dict)
            self.send_wininfo("CREDIT_WIN", f"line_win_bg", credit_win=credit_win,bonus_payloading=bonus_payloading)

    def send_payouts_ways(self, ways_infos,bonus_payloading):
        for credit_win, info_dict in ways_infos:
            self.send_wininfo("GAME_SPECIFIC", f"ways_win_single_bg")
            self.send_wininfo("GAME_SPECIFIC", "ways_win", info_dict)
            self.send_wininfo("CREDIT_WIN", f"ways_win_bg", credit_win=credit_win,bonus_payloading=bonus_payloading)

    def check_triggers(self, coin_trigger_count, sca_trigger_count, bn_trigger_count,
                    mode="bg", enable_wheel=True, has_delay=True):
        self.coin_places = self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"])

        if len(self.coin_places) >= coin_trigger_count:
            GV.TRIGGERING_MB = len(self.coin_places)
            self.send_wininfo("BONUS_TRIGGER", BN.HOLDANDSPIN)
            if GV.TRIGGERING_MB >= 9:
                self.send_wininfo("GAME_SPECIFIC", "trigger_has_from_bg_9+")
            starting_coin_picture = np.zeros(shape=(GV.HNS_COLS, GV.HNS_ROWS))
            for i, col in enumerate(self.current_coinpicture):
                for j, elem in enumerate(col):
                    starting_coin_picture[i][j + 9] = elem

            GV.EXECUTION_LIST.insert(0, [BN.HOLDANDSPIN, {"current_coinpicture": starting_coin_picture,
                                                          "reelpicture": self.reelpicture}])
            self.current_coinpicture = starting_coin_picture
            self.coin_places = self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"])
            self.send_wininfo("GAME_SPECIFIC", "rotate_symbols", {
                "places": self.coin_places,
                "sound": "fgs_ting",
            })
            if has_delay:
                self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})
            if mode == 'fg':
                self.send_wininfo("GAME_SPECIFIC", "trigger_has_from_fg")
            else:
                self.send_wininfo("GAME_SPECIFIC", "trigger_has_from_bg", {"triggering_MBs": GV.TRIGGERING_MB})

        elif len(self.coin_places) > 0:

            if mode == "bg":
                trigger_table = self.data["pp_trigger_bg"]
            else:
                trigger_table = self.data["pp_trigger_fg"]

            pp_trigger = 0 == trigger_table[len(self.coin_places) - 1].draw_random()
            #pp_trigger = True
            GV.TRIGGERING_MB = 6
            if mode == "bg":
                self.pp_pots(pp_trigger, BN.BASEGAME)
            else:
                self.pp_pots(pp_trigger, BN.FREEGAME)

            if pp_trigger:
                self.send_wininfo("BONUS_TRIGGER", BN.HOLDANDSPIN)

                pot_coins = []

                for i in range(coin_trigger_count - len(self.coin_places)):
                    pot_coins.append(self.coins_has.draw_random())

                starting_coin_picture = np.zeros(shape=(GV.HNS_COLS, GV.HNS_ROWS))
                for i, col in enumerate(self.current_coinpicture):
                    for j, elem in enumerate(col):
                        if elem==0 and len(pot_coins)>0: #should be putting pot coins in the first available locations
                            elem = pot_coins.pop()
                        starting_coin_picture[i][j+9] = elem

                GV.EXECUTION_LIST.insert(0, [BN.HOLDANDSPIN, {"current_coinpicture": starting_coin_picture, "reelpicture": self.reelpicture}])
                self.current_coinpicture = starting_coin_picture
                self.coin_places = self.places_in_matrix(self.reelpicture_enum, ["_COI_1_"])
                self.send_wininfo("GAME_SPECIFIC", "rotate_symbols", {
                    "places": self.coin_places,
                    "sound": "fgs_ting",
                })
                if has_delay:
                    self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})
                if mode == 'fg':
                    self.send_wininfo("GAME_SPECIFIC", "trigger_has_from_fg")
                else:
                    self.send_wininfo("GAME_SPECIFIC", "trigger_has_from_bg", {"triggering_MBs": GV.TRIGGERING_MB})
        if len(self.sca_places) >= sca_trigger_count:
        #if len(self.sca_places) >= 0:
            #total_played = 0
            # if mode == 'fg':
            #     max_fg = 60
            #     current_fg_remaining = self.meters[MC.FREE_GAMES].value
            #
            #     if current_fg_remaining + 10 <= max_fg:
            #         increase_by = 10
            #
            #     else:
            #         increase_by = max_fg - current_fg_remaining
            #
            #     if increase_by > 0:
            #         self.meters[MC.FREE_GAMES].increase_value(increase_by)
            #         self.send_wininfo("GAME_SPECIFIC", "retrigger_fg")
            #
            #         for i in range(increase_by):
            #             GV.EXECUTION_LIST.append([BN.FREEGAME, {}])

            if mode=='fg':
                max_fg = 60
                #total_played += 1
                current_fg_remaining = self.meters[MC.FREE_GAMES].value
                current_fg_played = GV.FREE_GAMES_PLAYED
                #current_fg_played = max(0,GV.FREE_GAMES_PLAYED - 1)
                #dodala sam -1 jer u fg logic dodajem, pa ovde moram da oduzmem jer retriger logika gleda stanje pre trenutnog spina
                #total = total_played + current_fg + 10

                if current_fg_remaining + current_fg_played + 10 <= max_fg:
                    self.meters[MC.FREE_GAMES].increase_value(10)
                    self.send_wininfo("GAME_SPECIFIC", "retrigger_fg")
                    for i in range(10):
                        GV.EXECUTION_LIST.append([BN.FREEGAME, {}])
                else:
                    increase_by = max_fg - current_fg_remaining - current_fg_played #can only increase by this much
                    self.meters[MC.FREE_GAMES].increase_value(increase_by)
                    self.send_wininfo("GAME_SPECIFIC", "retrigger_fg")
                    for i in range(increase_by):
                        GV.EXECUTION_LIST.append([BN.FREEGAME, {}])

            else:
                GV.FREE_GAMES_PLAYED = 0
                self.meters[MC.FREE_GAMES].set_value(10)
                self.send_wininfo("GAME_SPECIFIC", "trigger_fg")
                for i in range(10):
                    GV.EXECUTION_LIST.append([BN.FREEGAME, {"already_played":0}])

            self.send_wininfo("AVERAGE_VALUE", "fg_spins", value_to_track=5)
            self.send_wininfo("UPDATE_METERS", wininfo_data={"meters": self.meters})
            if mode == 'fg':
                self.send_wininfo("BONUS_TRIGGER", BN.FREEGAME_RE_TRIG)
            else:
                self.send_wininfo("BONUS_TRIGGER", BN.FREEGAME)
            #self.send_wininfo("GAME_SPECIFIC", "heartbeat_symbols", {
            #     "places": self.sca_places,
            #     "sound": "fgs_ting",
            # })
            # for i in range(10):
            #     GV.EXECUTION_LIST.append([BN.FREEGAME, {}])
            if has_delay:
                self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})
        if enable_wheel and len(self.bn_places) >= bn_trigger_count:
            self.send_wininfo("BONUS_TRIGGER", BN.WHEEL)
            self.send_wininfo("GAME_SPECIFIC", "trigger_bn")
            #self.send_wininfo("GAME_SPECIFIC", "heartbeat_symbols", {
            #     "places": self.bn_places,
            #     "sound": "fgs_ting",
            # })
            GV.EXECUTION_LIST.insert(0,[BN.WHEEL, {}])
            self.send_wininfo("GAME_SPECIFIC", "delay", {"delay_amount": "HOLD_REELPICTURE"})

    def apply_random_wild_feature(self):
        self.multiplier_picture = np.zeros_like(self.current_coinpicture)
        pattern_draw = self.data["random_wild_table"].draw_random()

        pattern = [int(char) for char in pattern_draw[1:]]


        for idx, val in enumerate(pattern):
            if val == 0:
                continue

            row = idx // 5
            col = idx % 5

            current_symbol = self.reelpicture[col][row]
            if current_symbol in ["_SCA_1_", "_COI_1_"]:
                continue

            self.reelpicture[col][row] = f"_JOK_{val}_"
            self.multiplier_picture[col][row] = val
            self.reelpicture_enum[col][row] = GV.STE[f"_JOK_{val}_"]





