import itertools
import multiprocessing as mp
import os
from collections import defaultdict

from global_variables import GlobalConfig as GV
import numpy as np
from global_variables import BonusNames as BN
from prototype_vibe.project_logic.project_logic import MyLogic
from run import meters, project_dashboard, scenes
from scepter.common.comm_event_loop_dispatcher import CommEventLoopDispatcher
from scepter.common.comm_objects import CommGfxLoadFromExcel
from scepter.communication_pipeline import CommunicationPipeline
from joblib import Parallel, delayed

mp.freeze_support()
from tqdm import tqdm


def calculate_reelstrip(excel_data_dict, node, base_idx):
    total_bet = GV.BET_MULTIPLIER * GV.CTC + GV.ANTE
    GV.STE = excel_data_dict["ste"]
    GV.ETS = excel_data_dict["ets"]
    GV.SYMBOLS = excel_data_dict["symbols"]
    line_shapes = excel_data_dict["line_shapes"]
    reelsets = excel_data_dict["reelsets"]
    weightsets = excel_data_dict["weightsets"]
    lookup = excel_data_dict["lookup"]
    lookup_flat = np.matrix.flatten(lookup)
    paytable_pays = excel_data_dict["paytable_pays"]
    reelset = reelsets[node][base_idx]
    weightset = weightsets[node][base_idx]
    # ANY LINE WIN PROB
    winning_stop_combinations_all = []
    average_lines_prob = 0.
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
                            average_lines_prob += weightset[0].probs[stop_idx_0] * weightset[1].probs[stop_idx_1] * weightset[2].probs[stop_idx_2]
    winning_stop_combinations_set = set(tuple(elem) for elem in winning_stop_combinations_all)
    num_winning_stop_combinations = len(winning_stop_combinations_set)
    probs = np.zeros((3, num_winning_stop_combinations))
    for comb_idx, comb in enumerate(winning_stop_combinations_set):
        for reel_idx, stop_idx in enumerate(comb):
            probs[reel_idx, comb_idx] = weightset[reel_idx].probs[stop_idx]
    any_line_win_prob = np.sum(np.prod(probs, axis=0))
    # LINE RTP
    possible_lines = np.array(list(itertools.product([GV.STE[sym] for sym in GV.SYMBOLS], repeat=GV.NUM_OF_REELS)))
    coords = tuple(possible_lines[:, reel_idx] for reel_idx in range(GV.NUM_OF_REELS))
    probs_per_combination_per_reel = np.zeros_like(possible_lines, dtype=np.float64)
    pays_per_combination = np.array([(GV.BET_MULTIPLIER * paytable_pays[w] if w != 255 else 0) for w in lookup_flat])
    rtp_base = 0
    for line_shape in line_shapes:
        prob_table = np.zeros((GV.NUM_OF_REELS, len(GV.SYMBOLS)))
        for reel_idx, reelband in enumerate(reelset):
            for stop_idx, stop in enumerate(reelband):
                sym = stop[line_shape[reel_idx]]
                # if GV.STE["_JOK_1_"] in stop: # only if expanding joker
                #     sym = GV.STE["_JOK_1_"]
                prob_table[reel_idx, sym] += weightset[reel_idx].probs[stop_idx]
            probs_per_combination_per_reel[:, reel_idx] = prob_table[reel_idx][coords[reel_idx]]
        probs_per_combination = np.prod(probs_per_combination_per_reel, axis=1)
        rtp_base += np.dot(probs_per_combination, pays_per_combination)
    rtp_base = rtp_base / total_bet
    # COINS
    coin_combinations = np.array(list(itertools.product(list(range(GV.REEL_HEIGHT+1)), repeat=GV.NUM_OF_REELS)))
    coin_prob_table = np.zeros((GV.NUM_OF_REELS, GV.REEL_HEIGHT+1))
    for reel_idx, reel in enumerate(reelset):
        for stop_idx, stop in enumerate(reel):
            num_coins_on_stop = np.count_nonzero(stop == GV.STE["_COI_1_"])
            coin_prob_table[reel_idx, num_coins_on_stop] += weightset[reel_idx].probs[stop_idx]
    num_coins_probs = {}
    for num_coins in range(GV.NUM_OF_REELS*GV.REEL_HEIGHT+1):
        num_coins_probs[num_coins] = 0
    for combination in coin_combinations:
        comb_prob = 1
        for reel_idx, num in enumerate(combination):
            comb_prob *= coin_prob_table[reel_idx, num]
        num_coins_probs[np.sum(combination)] += comb_prob
    # SCATTERS
    scatter_combinations = np.array(list(itertools.product([0, 1], repeat=GV.NUM_OF_REELS)))
    scatter_prob_table = np.zeros((GV.NUM_OF_REELS, 2))
    for reel_idx, reel in enumerate(reelset):
        for stop_idx, stop in enumerate(reel):
            num_scatters_on_stop = np.count_nonzero(stop == GV.STE["_SCA_1_"])
            scatter_prob_table[reel_idx, num_scatters_on_stop] += weightset[reel_idx].probs[stop_idx]
    num_scatters_probs = {}
    for num_scatters in range(GV.NUM_OF_REELS+1):
        num_scatters_probs[num_scatters] = 0
    for combination in scatter_combinations:
        comb_prob = 1
        for reel_idx, num in enumerate(combination):
            comb_prob *= scatter_prob_table[reel_idx, num]
        num_scatters_probs[np.sum(combination)] += comb_prob
            
    return rtp_base, num_coins_probs, num_scatters_probs, any_line_win_prob, average_lines_prob

