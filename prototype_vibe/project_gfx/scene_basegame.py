import math
import random
import pdb
import time

from global_variables import GlobalConfig as GV
import numpy as np
import pyglet
from global_variables import GroupConstants as GC
from scepter.common.constants import BatchTypes as BT
from scepter.common.constants import MeterConstants as MC
from scepter.gfx.accessories import colors as clrs
from scepter.gfx.grid.grid import Grid
from scepter.gfx.grid_object_manipulations.move_grid_objects import \
    move_grid_objects
from scepter.gfx.scenes.scene import Scene
import location_constants as LOCATIONS
from scepter.gfx.grid_objects.grid_label import GridLabel
from scepter.gfx.grid_objects.grid_sprite import GridSprite

from ..project_gfx.scene_template import Grid_ID, SceneGamepartTemplate

BY = 0.06
TY = 0.5
LX = 0.0176
RX = 0.0178
def set_credits(value):
    GV.idle_playmode.playmode_handler.play_logic.meters["credits"].set_value(
            value
        )
    GV.my_logic.meters["credits"].set_value(value)
    GV.meters["credits"] = value
def on_key_press(button, modifiers):
    
    my_basegame_scene = GV.my_scenes["basegame"]

    current_x = my_basegame_scene.current_window.get_location()[0]
    current_y = my_basegame_scene.current_window.get_location()[1]

    if button == 65460:
        my_basegame_scene.current_window.set_location(current_x-1, current_y)
    if button == 65461:
        my_basegame_scene.current_window.set_location(current_x, current_y + 1)
    if button == 65462:
        my_basegame_scene.current_window.set_location(current_x+1, current_y)
    if button == 65464:
        my_basegame_scene.current_window.set_location(current_x, current_y - 1)

    if button == 65463:
        # my_basegame_scene.current_window.width = 1080
        # my_basegame_scene.current_window.height = 1930
        set_credits(10000)
        

        pass
    if button == 65465:
        my_basegame_scene.current_window.width = 2160
        my_basegame_scene.current_window.height = 3860

