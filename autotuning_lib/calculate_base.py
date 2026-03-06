import itertools
import multiprocessing as mp
from collections import defaultdict

import global_variables as GV
import numpy as np

import csv
import pandas as pd

mp.freeze_support()
from tqdm import tqdm

NUM_WEIGHTSTRIPS = 5
CHANGE_AMOUNT = 0.05

DESIRED_OUTCOMES_VALUES = {
    "line_rtp": 0.5,
    "any_line_win_prob": 0.3,
}
DESIRED_OUTCOMES_FACTORS = {
    "line_rtp": 1.,
    "any_line_win_prob": 1.,
}

def write_result(weightstrips):
    big_matrix = np.vstack(np.array(weightstrips)).T
    big_matrix = big_matrix * 1_000_000_000
    big_matrix = np.array(big_matrix, dtype=np.uint32)
    pd.DataFrame(big_matrix).to_excel("weights.xlsx", sheet_name="ATT", header=None, index=False, engine="openpyxl")

def overall_calculation(calculations):
    overall_calculation = {}
    for calculation in calculations:
        for key, value in calculation.items():
            if key in overall_calculation:
                overall_calculation[key] = overall_calculation[key] + value
            else:
                overall_calculation[key] = value
    for key, value in overall_calculation.items():
        overall_calculation[key] = value/NUM_WEIGHTSTRIPS
    return overall_calculation

def return_better_desirability(base_idx, excel_data_dict, step_calculation, step_desirability, change, reelstrip, at_weightstrips):
    reel_idx, row_idx = change
    weightstrip_to_change = at_weightstrips[base_idx]
    weightstrip_to_change[reel_idx, row_idx] = weightstrip_to_change[reel_idx, row_idx] * (1 + CHANGE_AMOUNT)
    weightstrip_to_change[reel_idx] = weightstrip_to_change[reel_idx] / np.sum(weightstrip_to_change[reel_idx])
    step_calculation[base_idx] = calculate_reelstrip_at(excel_data_dict, reelstrip, weightstrip_to_change)
    new_desirability = calculate_desirability(step_calculation)
    if new_desirability < step_desirability:
        return (change, CHANGE_AMOUNT)
    return (change, -CHANGE_AMOUNT)
    

def calculate_desirability(calculations):
    outcomes = overall_calculation(calculations)
    desirability_factor = 0
    for key, calculated_value in outcomes.items():
        factor = DESIRED_OUTCOMES_FACTORS[key]
        desired_value = DESIRED_OUTCOMES_VALUES[key]
        desirability_factor += factor * ((abs(calculated_value - desired_value)) / desired_value)**2

    return desirability_factor

def calculate_reelstrip_at(excel_data_dict, reelset, weightset):
    for reel_idx, reel_weights in enumerate(weightset):
        weightset[reel_idx] = reel_weights/np.sum(reel_weights)
    total_bet = GV.BET_MULTIPLIER * GV.CTC + GV.ANTE
    GV.STE = excel_data_dict["ste"]
    GV.ETS = excel_data_dict["ets"]
    GV.SYMBOLS = excel_data_dict["symbols"]
    line_shapes = excel_data_dict["line_shapes"]
    lookup = excel_data_dict["lookup"]
    lookup_flat = np.matrix.flatten(lookup)
    paytable_pays = excel_data_dict["paytable_pays"]
    # ANY LINE WIN PROB
    winning_stop_combinations_all = []
    for line_shape in line_shapes:
        for stop_idx_0, stop_0 in enumerate(reelset[0]):
            for stop_idx_1, stop_1 in enumerate(reelset[1]):
                sym_0 = stop_0[line_shape[0]]
                sym_1 = stop_1[line_shape[1]]
                if sym_0==sym_1 or GV.STE["_JOK_1_"] in [sym_0, sym_1]:
                    for stop_idx_2, stop_2 in enumerate(reelset[2]):
                        sym_2 = stop_2[line_shape[2]]
                        if lookup[sym_0, sym_1, sym_2, GV.STE["_BLN_1_"], GV.STE["_BLN_1_"]] != 255:
                            winning_stop_combinations_all.append([stop_idx_0, stop_idx_1, stop_idx_2])
    winning_stop_combinations_set = set(tuple(elem) for elem in winning_stop_combinations_all)
    num_winning_stop_combinations = len(winning_stop_combinations_set)
    probs = np.zeros((3, num_winning_stop_combinations))
    for comb_idx, comb in enumerate(winning_stop_combinations_set):
        for reel_idx, stop_idx in enumerate(comb):
            probs[reel_idx, comb_idx] = weightset[reel_idx][stop_idx]
    any_line_win_prob = np.sum(np.prod(probs, axis=0))
    # LINE RTP
    possible_lines = np.array(list(itertools.product([GV.STE[sym] for sym in GV.SYMBOLS], repeat=GV.NUM_OF_REELS)))
    coords = tuple(possible_lines[:, reel_idx] for reel_idx in range(GV.NUM_OF_REELS))
    probs_per_combination_per_reel = np.zeros_like(possible_lines, dtype=np.float64)
    pays_per_combination = np.array([(paytable_pays[w] if w != 255 else 0) for w in lookup_flat])
    line_rtp = 0
    for line_shape in line_shapes:
        prob_table = np.zeros((GV.NUM_OF_REELS, len(GV.SYMBOLS)))
        for reel_idx, reelband in enumerate(reelset):
            for stop_idx, stop in enumerate(reelband):
                sym = stop[line_shape[reel_idx]]
                prob_table[reel_idx, sym] += weightset[reel_idx][stop_idx]
            probs_per_combination_per_reel[:, reel_idx] = prob_table[reel_idx][coords[reel_idx]]
        probs_per_combination = np.prod(probs_per_combination_per_reel, axis=1)
        line_rtp += np.dot(probs_per_combination, pays_per_combination)
    line_rtp = line_rtp / total_bet

    return {"line_rtp": line_rtp, "any_line_win_prob": any_line_win_prob}