def main():
    
    mylogic = MyLogic(meters=meters)

    comm_pipeline = CommunicationPipeline(
        CommEventLoopDispatcher(),
        CommEventLoopDispatcher(),
        play_logic=mylogic,
        scepterinfos_to_track={},
        project_name="Vibe Template Game",
        width=900,
        scenes=scenes,
        dashboard=project_dashboard,
    )

    comm_pipeline.core_communication_layer.playmode_handler.active_playmode.load_xls(load_xls_obj=CommGfxLoadFromExcel())

    excel_data_dict = comm_pipeline.core_communication_layer.playmode_handler.active_playmode.logic.data
    
    reelsets = excel_data_dict["reelsets"]
    base_weights = excel_data_dict["base_weights"]
    
    # CALCULATION
    
    # INPUTS
    inputs = [[], [], []]
    for node in reelsets:
        for base_idx, _ in enumerate(reelsets[node]) :
            # calculate_reelstrip(excel_data_dict, node, base_idx) # for debug
            inputs[0].append(excel_data_dict)
            inputs[1].append(node)
            inputs[2].append(base_idx)

    # CALCULATE BASES
    inputs_zip = zip(*inputs)
    if os.cpu_count() < 60:
        with mp.Pool(processes=int(os.cpu_count())) as pool:
            solutions = pool.starmap(
                calculate_reelstrip,
                inputs_zip,
                chunksize=1,
            )
    else:
        solutions = Parallel(n_jobs = -1)(
            delayed(calculate_reelstrip)(*inputs) for inputs in inputs_zip
        )

    
    # COLLECT RESULTS
    bg_rtp = 0
    fg_spin_rtp = 0
    has_bg_trig_prob = 0
    has_fg_trig_prob = 0
    bg_any_line_win_prob = 0
    fg_any_line_win_prob = 0
    bg_average_lines_prob = 0
    bg_scatter_probs = {k: 0. for k in range(GV.NUM_OF_REELS+1)}
    fg_scatter_probs = {k: 0. for k in range(GV.NUM_OF_REELS+1)}
    for (base_rtp, base_num_coins_probs, base_num_scatters_probs, base_any_line_win_prob, base_average_lines_prob), node, base_idx in zip(solutions, inputs[1], inputs[2]):
        base_prob = base_weights[node].probs[base_idx]
        if node == BN.BASEGAME:
            bg_rtp += base_prob * base_rtp
            for k in bg_scatter_probs:
                bg_scatter_probs[k] += base_prob * base_num_scatters_probs[k]
            has_bg_trig_prob += base_prob * sum([v for k, v in base_num_coins_probs.items() if k >= 6])
            bg_any_line_win_prob += base_prob * base_any_line_win_prob
            bg_average_lines_prob += base_prob * base_average_lines_prob
        elif node == BN.FREEGAME:
            fg_spin_rtp += base_prob * base_rtp
            for k in bg_scatter_probs:
                fg_scatter_probs[k] += base_prob * base_num_scatters_probs[k]
            has_fg_trig_prob += base_prob * sum([v for k, v in base_num_coins_probs.items() if k >= 6])
            fg_any_line_win_prob += base_prob * base_any_line_win_prob
            
    fg_trig_prob = sum([v for k, v in bg_scatter_probs.items() if k>=3])
    fg_retrig_prob = sum([v for k, v in fg_scatter_probs.items() if k>=3])
    
    # AVERAGE SPINS CALCULATION
    
    average_fg_spins = 0.
    for num_sca_bg, trigger_prob in bg_scatter_probs.items():
        if num_sca_bg >= 3:
            trigger_prob_internal = trigger_prob/fg_trig_prob
            average_fg_spins_internal = 5 / (1-5*fg_scatter_probs[3]-8*fg_scatter_probs[4]-10*fg_scatter_probs[5])
            average_fg_spins += average_fg_spins_internal * trigger_prob_internal
    
    # PRINT RESULTS
    
    print('bg_line_rtp', bg_rtp)
    print('fg_line_rtp', fg_trig_prob * average_fg_spins * fg_spin_rtp)
    print('fg_trig_prob', fg_trig_prob)
    print('has_bg_trig_prob', has_bg_trig_prob)
    print('fg_retrig_prob', fg_trig_prob * average_fg_spins * fg_retrig_prob)
    print('has_fg_trig_prob', fg_trig_prob * average_fg_spins * has_fg_trig_prob)
    print('average_fg_spins', average_fg_spins)
    print('bg_any_line_win_prob', bg_any_line_win_prob)
    print('fg_any_line_win_prob', fg_trig_prob * average_fg_spins * fg_any_line_win_prob)
    print('bg_num_average_lines', bg_average_lines_prob/bg_any_line_win_prob)
    

if __name__ == "__main__":
    main()