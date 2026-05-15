import csv
import hashlib
import itertools
import json
import multiprocessing as mp
import os
import pickle
import random
import shutil
from functools import cache
from os import makedirs, path

from joblib import Parallel, delayed

mp.freeze_support()

import time
from copy import deepcopy

from global_variables import GlobalConfig as GV
import numpy as np
import pyglet
from global_variables import BonusNames as BN
from PIL import Image
from scepter.common.constants import MeterConstants as MC
from scepter.common.constants import ScepterInfoInfo as SII
from scepter.common.constants import ScepterInfoType as SIT
from scepter.core.logic.logic import Logic
from scepter.core.logic.scepterinfo import ScepterInfo, ScepterInfoBlock
from scepter.core.logic.stake_options import StakeOptions
from scepter.get_root_path import get_project_gfx_source_path
from scepter.library.excom.constants import DataTypes as DT
from scepter.library.mathlib.paytable import Paytable
from tqdm import tqdm
from scepter.core.playmodes.playmode_ids import PlaymodeId
from .basegamelogic import BaseGameLogic
from .freegamelogic import FreeGameLogic
from .gamepartlogic_template import DrawGame
from .holdandspinlogic import HoldAndSpinLogic
from .wheellogic import WheelLogic
from scepter.library.excom.excel_io_mode import EXCEL_DATA_EXTRACTOR_CLASS_BY_MODE
import scepter.game_config


def load_pyglet_images(folder):
    folder_path = os.path.join(get_project_gfx_source_path(), folder)
    pictures = os.listdir(folder_path)
    for picture in pictures:
        picture_path = os.path.join(folder_path, picture)
        image = pyglet.image.load(picture_path)
        image.anchor_x = image.width // 2
        image.anchor_y = image.height // 2
        GV.PYGLET_IMAGES[picture[:-4]] = image
        GV.PYGLET_ANIMATION_IMAGES[picture[:-4]] = []
        # MINIREELS
        if folder == "symbols" and picture[:-4] in ["_COI_1_", "_BLN_1_", "_BLN_2_", ]:
            print("creating minireels for ", picture[:-4])
            in_array = np.array(Image.open(picture_path))
            h, w, d = np.shape(in_array)
            num_frames = int(2 * GV.OM["MINIREELS_SPEED"] * GV.OM["FRAMERATE"] - 1)
            for split_idx in range(num_frames+1):
                percentage = split_idx/num_frames
                out_array = np.copy((in_array))
                region_pointer_idx = int(2 * percentage * h)
                out_array = np.roll(out_array, region_pointer_idx, axis=0)
                out_array[region_pointer_idx:, :, :] = 0
                if percentage < 0.5:
                    out_array[region_pointer_idx:, :, :] = 0
                else:
                    out_array[0: region_pointer_idx-h, :, :] = 0
                img = Image.fromarray(np.uint8(out_array)).convert('RGBA')
                temp_path = os.path.join(get_project_gfx_source_path(), "temp.png")
                img.save(temp_path)
                image = pyglet.image.load(temp_path)
                image.anchor_x = image.width // 2
                image.anchor_y = image.height // 2
                GV.PYGLET_ANIMATION_IMAGES[picture[:-4]].append(image)
                pass

class MyStakeOptions(StakeOptions):
    @property
    def selected_total_bet(self):
        return self.selection["Line Credits"] * self.selection["Bet Multiplier"] + self.selection["Ante"]

def lookup_for_symbol(symbol, excel_data_dict):
    symbols = excel_data_dict["symbols"]
    ste = excel_data_dict["ste"]
    paytable_symbols = excel_data_dict["paytable_symbols"]
    paytable_lengths = excel_data_dict["paytable_lengths"]
    possible_lines = np.array(list(itertools.product([ste[sym] for sym in symbols], repeat=GV.NUM_OF_REELS-1)))
    first_column = np.array([ste[symbol] for _ in possible_lines])
    all_possible_lines = np.vstack((first_column, possible_lines.T)).T
    pays = np.zeros((np.shape(all_possible_lines)[0]))
    for idx, line in enumerate(all_possible_lines):
        pays[idx] = evaluate_line(line, paytable_symbols, paytable_lengths, ste)
    result_shape = []
    for _ in range(GV.NUM_OF_REELS-1):
        result_shape.append(len(symbols))
    result_shape = tuple(result_shape)
    lookup_part = pays.reshape(result_shape)  # from results to lookup_part
    lookup_part = lookup_part.astype(np.uint8)  # convert to uint8 to save on memory
    return (symbol, lookup_part)