class SceneBaseGame(SceneGamepartTemplate):
    def __init__(self, **kwargs):
        super().__init__(
            height_to_width=2*1080/1920,
            **kwargs
        )
        self.grids.add(
            Grid_ID.MAIN.value,
            Grid(
                x_cells=GV.NUM_OF_REELS,
                y_cells=GV.REEL_HEIGHT,
                left_cells=LX * GV.NUM_OF_REELS / ( 1 - LX - RX ),
                right_cells=RX * GV.NUM_OF_REELS / ( 1 - RX - LX ),
                bottom_cells=BY * GV.REEL_HEIGHT / ( 1 - BY - TY ),
                top_cells=TY * GV.REEL_HEIGHT / ( 1 - TY - BY ),
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

    def initialize_visualization(self, meter_updater=lambda: None):
        # initialize previous reel/coin buffers so spin logic can reference them
        self.previous_reelpicture = np.zeros((GV.NUM_OF_REELS, GV.REEL_HEIGHT), dtype=int)
        self.previous_reelpicture[:, :] = GV.STE["_BLN_1_"]
        self.previous_coinpicture = np.zeros_like(self.previous_reelpicture)
        self.previous_reelpicture_above = np.zeros((GV.NUM_OF_REELS,), dtype=int)
        self.previous_reelpicture_above[:] = GV.STE["_BLN_1_"]
        self.previous_coinpicture_above = np.zeros((GV.NUM_OF_REELS,), dtype=int)

        self.batches.add((BT.BASE.value, "WIN_EVAL"))
        self.draw_sprite_centered(
            grid_object_id = f"reels_back_bg",
            sprite_name = "reels_back_bg", 
            position=(0.5, 0.72),
            grid_id = Grid_ID.BCKG.value,
            group = GC.REELS_BACK
        )
        self.draw_sprite_centered(
            grid_object_id = f"reels_front",
            sprite_name = "reels_front", 
            position=(0.5, 0.72),
            grid_id = Grid_ID.BCKG.value,
            group = GC.REELS_FRONT
        )
        self.draw_sprite_centered(
            grid_object_id = f"bckg_top",
            sprite_name = "bckg_top", 
            position=(0.5, 0.25),
            grid_id = Grid_ID.BCKG.value,
            group = GC.TOP_SCREEN
        )
        for reel_idx in range(GV.NUM_OF_REELS):
            for row_idx in range(GV.REEL_HEIGHT):
                self.draw_sprite_centered(
                    grid_object_id = f"reel_sym_{reel_idx}_{row_idx}",
                    sprite_name = "_TOP_1_", 
                    position=(reel_idx + 0.5, row_idx + 0.5),
                    grid_id = Grid_ID.MAIN.value,
                    group = GC.REEL_SYMBOLS
                )

        self.create_pots()
        
        self.load_the_dashboard()
        active_windows = pyglet.app.windows
        #if self.current_window == "ERROR":
        #    if active_windows:
        #        self.current_window = next(iter(active_windows))
        #        self.current_window.push_handlers(on_key_press)
        pyglet.clock.schedule_once(
                self.draw_my_animation,
                0.1,
            )
        self.meter_updater = meter_updater
        meters_to_update = {MC.WIN: 0}
        self.meter_updater(meters_to_update)
    def draw_my_animation(self, dt):
        active_windows = pyglet.app.windows
        #if self.current_window == "ERROR":
        ##    if active_windows:
        #        self.current_window = next(iter(active_windows))
        #else:
         #   pass
            # temp_width = self.current_window.width
            # if temp_width % 100 != 0:
            #     temp_width += 100 - temp_width % 100
            # self.current_window.width = temp_width

        for meter in GV.meters:
            new_value = GV.meters[meter]
            if new_value != self.meters[meter]:
                self.meters[meter] = new_value
                if meter in LOCATIONS.meter_info:
                    for scene_name in GV.my_scenes:
                        scene = GV.my_scenes[scene_name]
                        # Skip scenes that don't have the MAIN grid defined yet
                        try:
                            scene.grids.get(Grid_ID.MAIN.value)
                        except Exception:
                            continue
                        scene.grid_objects.delete(to_delete_sub_string=f"{meter}_meter")
                        text = str(new_value)
                        # dodati $ ili sta vec ide uz taj meter
                        scene.grid_objects.add(
                            f"{meter}_meter",
                            GridLabel(
                                text=text,
                                r_x= LOCATIONS.meter_info[meter]["value"]["r_x"],
                                r_y= LOCATIONS.meter_info[meter]["value"]["r_y"],
                                r_width= LOCATIONS.meter_info[meter]["value"]["r_width"] * len(text),
                                r_height= LOCATIONS.meter_info[meter]["value"]["r_height"],
                                
                                anchor_x="center",
                                anchor_y="center",
                                color=clrs.rgb_to_rgba(LOCATIONS.meter_info[meter]["value"]["color"]),
                                
                                whiteboard=scene,
                                batch_id=BT.BASE.value,
                                group_idx=100001,
                                grid_id=Grid_ID.MAIN.value,
                            ),
                        )
        #speed = 1/self.timer.time_span(1)
        #if speed >=1:
        speed = 1/self.timer.time_span(1)

        speed_types = {0.25:0, 0.5:1, 1:2, 2:3, 4:4, 8:5, 16:6, 32:7}
        speed_idx = speed_types[speed]

        if True:
            self.speed_setting = speed_idx
            for temp_scene_name in GV.my_scenes:
                temp_scene = GV.my_scenes[temp_scene_name]
                # Skip scenes that don't have the MAIN grid defined yet
                try:
                    temp_scene.grids.get(Grid_ID.MAIN.value)
                except Exception:
                    continue
                temp_scene.grid_objects.delete(to_delete_sub_string="speed_meter")
                temp_scene.grid_objects.add(
                    "speed_meter_visual",
                    GridSprite(
                        r_x= LOCATIONS.speed_meter_info["image"]["r_x"],
                        r_y= LOCATIONS.speed_meter_info["image"]["r_y"],
                        r_width= LOCATIONS.speed_meter_info["image"]["r_width"],
                        r_height= LOCATIONS.speed_meter_info["image"]["r_height"],
                        pict=GV.PYGLET_IMAGES[f"speed_{speed_idx}"],
                        whiteboard=temp_scene,
                        batch_id=BT.BASE.value,
                        group_idx=100001,
                        grid_id=Grid_ID.MAIN.value,
                    ),
                )
                temp_empty_space = ""
                if len(str(speed)) < 4:
                    temp_empty_space = " "
                text = f"SPEED = x {speed}"
                temp_scene.grid_objects.add(
                    "speed_meter_text",
                    GridLabel(
                        text=text,
                        r_x= LOCATIONS.speed_meter_info["value"]["r_x"],
                        r_y= LOCATIONS.speed_meter_info["value"]["r_y"],
                        r_width= LOCATIONS.speed_meter_info["value"]["r_width"] * len(text),
                        r_height= LOCATIONS.speed_meter_info["value"]["r_height"],
                        
                        anchor_x="left",
                        anchor_y="center",
                        color=clrs.rgb_to_rgba(LOCATIONS.speed_meter_info["value"]["color"]),
                        
                        whiteboard=temp_scene,
                        batch_id=BT.BASE.value,
                        group_idx=100001,
                        grid_id=Grid_ID.MAIN.value,
                    ),
                )
        pyglet.clock.schedule_once(
            self.draw_my_animation,
            0.05,
        )
    def start_visualization(self, scepterInfo):
        # sounds
        if "info_dict" in scepterInfo.info and "sound" in scepterInfo.info["info_dict"]:
            self.play_sound(0, scepterInfo.info["info_dict"]["sound"])
            
        # game specific scepterinfos
        if scepterInfo.id == "spin_reels":
            self.__spin_reels(scepterInfo)
        elif scepterInfo.id == "pot":
            self.__pot(scepterInfo)
        elif scepterInfo.id == "refresh":
            self.__refresh(scepterInfo)
            
        # standardized scepterinfos
        else:
            self.standard_scepterinfo(scepterInfo)

    def __refresh(self, scepterInfo):
        reelpicture = scepterInfo.info["info_dict"]["reelpicture"]
        current_coinpicture = scepterInfo.info["info_dict"]["current_coinpicture"]
        for reel_idx, reel in enumerate(reelpicture):
            for row_idx, symbol in enumerate(reel):
                label = current_coinpicture[reel_idx, row_idx]
                self.draw_sprite_centered(
                    grid_object_id = f"reel_sym_{reel_idx}_{row_idx}",
                    sprite_name = GV.ETS[symbol], 
                    position = (reel_idx + 0.5, row_idx + 0.5),
                    grid_id = Grid_ID.MAIN.value,
                    group = GC.REEL_SYMBOLS
                )
                if label:
                    if label in GV.PROG_JACKPOT_ETN:
                        label = GV.PROG_JACKPOT_ETN[label]
                    self.draw_label_centered(
                        grid_object_id = f"reel_label_{reel_idx}_{row_idx}",
                        label = label,
                        position= (reel_idx + 0.5, row_idx + 0.5),
                        grid_id=Grid_ID.MAIN.value,
                        group=GC.REEL_LABELS,
                    )
        self.prepare_settle_visualization(0, scepterInfo)
            
    def move_spinning_reels(self, dt, objects, move_amount):
        for object in objects:
            object.r_y -= move_amount            

    def __spin_reels(self, scepterInfo):
        stop_positions = scepterInfo.info["info_dict"]["stop_positions"]
        current_reelpicture = scepterInfo.info["info_dict"]["current_reelpicture"]
        current_coinpicture = scepterInfo.info["info_dict"]["current_coinpicture"]
        # current_coinpicture = np.zeros_like(current_reelpicture) # use if no coins
        reels_to_tension_spin = scepterInfo.info["info_dict"]["reels_to_tension_spin"]
        # creating a 2D representation of reelstrips, like in excel
        reelset_2d = scepterInfo.info["info_dict"]["reelset_enum"]
        selected_bet_multiplier = self.selected_stake_options["Bet Multiplier"] # might be usefull
        coins_has = self.logic_data["coins_has"]
        # overshoot
        overshoot_time = math.pi * GV.OM["OVERSHOOT_AMPLITUDE"] * GV.OM["REEL_SPEED"]
        steps = round(GV.OM["FRAMERATE"] * overshoot_time)
        overshoot_path = []
        dt = overshoot_time / steps
        for i in range(steps):
            overshoot_path.append(GV.OM["OVERSHOOT_AMPLITUDE"] * math.sin(math.pi * i * dt / overshoot_time))
        overshoot_path.append(0)
        # delete everything
        self.grid_objects.delete(to_delete_sub_string=f"reel_sym_")
        self.grid_objects.delete(to_delete_sub_string=f"reel_label_")
        self.grid_objects.delete(to_delete_sub_string=f"spin_sym_")
        self.grid_objects.delete(to_delete_sub_string=f"spin_label_")
        self.grid_objects.delete(to_delete_sub_string=f"pp_")
        for reel_idx in range(GV.NUM_OF_REELS): # for every reel ...
            tension_spin_length  = round(np.sum(reels_to_tension_spin[:reel_idx+1]) * GV.OM["TENSION_SPIN"] / GV.OM["REEL_SPEED"])
            tension_spin_time = tension_spin_length * GV.OM["REEL_SPEED"]
            # creating the spinning reel
            """
            Part of the reelband is taken, such that the symbols above and below the stop position are seen on the 
            actual reelpicture, above and below. Fist symbol in spin_symbols is the above reelpicture symbol. 
            Next GV.NUM_OF_REELS symbols are reelpicture symbols. One after that is the one below the reelpicture.
            Last GV.NUM_OF_REELS are symbols from the reelpicture from the previous spin. spin_labels is used to 
            draw labels on coins, the same way as spin_symbols. If there are replacement smbols, before replacing the
            reepicture and previous_reelpicture with appropriate symbols, go trough the spin_symbols and replace them.
            """
            spin_height = round(1 + GV.REEL_HEIGHT + (GV.OM["FIRST_STOP_TIME"] + reel_idx * GV.OM["NEXT_REEL_TIME"]) / GV.OM["REEL_SPEED"] + tension_spin_length)
            spin_symbols = GV.STE["_BLN_1_"] * np.ones((spin_height,))
            spin_labels = np.zeros_like(spin_symbols)
            reelband = reelset_2d[reel_idx]
            # make the reelband longer so that reelroll is possible
            while len(reelband) <= len(spin_symbols):
                reelband = np.hstack((reelband, reelband))
            # roll the reels so that spin_symbols has the right offset
            stop_position = stop_positions[reel_idx]
            roll_offset = - stop_position + GV.REEL_HEIGHT - 1
            spin_symbols = np.roll(reelband, round(roll_offset))[: spin_height]
            # place all labels on coins if needed.
            where_coins = np.where(spin_symbols == GV.STE["_COI_1_"])
            for pos in zip(*where_coins):
                spin_labels[pos] = coins_has.draw_random_non_outcome()
            # place the current and the next reelpicture parts at the appropriate place in spin_symbols and spin_labels
            spin_symbols[-GV.REEL_HEIGHT:] = self.previous_reelpicture[reel_idx]
            spin_labels[-GV.REEL_HEIGHT:] = self.previous_coinpicture[reel_idx]
            spin_symbols[-GV.REEL_HEIGHT-1] = self.previous_reelpicture_above[reel_idx]
            spin_labels[-GV.REEL_HEIGHT-1] = self.previous_coinpicture_above[reel_idx]
            spin_symbols[1: 1 + GV.REEL_HEIGHT] = current_reelpicture[reel_idx]
            spin_labels[1: 1 + GV.REEL_HEIGHT] = current_coinpicture[reel_idx]
            # time to spin this reel
            move_time = GV.OM["FIRST_STOP_TIME"] + reel_idx * GV.OM["NEXT_REEL_TIME"] + tension_spin_time
            objects_to_move = []
            # drawing the spinning reels with symbols and labels
            for row_idx, (sym, label) in enumerate(zip(np.flip(spin_symbols), np.flip(spin_labels))):
                # draw symbol sprite
                self.draw_sprite_centered(
                    grid_object_id = f"spin_sym_{reel_idx}_{row_idx}",
                    sprite_name = GV.ETS[sym], 
                    position=(reel_idx + 0.5, GV.REEL_HEIGHT - row_idx - 0.5),
                    grid_id = Grid_ID.MAIN.value,
                    group = GC.SPINNING_SYMBOLS
                )
                objects_to_move.append(self.grid_objects.get(f"spin_sym_{reel_idx}_{row_idx}"))
                if label: 
                    # draw coin label
                    if label in GV.PROG_JACKPOT_ETN:
                        label = GV.PROG_JACKPOT_ETN[label]
                    self.draw_label_centered(
                        grid_object_id = f"spin_label_{reel_idx}_{row_idx}",
                        label = label,
                        position= (reel_idx + 0.5, GV.REEL_HEIGHT - row_idx - 0.5),
                        grid_id=Grid_ID.MAIN.value,
                        group=GC.SPINNING_LABELS,
                    )
                    objects_to_move.append(self.grid_objects.get(f"spin_label_{reel_idx}_{row_idx}"))
            # moving the spinning reel
            for frame in range(round(move_time*GV.OM["FRAMERATE"])):
                pyglet.clock.schedule_once(
                    self.move_spinning_reels,
                    self.timer.time_span(frame / GV.OM["FRAMERATE"]),
                    objects_to_move,
                    move_amount = 1/(GV.OM["REEL_SPEED"]*GV.OM["FRAMERATE"]),
                )
            # overshoot animation
            for frame, (position_0, position_1) in enumerate(zip(overshoot_path[:-1], overshoot_path[1:])):
                pyglet.clock.schedule_once(
                    self.move_spinning_reels,
                    self.timer.time_span(move_time + frame / GV.OM["FRAMERATE"]),
                    objects_to_move,
                    move_amount = position_1 - position_0,
                )
            # reel stop sound
            pyglet.clock.schedule_once(
                self.play_sound,
                self.timer.time_span(move_time + overshoot_time),
                f"reel_land_{reel_idx}",
            )
            # drawing the actual reel from current_reelpicture
            pyglet.clock.schedule_once(
                self.draw_reel,
                self.timer.time_span(move_time + overshoot_time + 0.01),
                scepterInfo,
                reel_idx,
                tension_spin_length,
            )
            # remembering what was above the reelpicture for the next spin (all in graphics)
            self.previous_reelpicture_above[reel_idx] = spin_symbols[0]
            self.previous_coinpicture_above[reel_idx] = spin_labels[0]
        # settle SI visualization
        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            self.timer.time_span(move_time + overshoot_time + 0.1),
            scepterInfo,
        )
        # remembering what was on the reelpicture for the next spin (all in graphics)
        self.previous_reelpicture = np.copy(current_reelpicture)
        self.previous_coinpicture = np.copy(current_coinpicture)
        
    def draw_reel(self, dt, scepterInfo, reel_idx, tension_spin_length):
        spin_height = round(1 + GV.REEL_HEIGHT + (GV.OM["FIRST_STOP_TIME"] + reel_idx * GV.OM["NEXT_REEL_TIME"]) / GV.OM["REEL_SPEED"] + tension_spin_length)
        current_reelpicture = scepterInfo.info["info_dict"]["current_reelpicture"]
        if "current_coinpicture" not in scepterInfo.info["info_dict"]:
            current_coinpicture = np.zeros_like(current_reelpicture)
        else:
            current_coinpicture = scepterInfo.info["info_dict"]["current_coinpicture"]
        for row_idx, (symbol, label) in enumerate(zip(current_reelpicture[reel_idx], current_coinpicture[reel_idx])):
            self.grid_objects.delete(to_delete_sub_string=f"spin_sym_{reel_idx}_{spin_height - 2 - row_idx}")
            self.grid_objects.delete(to_delete_sub_string=f"spin_label_{reel_idx}_{spin_height - 2 - row_idx}")
            self.draw_sprite_centered(
                grid_object_id = f"reel_sym_{reel_idx}_{row_idx}",
                sprite_name = GV.ETS[symbol], 
                position = (reel_idx + 0.5, row_idx + 0.5),
                grid_id = Grid_ID.MAIN.value,
                group = GC.REEL_SYMBOLS
            )
            if label:
                # draw coin label
                if label in GV.PROG_JACKPOT_ETN:
                    label = GV.PROG_JACKPOT_ETN[label]
                self.draw_label_centered(
                    grid_object_id = f"reel_label_{reel_idx}_{row_idx}",
                    label = label,
                    position= (reel_idx + 0.5, row_idx + 0.5),
                    grid_id=Grid_ID.MAIN.value,
                    group=GC.REEL_LABELS,
                )

    def __pot(self, scepterInfo):
        #collect symbols from reels to pots
        self.collect_symbols(scepterInfo)

        self.trigger_pot(scepterInfo)

        ##TODO: fix timing and visual glitch


    def collect_symbols(self, scepterInfo):
        coords = scepterInfo.info["info_dict"]["coords"]
        pot_index = scepterInfo.info["info_dict"]["pot_index"]

        pot_sprites = GV.POTS_BG_SYMS
        pot_to_move_to = self.grid_objects.get(f"pot_{pot_index}")
        move_to_coords = [(pot_to_move_to.r_x, pot_to_move_to.r_y)]

        for reel_idx, row_idx in coords:
            object_id = f"pp_{pot_index}_sym_{reel_idx}_{row_idx}"
            self.draw_sprite_centered(
                    grid_object_id = object_id,
                    sprite_name = f"{pot_sprites[pot_index][0]}", 
                    position = (reel_idx + 0.5, row_idx + 0.5),
                    grid_id = Grid_ID.MAIN.value,
                    group = GC.REELS_FRONT
                )

            object = self.grid_objects.get(object_id)
            objects_to_move = [object]
            move_from_coords = [(object.r_x, object.r_y)]
            move_grid_objects(
                objects=objects_to_move,
                from_coordinates=move_from_coords,
                to_coordinates=move_to_coords,
                duration=self.timer.time_span(GV.OM["COLLECT_COIN"] + 0.01),
                steps=int(GV.OM["FRAMERATE"]*GV.OM["COLLECT_COIN"]),
                next_function_to_call=self.do_nothing,
                kargs={},
                delay=0,
            )

    def trigger_pot(self, scepterInfo):
        trigger = scepterInfo.info["info_dict"]["trigger"]
        pot_index = scepterInfo.info["info_dict"]["pot_index"]

        if(trigger):
            object = self.grid_objects.get(f"pot_{pot_index}")
            objects = [object]
            num_steps = round(GV.OM["SHAKE"] * GV.OM["FRAMERATE"])
            prev_x = 0
            prev_y = 0
            for step  in range(num_steps):
                dt = GV.OM["SHAKE"] * step / GV.OM["FRAMERATE"]
                rand_x = np.random.uniform(-0.03, 0.03)
                rand_y = np.random.uniform(-0.03, 0.03)
                pyglet.clock.schedule_once(
                    self.move_single_step,
                    self.timer.time_span(dt),
                    objects,
                    rand_x - prev_x if step != num_steps-1 else - prev_x,
                    rand_y - prev_y if step != num_steps-1 else - prev_y,
                )
                prev_x = 1 * rand_x
                prev_y = 1 * rand_y
            pyglet.clock.schedule_once(
                self.prepare_settle_visualization,
                self.timer.time_span(dt + 0.01),
                scepterInfo,
            )

            
    def create_pots(self):
        center_x = 2.5
        y_pos = -0.6
        n_pots = GV.POTS_BG
        spacing = 1

        if n_pots <= 1:
            positions = [center_x]
        else:
            total_span = spacing * (n_pots - 1)
            start_x = center_x - total_span / 2
            positions = [start_x + i * spacing for i in range(n_pots)]
        for pot_index, x_pos in enumerate(positions):
            self.draw_sprite_centered(
                grid_object_id= f"pot_{pot_index}",
                sprite_name = f"pot_{pot_index}",
                position= (x_pos, y_pos),
                grid_id= Grid_ID.MAIN.value,
                group= GC.REEL_LABELS,
            )
    