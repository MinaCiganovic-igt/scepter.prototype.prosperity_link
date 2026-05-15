import math
import random
from typing import Optional, Tuple

from global_variables import GlobalConfig as GV
import numpy as np
import pyglet
from global_variables import GroupConstants as GC
from scepter.common.constants import BatchTypes as BT
from scepter.common.constants import MeterConstants as MC
from scepter.gfx.accessories import colors as clrs
from scepter.gfx.grid.grid import Grid
from scepter.gfx.grid_object_manipulations.move_grid_objects import move_grid_objects
from scepter.gfx.scenes.scene import Scene
from scepter.gfx.grid_objects.grid_sprite import GridSprite
from ..project_gfx.scene_template import Grid_ID, SceneGamepartTemplate
from .scene_holdandspin_helpers import draw_counter_side, draw_top_counters, draw_locked_row_dimmers

BY = 0.06
TY = 0.3
LX = 0.0176
RX = 0.0178
CENTER_OFFSET = 0.5
CORNER_MARGIN = 0.25

class SceneHoldAndSpin(SceneGamepartTemplate):
    def __init__(self, **kwargs):
        super().__init__(
            height_to_width=2*1080/1920,
            **kwargs
        )
        self.grids.add(
            Grid_ID.MAIN.value,
            Grid(
                x_cells=GV.HNS_COLS,
                y_cells=GV.HNS_ROWS,
                left_cells=LX * GV.HNS_COLS / ( 1 - LX - RX ),
                right_cells=RX * GV.HNS_COLS / ( 1 - RX - LX ),
                bottom_cells=BY * GV.HNS_ROWS / ( 1 - BY - TY ),
                top_cells=TY * GV.HNS_ROWS / ( 1 - TY - BY ),
            ),
            grid_objects=self.grid_objects,
            batches=self.batches,
        )
        self.grids.add(
            Grid_ID.BCKG.value,
            Grid(
                left_cells=0,
                x_cells=1,
                right_cells=0,
                bottom_cells=0,
                y_cells=1,
                top_cells=0,
            ),
            grid_objects=self.grid_objects,
            batches=self.batches,
        )
        self.saved_scepterinfo = None
        GV.my_scenes["holdandspin"] = self

    def _cell_center(self, reel: int, row: int) -> Tuple[float, float]:
        """Return the centered cell coordinates used for drawing sprites/labels."""
        return (reel + CENTER_OFFSET, row + CENTER_OFFSET)
    # def _cell_center(self, reel: int, row: int):
    #     gap_size = 0.6  # razmak između grupa od 3 reda
    #     group = row // 3
    #     x = reel + CENTER_OFFSET
    #     y = row + CENTER_OFFSET + group * gap_size
    #     return (x, y)

    def initialize_visualization(self, meter_updater=None):
        self.previous_reelpicture = np.full((GV.HNS_COLS, GV.HNS_ROWS), GV.STE["_BLN_2_"])
        self.reels_to_spin = np.zeros_like(self.previous_reelpicture)
        self.batches.add((BT.BASE.value, "WIN_EVAL"))
        for reel_idx in range(GV.HNS_COLS):
            for row_idx in range(GV.HNS_ROWS):
                self.draw_sprite_centered_with_size(
                    grid_object_id=f"reels_back_has_{reel_idx}_{row_idx}",
                    sprite_name="reels_back_has",
                    position=self._cell_center(reel_idx, row_idx),
                    grid_id=Grid_ID.MAIN.value,
                    group=GC.REELS_BACK,
                    symbol_size=(1, 1),
                )
                self.draw_sprite_centered(
                    grid_object_id=f"reel_sym_{reel_idx}_{row_idx}",
                    sprite_name="_TOP_1_",
                    position=self._cell_center(reel_idx, row_idx),
                    grid_id=Grid_ID.MAIN.value,
                    group=GC.REEL_SYMBOLS,
                )
        self.load_the_dashboard()
        self.meter_updater = meter_updater
        meters_to_update = {"RANDOM_SEED": GV.RANDOM_SEED}
        self.meter_updater(meters_to_update)
        if GV.COUNTER_ON:
            #counters = GV.LRS_COUNTERS
            counters = [max(9-GV.TRIGGERING_MB,0),18-GV.TRIGGERING_MB,32-GV.TRIGGERING_MB]
            if counters:
                draw_counter_side(self, counters, side="right")

            print("Counters:", counters)
        #Draw Jackpot Pip Top Counters
        if GV.JACKPOT_PIPS_ON:
            draw_top_counters(self, GV.JACKPOT_PIPS_COUNTERS)
        if GV.TRIGGERING_MB >= 9:
            draw_locked_row_dimmers(self, [0,1,2,3,4,5])
        else:
            draw_locked_row_dimmers(self, [0,1,2,3,4,5,6,7,8])

    def create_symbols_to_spin(self, pos, first_element, last_element):
        reel_idx, row_idx = pos
        num_symbols_to_pass = round( GV.HNS_ROWS * reel_idx + row_idx + GV.OM["HOLDANDSPIN"] / GV.OM["MINIREELS_SPEED"])
        num_coins = 2
        symbols_to_spin = ["_BLN_2_" for _ in range(num_symbols_to_pass)]
        for sym_idx in range(num_coins):
            symbols_to_spin[sym_idx] = "_COI_1_"
        random.shuffle(symbols_to_spin)
        symbols_to_spin[-1] = last_element
        symbols_to_spin[0] = first_element
        return symbols_to_spin
    
    def start_visualization(self, scepterInfo):
        if "info_dict" in scepterInfo.info and "sound" in scepterInfo.info["info_dict"]:
            self.play_sound(0, scepterInfo.info["info_dict"]["sound"])
        handlers = {
            "refresh": self.__refresh,
            "spin_reels": self.__spin_reels,
            #"unlock": self.__unlock_intf,
        }
        handlers.get(scepterInfo.id, self.standard_scepterinfo)(scepterInfo)

    # def __unlock_intf(self, scepterInfo):
    #     dimmed = scepterInfo.info["info_dict"]["dimmed_reels"]
    #     self.grid_objects.delete(to_delete_sub_string="dimmer_")
    #     draw_locked_row_dimmers(self, dimmed)

    def __spin_reels(self, scepterInfo):
        self.reels_to_spin[:, :] = 1
        self.grid_objects.delete(to_delete_sub_string=f"spin_sym_")
        dimmed = scepterInfo.info["info_dict"]["dimmed_reels"]
        counters = scepterInfo.info["info_dict"]["counters"]

        # increment top counters each spin and redraw
        if not hasattr(self, "top_counters"):
            self.top_counters = [0] * 3
        if GV.JACKPOT_PIPS_ON:
            #ADD LOGIC FOR GV.JACKPOTS_PIPS_COUNTERS INCREMENT IF NEEDED
            #
            #
            #
            draw_top_counters(self, GV.JACKPOT_PIPS_COUNTERS)
        if GV.COUNTER_ON:
            counts = counters
            #mults = [int(x) + 1 for x in mults] #CHANGE THIS TO HOWEVER YOUR CODE SHOULD FUNCTION
            #GV.LRS_MULTIPLIERS = mults
            self.grid_objects.delete(to_delete_sub_string="count_")
            draw_counter_side(self, counts, side="right")

        reelpicture = scepterInfo.info["info_dict"]["reelpicture"]
        current_coinpicture = scepterInfo.info["info_dict"]["current_coinpicture"]
        places_to_spin = scepterInfo.info["info_dict"]["places_to_spin"]


        #print("SPIN POSITIONS: ", places_to_spin)
        for reel_idx, row_idx in places_to_spin:
            symbols_to_spin = self.create_symbols_to_spin(
                (reel_idx, row_idx), 
                first_element=GV.ETS[self.previous_reelpicture[reel_idx, row_idx]],
                last_element=reelpicture[reel_idx, row_idx]
                #last_element=GV.ETS[reelpicture[reel_idx, row_idx]]
            )
            time = 0
            pyglet.clock.schedule_once(
                self.__first_pass,
                self.timer.time_span(time),
                (reel_idx, row_idx),
                symbols_to_spin[0],
                0,
            )
            for sym_idx, symbol_to_spin in enumerate(symbols_to_spin[1:]):
                pyglet.clock.schedule_once(
                    self.__single_pass,
                    self.timer.time_span(time),
                    (reel_idx, row_idx),
                    symbol_to_spin,
                    sym_idx + 1,
                )
                time += GV.OM["MINIREELS_SPEED"]
            pyglet.clock.schedule_once(
                self.__draw_reel_sym,
                self.timer.time_span(time),
                (reel_idx, row_idx),
                reelpicture[reel_idx, row_idx],
                current_coinpicture[reel_idx, row_idx],
            )
        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            self.timer.time_span(round((GV.HNS_ROWS * (GV.HNS_COLS-1) + (GV.HNS_ROWS-1)) * GV.OM["MINIREELS_SPEED"] + GV.OM["HOLDANDSPIN"])),
            scepterInfo,
        )
        pyglet.clock.schedule_once(
            self.draw_locked_row_dimmers1,
            self.timer.time_span(round((GV.HNS_ROWS * (GV.HNS_COLS-1) + (GV.HNS_ROWS-1)) * GV.OM["MINIREELS_SPEED"] + GV.OM["HOLDANDSPIN"])),
            dimmed,
        )

    def draw_locked_row_dimmers1(self, dt, dimmed):
        self.grid_objects.delete(to_delete_sub_string="dimmer_")
        draw_locked_row_dimmers(self, dimmed)
    
    def __single_pass(self, dt, pos, symbol, sym_idx):
        reel_idx, row_idx = pos
        t = 0
        for frame, image in enumerate(GV.PYGLET_ANIMATION_IMAGES[symbol]):
            pyglet.clock.schedule_once(
                self.__draw_minireel_frame,
                self.timer.time_span(t),
                (reel_idx, row_idx),
                image,
                "_COI_1_",
                sym_idx,
                first_sprite = True if not frame else False
            )
            t += 1/GV.OM["FRAMERATE"]
    
    def __first_pass(self, dt, pos, symbol, sym_idx):
        reel_idx, row_idx = pos
        self.grid_objects.delete(to_delete_sub_string=f"reel_sym_{reel_idx}_{row_idx}")
        num_frames = int(2 * GV.OM["MINIREELS_SPEED"] * GV.OM["FRAMERATE"] - 1)
        t = 0
        for frame, image in enumerate(GV.PYGLET_ANIMATION_IMAGES[symbol]):
            if frame >= num_frames//2:
                pyglet.clock.schedule_once(
                    self.__draw_minireel_frame,
                    self.timer.time_span(t),
                    (reel_idx, row_idx),
                    image,
                    "_COI_1_",
                    sym_idx,
                    first_sprite = frame==num_frames//2
                )
                t += 1/GV.OM["FRAMERATE"]
                
    def __draw_minireel_frame(self, dt, pos, image, sym_name, sym_idx, first_sprite = False):
        reel_idx, row_idx = pos
        if self.previous_reelpicture[reel_idx, row_idx] != GV.STE["_BLN_2_"]:
            return
        if self.reels_to_spin[reel_idx, row_idx]:
            grid_object_id = f"spin_sym_{reel_idx}_{row_idx}_{sym_idx}"
            if first_sprite:
                grid = self.grids.get(Grid_ID.MAIN.value)
                r_x = pos[0] + 0.5
                r_y = grid.y_cells - pos[1] - CENTER_OFFSET
                self.grid_objects.delete(to_delete_sub_string=grid_object_id)
                self.grid_objects.add(
                    grid_object_id,
                    GridSprite(
                        r_x=r_x,
                        r_y=r_y,
                        r_width=GV.SYMBOL_WIDTH[sym_name][0],
                        r_height=GV.SYMBOL_WIDTH[sym_name][1],
                        pict=image,
                        whiteboard=self,
                        batch_id=BT.BASE.value,
                        group_idx=5,
                        grid_id=Grid_ID.MAIN.value,
                    ),
                )
            else:
                try:
                    obj = self.grid_objects.get(grid_object_id)
                    obj.image = image
                except:
                    return
    
    def __draw_reel_sym(self, dt, pos, sym, coin_value):
        reel_idx, row_idx = pos
        self.grid_objects.delete(to_delete_sub_string=f"spin_sym_{reel_idx}_{row_idx}")
        if sym != GV.STE["_BLN_2_"]:
            self.play_sound(0, f"reel_land_{reel_idx}")
        self.reels_to_spin[reel_idx, row_idx] = 0
        self.draw_sprite_centered(
            grid_object_id=f"reel_sym_{reel_idx}_{row_idx}",
            #sprite_name=GV.ETS[sym],
            sprite_name=sym,
            position=self._cell_center(reel_idx, row_idx),
            grid_id=Grid_ID.MAIN.value,
            group=GC.REEL_SYMBOLS,
        )
        if coin_value:
            self.draw_label_centered(
                grid_object_id=f"reel_label_{reel_idx}_{row_idx}",
                label=coin_value,
                position=self._cell_center(reel_idx, row_idx),
                grid_id=Grid_ID.MAIN.value,
                group=GC.REEL_LABELS,
            )


    
    
    def __refresh(self, scepterInfo):
        pyglet.clock.unschedule(self.__draw_minireel_frame)
        self.grid_objects.delete(to_delete_sub_string=f"spin_sym_")
        reelpicture = scepterInfo.info["info_dict"]["reelpicture"]
        current_coinpicture = scepterInfo.info["info_dict"]["current_coinpicture"]
        self.grid_objects.delete(to_delete_sub_string=f"reel_sym_")
        self.grid_objects.delete(to_delete_sub_string=f"reel_label_")
        for reel_idx, reel in enumerate(reelpicture):
            for row_idx, symbol in enumerate(reel):
                label = current_coinpicture[reel_idx, row_idx]
                self.draw_sprite_centered(
                    grid_object_id = f"reel_sym_{reel_idx}_{row_idx}",
                    sprite_name = symbol,
                    position = (reel_idx + 0.5, row_idx + 0.5),
                    grid_id = Grid_ID.MAIN.value,
                    group = GC.REEL_SYMBOLS
                )
                if label:
                    self.draw_label_centered(
                        grid_object_id = f"reel_label_{reel_idx}_{row_idx}",
                        label = label,
                        position= (reel_idx + 0.5, row_idx + 0.5),
                        grid_id=Grid_ID.MAIN.value,
                        group=GC.REEL_LABELS,
                    )
        self.prepare_settle_visualization(0, scepterInfo) 
