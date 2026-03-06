from copy import deepcopy

from global_variables import GlobalConfig as GV
import numpy as np
from scepter.common.constants import MeterConstants as MC
from scepter.common.constants import ScepterInfoInfo as SII
from scepter.common.constants import ScepterInfoType as SIT
from scepter.core.logic.gamepart_logic import GamePartLogic
from scepter.core.logic.scepterinfo import ScepterInfo
from scepter.library.randomizer.weight_representations.weights import Weights


class GamePartLogicTemplate(GamePartLogic):
    def places_in_matrix(self, matrix, symbol_list):
        places = []
        if symbol_list:
            for reel_idx, reel in enumerate(matrix):
                for row_idx, sym in enumerate(reel):
                    if GV.ETS[sym] in symbol_list:
                        places.append((reel_idx, row_idx))
        return places

    def send_wininfo(self, wininfo_type, wininfo_id="", wininfo_data={}, credit_win=0, value_to_track = 0,bonus_payloading = None):
        credit_win = int(credit_win)
        if wininfo_type == "WAIT_FOR_USER_INPUT":
            scepterinfo = ScepterInfo({SIT.DRAW_ANIMATION}, "manual_spin")
            self.sib.add_scepterinfo(scepterinfo)
        if wininfo_type == "CREDIT_WIN" and credit_win:
            for scepterinfo in self.process_credit_win(credit_win, scepterinfo_id=wininfo_id, additional_infos={}):
                self.sib.add_scepterinfo(scepterinfo)
            if bonus_payloading:
                bg_stat_si = ScepterInfo(set([SIT.STATS_PAYLOAD]), bonus_payloading)
                bg_stat_si.add("credit_win", credit_win)
                self.sib.add_scepterinfo(bg_stat_si)
        if wininfo_type == "STATS_CREDIT":
            scepterinfo = ScepterInfo(set([SIT.STATS_PAYLOAD]), wininfo_id)
            scepterinfo.add("credit_win", credit_win)
            self.sib.add_scepterinfo(scepterinfo)
        if wininfo_type == "STATS_EVENT":
            scepterinfo = ScepterInfo(set([SIT.STATS_PAYLOAD]), wininfo_id)
            scepterinfo.add("credit_win", 0)
            self.sib.add_scepterinfo(scepterinfo)
        if wininfo_type == "BONUS_TRIGGER":
            scepterinfo = ScepterInfo(set([SIT.BONUS_TRIGGER]), wininfo_id)
            self.sib.add_scepterinfo(scepterinfo)
        if wininfo_type == "AVERAGE_VALUE":
            scepterinfo = ScepterInfo(set([SIT.GAME_SPECIFIC]), wininfo_id)
            scepterinfo.add("info_dict", {"value_to_track": value_to_track})
            self.sib.add_scepterinfo(scepterinfo)        
        if not self.speed_up_sim:
            wininfo_data = deepcopy(wininfo_data)
            if wininfo_type == "GAME_SPECIFIC":
                scepterinfo = ScepterInfo(set([SIT.GAME_SPECIFIC]), wininfo_id)
                scepterinfo.add("info_dict", wininfo_data)
                self.sib.add_scepterinfo(scepterinfo)
            if wininfo_type == "UPDATE_METERS":
                for meter_constant in wininfo_data["meters"]:
                    if meter_constant != MC.CREDITS:
                        scepterinfo = ScepterInfo(set([SIT.VISUALIZE_METERS]), wininfo_id)
                        scepterinfo.add(SII.METERS_TO_UPDATE, {meter_constant: self.meters[meter_constant].value})
                        self.sib.add_scepterinfo(scepterinfo)

class DrawGame:
    def __init__(self, weights, results = None):
        self.weights = np.array(weights, dtype=np.uint32)
        self.probs = self.weights / np.sum(self.weights)
        self.huffman_representation = Weights(weights)
        self.results = results

    def draw_random(self):
        draw_idx = self.huffman_representation.draw_random()
        if GV.PRIZE_FIRST:
            if GV.CREATE_OUTCOMES:
                if self.results:
                    GV.DRAWGAME_LIST.append(self.results[draw_idx])
                else:
                    GV.DRAWGAME_LIST.append(draw_idx)
            else:
                return GV.DRAWGAME_LIST.pop(0)
            
        if self.results == []:
            raise ValueError('Empty list for drawgame result')
        
        if self.results:
            return self.results[draw_idx]
        return draw_idx
    
    def draw_random_non_outcome(self):
        draw_idx = np.random.choice(len(self.probs), p=self.probs)
        if self.results:
            return self.results[draw_idx]
        else:
            return draw_idx
