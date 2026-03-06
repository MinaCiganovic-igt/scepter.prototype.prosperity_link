import csv
import pickle
import statistics
from collections import defaultdict
from copy import deepcopy

from global_variables import GlobalConfig as GV
import numpy as np
from global_variables import BonusNames as BN
from scepter.common.constants import MeterConstants as MC
from scepter.common.constants import ScepterInfoType as SIT
from scepter.core.logic.meter import Meter

meters = {
    mc: Meter()
    for mc in [MC.CREDITS, MC.WIN, MC.TOTAL_BET, MC.FREE_GAMES, MC.SPIN_COUNTER]
}


def def_value():
    return 0


class MyStakeOptions:
    @property
    def selection(self):
        return {
            "Line Credits": GV.CTC,
            "Bet Multiplier": GV.BET_MULTIPLIER,
            "Ante": GV.ANTE,
        }


def play_specific(excel_data_dict, gameparts, play_id = 0):
    scepterInfoBlockList = []
    GV.EXECUTION_LIST = [[BN.BASEGAME, {}]]
    GV.DRAWGAME_LIST = []
    total_credit_win = 0
    while GV.EXECUTION_LIST:
        scene, parameters = GV.EXECUTION_LIST.pop(-1)
        parameters["data"] = excel_data_dict
        sib = gameparts[scene].play(
            playmode="SIM", parameters=parameters, stake_options=MyStakeOptions(), speed_up_sim=True
        )
        for si in sib.scepterinfos:
            if "WIN_EVALUATION" in si.types and si.info["credit_win"]:
                total_credit_win += si.info["credit_win"]
        scepterInfoBlockList.append(sib)
    GV.DRAWGAME_LIST.append(total_credit_win)
    if not total_credit_win:
        GV.OUTCOMES_DICT[0].append(GV.DRAWGAME_LIST)
    else:
        GV.OUTCOMES_DICT[play_id + 10_000] = GV.DRAWGAME_LIST
    return scepterInfoBlockList, total_credit_win


def play_batch(batch_id, excel_data_dict, gameparts):
    GV.SYMBOLS = excel_data_dict["symbols"]
    GV.STE = excel_data_dict["ste"]
    GV.ETS = excel_data_dict["ets"]
    total_bet = GV.CTC * GV.BET_MULTIPLIER + GV.ANTE
    list_of_sibl = []
    game_event_log = defaultdict(def_value)
    total_credit_wins = []
    for play_idx in range(GV.BATCH_SIZE):
        game_event_log_single_play = defaultdict(def_value)
        sibl, total_credit_win = play_specific(excel_data_dict, gameparts, play_id=play_idx + batch_id * GV.BATCH_SIZE)
        list_of_sibl.append(sibl)
        total_credit_wins.append(total_credit_win)
        if total_credit_win:
            game_event_log_single_play[f"SE_any_win"] += 1
            for pay_range in excel_data_dict["pay_distribution_values"]:
                r1 = pay_range[0] if pay_range[0] < 1 else int(pay_range[0])
                r2 = pay_range[1] if pay_range[1] < 1 else int(pay_range[1])
                if r1 * total_bet < total_credit_win <= r2 * total_bet:
                    game_event_log_single_play[f"PD_{r1}_{r2}"] += total_credit_win
                    game_event_log_single_play[f"FQ_{r1}_{r2}"] += 1
                    break
            else:
                game_event_log_single_play[f"PD_{int(pay_range[-1])}+"] += total_credit_win
                game_event_log_single_play[f"FQ_{int(pay_range[-1])}+"] += 1
        for sib in sibl:
            for scepterInfo in sib.scepterinfos:
                if SIT.WIN_EVALUATION in scepterInfo.types and scepterInfo.info["credit_win"]:
                    game_event_log_single_play[f"CW_{scepterInfo.id}"] += scepterInfo.info["credit_win"]
                elif SIT.STATS_PAYLOAD in scepterInfo.types:
                    if scepterInfo.info["credit_win"]:
                        game_event_log_single_play[f"SC_{scepterInfo.id}"] += scepterInfo.info["credit_win"]
                    else:
                        game_event_log_single_play[f"SE_{scepterInfo.id}"] += 1
                elif SIT.GAME_SPECIFIC in scepterInfo.types:
                    game_event_log_single_play[f"AV_{scepterInfo.id}"] += scepterInfo.info["info_dict"]["value_to_track"]
                    game_event_log_single_play[f"NV_{scepterInfo.id}"] = 1 # number of values
                elif SIT.BONUS_TRIGGER in scepterInfo.types:
                    game_event_log_single_play[f"ON_{scepterInfo.id}"] = 1 # number of values
        for k, v in game_event_log_single_play.items():
            game_event_log[k] += v
                        
    batch_avg_cw = sum(total_credit_wins)/len(total_credit_wins)
    data_to_pickle = {
        "game_event_log": game_event_log,
        "standard_deviation": statistics.stdev(total_credit_wins),
        "batch_avg_cw": batch_avg_cw,
    }
    with open(f"batch_results\\{batch_id}.pkl", "wb") as f:
        pickle.dump(data_to_pickle, f)


def create_fsd(fsd_name):
    with open(f"outcomes_dict.pkl", "rb") as f:
        outcomes_dict = pickle.load(f)
    fsd_data = [
        [
            "Seed",
            "TotalPay",
            "BonusPay",
            "Bonus",
            "FreeSpins",
            "Progressive",
            "Category",
            "Freq",
            "ProgressiveBonus",
        ]
    ]
    fsd_data.append(["0", "0", "0", "0", "0", "0", "0", f"{100*len(outcomes_dict[0])}", "0"])
    for seed_idx in range(10_000, GV.NUM_OF_GAMES + 10_000):
        if seed_idx in outcomes_dict:
            total_credit_win = outcomes_dict[seed_idx][-1]
            if total_credit_win:
                fsd_data.append(
                    [
                        f"{seed_idx}",
                        f"{total_credit_win}",
                        "0",
                        "0",
                        "0",
                        "0",
                        "0",
                        "100",
                        "0",
                    ]
                )
    with open(fsd_name, "w", newline="") as csvfile:
        output_fsd = csv.writer(csvfile, delimiter=",")
        for row in fsd_data:
            output_fsd.writerow(row)