def evaluate_line(line_symbols, paytable_symbols, paytable_lengths, ste):
    for pay_index, (symbol, length) in enumerate(zip(paytable_symbols, paytable_lengths)):
        for reel_idx, line_symbol in enumerate(line_symbols):
            if line_symbol not in [ste[symbol], ste["_JOK_1_"]] and reel_idx < length:
                break
        else:
            return int(pay_index)
    return 255

class MyLogic(Logic):
    def __init__(self, meters={}):
        super().__init__(meters=meters, stake_options=MyStakeOptions())
        self.gameparts = {
            BN.BASEGAME: BaseGameLogic(meters=meters),
            BN.FREEGAME: FreeGameLogic(meters=meters),
            BN.HOLDANDSPIN: HoldAndSpinLogic(meters=meters),
            BN.WHEEL: WheelLogic(meters=meters),
        }
        GV.my_logic = self
        self.xls_object = None
        self.excel_hash = None

    def get_stake_options(self):
        return self.stake_options.selection

    def update_on_stake_change(self):
        return

    def prepare_reset_state(self):
        state = {}
        return state

    def reset_progressives(self):
        pass

    @cache
    def load_reelstrip(self, sheet_name, coordinate):
        self.xls_object.select_sheet(sheet_name)
        reels = self.xls_object.extract_from_consecutive_columns(DT.STRING, coordinate)
        reels_enum = []
        for reel_idx, reel in enumerate(reels):
            reels_enum.append([GV.STE[s] for s in reel])
        return reels, reels_enum
    
    def load_sounds(self):
        GV.SOUNDS_DICT = {}
        sounds_folder_path = os.path.join(get_project_gfx_source_path(), "sounds")
        sounds = os.listdir(sounds_folder_path)
        for sound in sounds:
            GV.SOUNDS_DICT[sound[:-4]] = pyglet.media.load(os.path.join(sounds_folder_path, f"{sound}"))

    def load_game_data(self):
        
        if GV.ALWAYS_RELOAD_EXCEL==False:
            print("hash is different, loading excel data ...")
        
        # PAY DISTRIBUTION RANGES
        print("Pay Distribution")
        self.xls_object.select_sheet("ScepterInput")
        distribution_ranges = self.xls_object.extract_from_column(DT.FLOAT, "B5")
        pay_distribution_values = list(zip(distribution_ranges[:-1], distribution_ranges[1:]))
        
        # # LINES
        # print("Lines")
        # self.xls_object.select_sheet("Lines")
        # paylines = np.array(self.xls_object.extract_from_consecutive_rows(DT.INTEGER, "C3"))

        # PAYTABLE
        print("Paytable")
        paytable = Paytable()
        paytable.initialize_from_excel(self.xls_object, "Paytable", "C7")

        # REELS AND WEIGHTS
        reelsets = {}
        reelsets_enum = {}
        weightsets = {}
        base_weights = {}
        for coord, bonus in zip(["K5", "P5"], [BN.BASEGAME, BN.FREEGAME]):
            reelsets[bonus], weightsets[bonus],reelsets_enum[bonus] = [], [], []
            self.xls_object.select_sheet("ScepterInput")
            table = self.xls_object.extract_from_consecutive_rows(DT.STRING, coord)
            base_weights[bonus] = []
            for row in table:
                (sheet_name, weight, sector_coord, weight_coord) = row
                print(f"reelstrip {sector_coord} \t weightstrip {weight_coord}")
                base_weights[bonus].append(int(float(weight)))
                reels,reels_enum = self.load_reelstrip(sheet_name, sector_coord)
                reelsets_enum[bonus].append(reels_enum)
                reelsets[bonus].append(reels)
                self.xls_object.select_sheet(sheet_name)
                weightsets[bonus].append(
                    [DrawGame(w) for w in self.xls_object.extract_from_consecutive_columns(DT.INTEGER, weight_coord)]
                )
            base_weights[bonus] = DrawGame(base_weights[bonus])

        self.xls_object.select_sheet("BG_DRAW")
        reelset_selection = DrawGame(
            weights = self.xls_object.extract_from_column(DT.INTEGER, "C3")
        )

        self.xls_object.select_sheet("FG_FEAT")
        random_wild_table = DrawGame(
            weights = self.xls_object.extract_from_column(DT.INTEGER, "B3"),
            results = self.xls_object.extract_from_column(DT.STRING, "A3"),
        )

        self.xls_object.select_sheet("HaS")
        coins_bg_fg = DrawGame(
            weights = self.xls_object.extract_from_column(DT.INTEGER, "C26"),
            results = self.xls_object.extract_from_column(DT.STRING, "B26"),
        )
        coins_has = DrawGame(
            weights = self.xls_object.extract_from_column(DT.INTEGER, "C3"),
            results = self.xls_object.extract_from_column(DT.INTEGER, "B3"),
        )
        num_new_coins_drawn_dg = [DrawGame(w) for w in self.xls_object.extract_from_consecutive_columns(DT.INTEGER, "G3")]
        num_spins_dg = [DrawGame(w, self.xls_object.extract_from_column(DT.INTEGER, "F21")) for w in self.xls_object.extract_from_consecutive_columns(DT.INTEGER, "G21")]

        pp_trigger_bg = [DrawGame(w) for w in self.xls_object.extract_from_consecutive_rows(DT.INTEGER, "R3")]
        #dodatak za fg
        pp_trigger_fg = [DrawGame(w) for w in self.xls_object.extract_from_consecutive_rows(DT.INTEGER, "V3")]

        # MODE SELECTOR
        feat_mode_selector = DrawGame(
            weights=self.xls_object.extract_from_column(DT.INTEGER, "R38"),
            results=self.xls_object.extract_from_column(DT.INTEGER, "Q38"),
        )

        # STOPPER SELECTOR
        stopper_selector = DrawGame(
            weights=self.xls_object.extract_from_column(DT.INTEGER, "U39"),
            results=self.xls_object.extract_from_column(DT.INTEGER, "T39"),
        )

        # TABLE 1
        hns_table_1_values = self.xls_object.extract_from_column(DT.INTEGER, "Q14")
        hns_table_1 = [
            DrawGame(w, hns_table_1_values)
            for w in self.xls_object.extract_from_consecutive_columns(DT.INTEGER, "R14")
        ]

        # TABLE 2
        hns_table_2_values = self.xls_object.extract_from_column(DT.INTEGER, "X14")
        hns_table_2 = [
            DrawGame(w, hns_table_2_values)
            for w in self.xls_object.extract_from_consecutive_columns(DT.INTEGER, "Y14")
        ]

        #FEATURE TABLES
        feature_tables = {}

        interface_columns = ["Q", "V", "AA", "AF"]

        for mode_idx, row in enumerate([48, 58, 68, 78], start=1):
            feature_tables[mode_idx] = {}

            for interface_idx, col in enumerate(interface_columns, start=1):
                coord = f"{col}{row}"
                table = self.xls_object.extract_from_consecutive_rows(DT.INTEGER, coord)
                rs_ids = []
                ws0 = []
                ws1 = []
                ws2 = []

                for row_data in table:
                    rs_id = row_data[0]
                    weight0 = row_data[1]
                    weight1 = row_data[2]
                    weight2 = row_data[3]

                    rs_ids.append(rs_id)
                    ws0.append(weight0)
                    ws1.append(weight1)
                    ws2.append(weight2)

                feature_tables[mode_idx][interface_idx] = {
                    0: DrawGame(ws0, rs_ids),
                    1: DrawGame(ws1, rs_ids),
                    2: DrawGame(ws2, rs_ids),
                }

        #RS
        rs_tables = {}
        columns = [
            ("Q", "R"),
            ("T", "U"),
            ("W", "X"),
            ("Z", "AA"),
            ("AC", "AD"),
            ("AF", "AG"),
            ("AI", "AJ"),
            ("AL", "AM"),
        ]
        start_row = 88
        for rs_id, (sym_col, weight_col) in enumerate(columns, start=1):
            symbols = self.xls_object.extract_from_column(DT.STRING, f"{sym_col}{start_row}")
            weights = self.xls_object.extract_from_column(DT.INTEGER, f"{weight_col}{start_row}")
            rs_tables[rs_id] = DrawGame(weights, symbols)


        #WHEEL VALUES and WEIGHTS
        self.xls_object.select_sheet("Wheel")
        wheel_wedges = DrawGame(
            weights = self.xls_object.extract_from_column(DT.INTEGER, "E4"),
            results = self.xls_object.extract_from_column(DT.INTEGER, "B4"),
        )

        # EXCEL DATA
        self.data = {
            "symbols": GV.SYMBOLS,
            "ets": GV.ETS,
            "ste": GV.STE,
            "pay_distribution_values": pay_distribution_values,
            #"paylines": paylines,
            "reelsets": reelsets,
            "reelsets_enum": reelsets_enum,
            "weightsets": weightsets,
            "base_weights": base_weights,
            "paytable": paytable,
            "coins_bg_fg": coins_bg_fg,
            "coins_has": coins_has,
            "num_new_coins_drawn_dg": num_new_coins_drawn_dg,
            "num_spins_dg": num_spins_dg,
            "wheel_wedges": wheel_wedges,
            "pp_trigger_bg": pp_trigger_bg,
            "pp_trigger_fg": pp_trigger_fg,
            "reelset_selection": reelset_selection,
            "feat_mode_selector": feat_mode_selector,
            "stopper_selector": stopper_selector,
            "hns_table_1": hns_table_1,
            "hns_table_2": hns_table_2,
            "feature_tables": feature_tables,
            "rs_tables": rs_tables,
            "random_wild_table": random_wild_table,
        }

        # EXCEL DATA PICKLE
        with open(f"excel_pickle.pkl", "wb") as f:
            pickle.dump({"hash": self.excel_hash, "data": self.data}, f)
    
    def load_from_xls(self, xls_path):
        
        # SOUNDS
        self.load_sounds()
            
        # OVERRIDE MENU
        GV.OM = json.load(open(path.join(get_project_gfx_source_path(), "constants.json"))) # override menu - timing constants and framerate
        
        # SYMBOL WIDTHS
        GV.SYMBOL_WIDTH = json.load(open(path.join(get_project_gfx_source_path(), "symbol_width.json")))
        
        if GV.MACHINE_BUILD:
            print("machine build ...")
            with open(f"excel_pickle.pkl", "rb") as f:
                data_dict = pickle.load(f)
                
            self.data = data_dict["data"]

            GV.SYMBOLS = self.data["symbols"]
            GV.STE = self.data["ste"]
            GV.ETS = self.data["ets"]
                
            stakes_raw_data = [('Line Credits', 'Bet Multiplier', "Ante"), (f"{GV.CTC}", f"{GV.BET_MULTIPLIER}", f"{GV.ANTE}")]
            self.stake_options.extract_from_raw_data(stakes_raw_data)
            
        else:
            self.excel_path = xls_path
            self.xls_object = EXCEL_DATA_EXTRACTOR_CLASS_BY_MODE[scepter.game_config.GAME_CONFIG.excel_io]()
            self.xls_object.open_workbook(xls_path)
            
            self.xls_object.select_sheet("ScepterInput")
            symbols = self.xls_object.extract_from_column(DT.STRING, "I5")
            if "_BLN_1_" not in symbols:
                symbols.append("_BLN_1_")
            if "_BLN_2_" not in symbols:
                symbols.append("_BLN_2_")
            ets, ste = {}, {}
            for i, sym in enumerate(symbols):
                ets[i] = sym
                ste[sym] = i
            GV.SYMBOLS = symbols
            GV.STE = ste
            GV.ETS = ets
            
            # PRIZE FIRST
        
            self.fsd_data = {}
            if GV.PRIZE_FIRST:
                with open(f"Template_Final_Seed_Data_L25C1TB25.csv", "r") as csvf:
                    reader = csv.reader(csvf, delimiter=",", quotechar='"')
                    fsd_data = [row for row in reader]
                seeds = [int(row[0]) for row in fsd_data[1:]]
                freqs = [int(row[7]) for row in fsd_data[1:]]
                pays =  [int(row[1]) for row in fsd_data[1:]]
                self.fsd_data = {
                    "seeds": seeds,
                    "freqs": DrawGame(freqs),
                    "pays": pays,
                }

            # STAKES

            self.xls_object.select_sheet("ScepterInput")
            stakes_raw_data = list(zip(*self.xls_object.extract_from_columns(DT.STRING, ["D4", "E4", "F4"])))
            self.stake_options.extract_from_raw_data(stakes_raw_data)

            if GV.ALWAYS_RELOAD_EXCEL:
                self.load_game_data()
            else:

                # EXCEL HASH LOGIC
                BUF_SIZE = 2**16
                sha256 = hashlib.sha256()
                with open(self.excel_path, 'rb') as f:
                    while True:
                        data = f.read(BUF_SIZE)
                        if not data:
                            break
                        sha256.update(data)
                self.excel_hash = sha256.hexdigest()
                print("excel_hash")
                print(self.excel_hash)

                try:
                    with open(f"excel_pickle.pkl", "rb") as f:
                        dict = pickle.load(f)
                        hash_file = dict["hash"]
                        if hash_file==self.excel_hash:
                            print("hash is the same, skipping excel loading ...")
                            self.data = dict["data"]
                        else:
                            self.load_game_data()
                except:
                    self.load_game_data()
                
        # PICTURES
        
        GV.PYGLET_IMAGES = {}
        GV.PYGLET_ANIMATION_IMAGES = {}
        load_pyglet_images("symbols")
        load_pyglet_images("backgrounds")
        load_pyglet_images("grid_frames")    
        
        # FINAL
        
        for gamepart in self.gameparts:
            self.gameparts[gamepart].datafields = [k for k in self.data]
            self.gameparts[gamepart].data = self.data   
         
        print("... excel data is loaded !\n")

    def play_specific(self, playmode=None):
        #GV.RANDOM_SEED = np.random.randint(low=0, high=2**31-1)
        #print(GV.RANDOM_SEED)
        #random.seed(GV.RANDOM_SEED)
        data = self.data
        scepterInfoBlockList = []
        if GV.PRIZE_FIRST:
            outcome_idx = self.fsd_data["freqs"].draw_random_non_outcome()
            outcome = self.fsd_data["seeds"][outcome_idx]
            if not outcome:
                GV.DRAWGAME_LIST = deepcopy(random.choice(GV.OUTCOMES_DICT[0]))
            else:
                GV.DRAWGAME_LIST = deepcopy(GV.OUTCOMES_DICT[outcome])
            if int(self.fsd_data["pays"][outcome_idx]) != GV.DRAWGAME_LIST[-1]:
                raise Exception("wrong pay!")

        speed_up_sim = False
        if playmode != PlaymodeId.NATURAL_PLAY:
            speed_up_sim = True #probaj sa F
        # MAIN LOGIC
        GV.EXECUTION_LIST = [[BN.BASEGAME, {}]]
        while GV.EXECUTION_LIST:
            scene, parameters = GV.EXECUTION_LIST.pop(0)
            parameters["data"] = data
            scepterInfoBlockList.append(
                self.gameparts[scene].play(
                    stake_options=self.stake_options,
                    playmode=playmode,
                    parameters=parameters,
                    speed_up_sim = False#speed_up_sim,
                )
            )
        # if self.meters[MC.WIN].value: # any win
        #     sib = ScepterInfoBlock(BN.BASEGAME)
        #     si = ScepterInfo(set([SIT.STATS_PAYLOAD]), f"any_win")
        #     si.add("credit_win", 0)
        #     sib.add_scepterinfo(si)
        #     scepterInfoBlockList.append(sib)

        # for sib in scepterInfoBlockList:
        #     print(sib.scene_name)
        #     for si in sib.scepterinfos:
        #         print(si.id)
        #     print("")

        return scepterInfoBlockList, False
