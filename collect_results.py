import multiprocessing as mp
import os
import pickle
import sys
from collections import defaultdict

from global_variables import GlobalConfig as GV
import prototype_installer_config

mp.freeze_support()
import math
from tkinter import Tk, filedialog

assert prototype_installer_config, "installer_config imported for execution"
import csv


def def_value():
    return 0

def browse(root_directory):
    root = Tk()
    root.withdraw()
    pth = filedialog.askopenfilename(
        initialdir=root_directory,
        title="Math Excel File",
        filetypes=(("xls files", ".xls*"),),
    )
    del root
    return pth


def collect_results(excel_path):
    # try:
    #     sys.argv[1]
    #     GV.NUM_OF_GAMES = int(sys.argv[1])
    # except:
    #     GV.NUM_OF_GAMES = 1_000_000
    GV.NUM_OF_BATCHES = int(GV.NUM_OF_GAMES / GV.BATCH_SIZE) 
    
    total_bet = GV.BET_MULTIPLIER * GV.CTC + GV.ANTE

    # RESULT COLLECTION

    batch_avg_cws, standard_deviations = [], []
    game_event_log = defaultdict(def_value)
    for batch_id in range(GV.NUM_OF_BATCHES):
        with open(f"batch_results\\{batch_id}.pkl", "rb") as input_file:
            pickled_batch_result = pickle.load(input_file)
            for key, value in pickled_batch_result["game_event_log"].items():
                game_event_log[key] += value
            batch_avg_cws.append(pickled_batch_result["batch_avg_cw"])
            standard_deviations.append(pickled_batch_result["standard_deviation"])
    
    avg_cw = sum(batch_avg_cws)/len(batch_avg_cws)
    sigma_squared = 0
    for batch_avg_cw, batch_sigma in zip(batch_avg_cws, standard_deviations):
        sigma_squared += (batch_sigma**2 + batch_avg_cw**2) / GV.NUM_OF_BATCHES
    sigma_squared -= avg_cw
    plus_minus = 1.959963985 * math.sqrt(sigma_squared) / total_bet / math.sqrt(GV.NUM_OF_GAMES)
    
    output_list = []
    output_list.append([f"GAMES_PLAYED", f"{GV.NUM_OF_GAMES}"])
    output_list.append([f"BET_MULTIPLIER", f"{GV.BET_MULTIPLIER}"])
    output_list.append([f"plus_minus_rtp", f"{plus_minus}"])
    output_list.append([f"volatility", f"{math.sqrt(sigma_squared) / total_bet}"])
    output_list.append(["scepterinfo_idx", "scepterinfo_names", "scepterinfo_type", "values"])
    for i, k in enumerate(sorted(game_event_log.keys())):
        if k[0:2] == "CW":
            output_list.append([f"{i}", f"{k[3:]}", "CREDIT_WIN", f"{round(100 * game_event_log[k] / GV.NUM_OF_GAMES / total_bet, 6)}%"])
        elif k[0:2] == "SC":
            output_list.append([f"{i}", f"{k[3:]}", "STATS_CREDIT", f"{round(100 * game_event_log[k] / GV.NUM_OF_GAMES / total_bet, 6)}%"])
        elif k[0:2] == "SE":
            output_list.append([f"{i}", f"{k[3:]}", "HIT_RATIO", f"{GV.NUM_OF_GAMES / game_event_log[k]}"])
        elif k[0:2] == "PD":
            output_list.append([f"{i}", f"{k}", "PAY_DISTRIBUTION", f"{round(100 * (game_event_log[k]) / GV.NUM_OF_GAMES / total_bet, 6)}%"])
        elif k[0:2] == "FQ":
            output_list.append([f"{i}", f"{k}", "PAY_FREQUENCY", f"{GV.NUM_OF_GAMES / game_event_log[k]}"])
        elif k[0:2] == "AV":
            average_value = game_event_log[k]
            num_events = game_event_log[f"NV{k[2:]}"]
            output_list.append([f"{i}", f"{k[3:]}", "AVERAGE_VALUE", f"{average_value/num_events}"])
        elif k[0:2] == "ON":
            output_list.append([f"{i}", f"{k[3:]}", "BONUS_TRIGGER", f"{GV.NUM_OF_GAMES / game_event_log[k]}"])
        elif k[0:2] != "NV":
            print("wierd")    
    
    excel_directory = os.path.dirname(os.path.abspath(excel_path))
    with open(os.path.join(excel_directory, "sim_results.csv"), "w", newline='') as csvfile:
        output= csv.writer(csvfile, delimiter=",")
        for row in output_list:
            output.writerow(row)

if __name__ == "__main__":
    excel_path = browse(os.getcwd())
    collect_results(excel_path)
