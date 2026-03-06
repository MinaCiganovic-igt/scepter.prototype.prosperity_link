import math
import os
import random
from copy import deepcopy
from enum import Enum, auto

from global_variables import GlobalConfig as GV
import numpy as np
import pyglet
from global_variables import GroupConstants as GC
from scepter.common.constants import BatchTypes as BT
from scepter.common.constants import MeterConstants as MC
from scepter.common.constants import ScepterInfoInfo as SII
from scepter.common.constants import ScepterInfoType as SIT
from scepter.common.internal_constants import BaseControlIds
from scepter.gfx.accessories import colors as clrs
from scepter.gfx.grid.grid import Grid
from scepter.gfx.grid_object_manipulations.heartbeat import \
    heart_beat_left_bottom_anchored
from scepter.gfx.grid_object_manipulations.move_grid_objects import \
    move_grid_objects
from scepter.gfx.grid_object_manipulations.shiver_grid_objects import \
    shiver_grid_objects
from scepter.gfx.grid_objects.grid_frame import GridFrame
from scepter.gfx.grid_objects.grid_label import GridLabel
from scepter.gfx.grid_objects.grid_sprite import GridSprite
from scepter.gfx.scenes.scene import Scene
from scepter.get_root_path import get_project_gfx_target_path, get_root_path
import location_constants as LOCATIONS

BY = 0.25
TY = 3.45
LX = 0.25
RX = 0.25

class Grid_ID(Enum):
    MAIN = auto()
    BCKG = auto()
    WHEEL = auto()

class SceneGamepartTemplate(Scene):
    def __init__(self,height_to_width=1, **kwargs):
        Scene.__init__(
            self,
            height_to_width=height_to_width,
            **kwargs
        )
        self.saved_scepterinfo = None

    def draw_sprite_centered(self, grid_object_id, sprite_name, position, grid_id, group, symbol_size = (1, 1)):
        if sprite_name in GV.SYMBOL_WIDTH:
            symbol_size = GV.SYMBOL_WIDTH[sprite_name]
        grid = self.grids.get(grid_id)
        r_x = position[0]
        r_y = grid.y_cells - position[1]
        self.grid_objects.delete(to_delete_sub_string=grid_object_id)
        self.grid_objects.add(
            grid_object_id,
            GridSprite(
                r_x=r_x,
                r_y=r_y,
                r_width=symbol_size[0],
                r_height=symbol_size[1],
                pict=GV.PYGLET_IMAGES[sprite_name],
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=group,
                grid_id=grid_id,
            ),
        )

    def draw_sprite_centered_with_size(self, grid_object_id, sprite_name, position, grid_id, group, symbol_size):
        grid = self.grids.get(grid_id)
        r_x = position[0]
        r_y = grid.y_cells - position[1]

        self.grid_objects.delete(to_delete_sub_string=grid_object_id)
        self.grid_objects.add(
            grid_object_id,
            GridSprite(
                r_x=r_x,
                r_y=r_y,
                r_width=symbol_size[0],
                r_height=symbol_size[1],
                pict=GV.PYGLET_IMAGES[sprite_name],
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=group,
                grid_id=grid_id,
            ),
        )

    def draw_generated_sprite_centered(self, grid_object_id, sprite_name, folder_name, position, grid_id, group, symbol_size = (1, 1)):
        if sprite_name in GV.SYMBOL_WIDTH:
            symbol_size = GV.SYMBOL_WIDTH[sprite_name]
        grid = self.grids.get(grid_id)
        r_x = position[0]
        r_y = grid.y_cells - position[1]
        self.grid_objects.delete(to_delete_sub_string=grid_object_id)
        self.grid_objects.add(
            grid_object_id,
            GridSprite(
                r_x=r_x,
                r_y=r_y,
                r_width=symbol_size[0],
                r_height=symbol_size[1],
                pict=pyglet.image.load(
                    os.path.join(get_project_gfx_target_path(), folder_name, sprite_name)
                ),
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=group,
                grid_id=grid_id,
            ),
        )

    def draw_label_centered(self, grid_object_id, label, position, grid_id, group, size = (0.5, 0.5), color = clrs.Black):
        grid = self.grids.get(grid_id)
        r_x = position[0]
        r_y = grid.y_cells - position[1]
        if type(label) in [float,np.float64]:
            label = round(label)
        self.grid_objects.delete(to_delete_sub_string=grid_object_id)
        self.grid_objects.add(
            grid_object_id,
            GridLabel(
                text=str(label),
                r_x=r_x,
                r_y=r_y,
                r_width=size[0],
                r_height=size[1],
                anchor_x="center",
                anchor_y="center",
                color=clrs.rgb_to_rgba(color),
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=group,
                grid_id=grid_id,
            ),
        )
    def draw_string_centered(self, grid_object_id, label, position, grid_id, group, size = (0.5, 0.5), color = clrs.Black):
        grid = self.grids.get(grid_id)
        r_x = position[0]
        r_y = grid.y_cells - position[1]
        self.grid_objects.delete(to_delete_sub_string=grid_object_id)
        self.grid_objects.add(
            grid_object_id,
            GridLabel(
                text=str((label)),
                r_x=r_x,
                r_y=r_y,
                r_width=size[0],
                r_height=size[1],
                anchor_x="center",
                anchor_y="center",
                color=clrs.rgb_to_rgba(color),
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=group,
                grid_id=grid_id,
            ),
        )
    def load_the_dashboard(self):
        text = "WIN"
        self.grid_objects.add(
            "win_label",
            GridLabel(
                text=text,
                r_x= LOCATIONS.meter_info['win']["label"]["r_x"],
                r_y= LOCATIONS.meter_info['win']["label"]["r_y"],
                r_width= LOCATIONS.meter_info['win']["label"]["r_width"] * len(text),
                r_height= LOCATIONS.meter_info['win']["label"]["r_height"],
                anchor_x="center",
                anchor_y="center",
                color=clrs.rgb_to_rgba(clrs.Yellow),
                
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=100001,
                grid_id=Grid_ID.MAIN.value,
            ),
        )
        
        self.grid_objects.add(
            "credits_label",
            GridLabel(
                text="Credits",
                r_x= LOCATIONS.meter_info['credits']["label"]["r_x"],
                r_y= LOCATIONS.meter_info['credits']["label"]["r_y"],
                r_width= LOCATIONS.meter_info['credits']["label"]["r_width"] * len(text),
                r_height= LOCATIONS.meter_info['credits']["label"]["r_height"],
                anchor_x="center",
                anchor_y="center",
                color=clrs.rgb_to_rgba(clrs.White),
                
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=100001,
                grid_id=Grid_ID.MAIN.value,
            ),
        )
        self.grid_objects.add(
            "CTC_label",
            GridLabel(
                text="Line Bet",
                r_x= LOCATIONS.meter_info['total_bet']["label"]["r_x"],
                r_y= LOCATIONS.meter_info['total_bet']["label"]["r_y"],
                r_width= LOCATIONS.meter_info['total_bet']["label"]["r_width"] * len(text),
                r_height= LOCATIONS.meter_info['total_bet']["label"]["r_height"],
                anchor_x="center",
                anchor_y="center",
                color=clrs.rgb_to_rgba(clrs.White),
                
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=100001,
                grid_id=Grid_ID.MAIN.value,
            ),
        )
        self.grid_objects.add(
            "RNG_SEED",
            GridLabel(
                text="SEED",
                r_x= LOCATIONS.meter_info['RANDOM_SEED']["label"]["r_x"],
                r_y= LOCATIONS.meter_info['RANDOM_SEED']["label"]["r_y"],
                r_width= LOCATIONS.meter_info['RANDOM_SEED']["label"]["r_width"] * len(text),
                r_height= LOCATIONS.meter_info['RANDOM_SEED']["label"]["r_height"],
                anchor_x="center",
                anchor_y="center",
                color=clrs.rgb_to_rgba(clrs.White),
                
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=100001,
                grid_id=Grid_ID.MAIN.value,
            ),
        )
        self.grid_objects.add(
            "dashboard_background",
            GridSprite(
                r_x=0.5,
                r_y=0.03,
                r_width=1,
                r_height=0.06,
                pict=GV.PYGLET_IMAGES["dashboard_background"],
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=100000,
                grid_id=Grid_ID.BCKG.value,
            ),
        )
    def standard_scepterinfo(self, scepterInfo):
        if scepterInfo.id == "any_win":
                pyglet.clock.schedule_once(
                self.prepare_settle_visualization,
                GV.OM["HOLD_WIN"],
                scepterInfo,
            )
        elif scepterInfo.id == "heartbeat_symbols":
            self.__heartbeat_symbols(scepterInfo)
        elif scepterInfo.id == "shake_symbols":
            self.__shake_symbols(scepterInfo)
        elif scepterInfo.id == "line_win":
            self.__line_win(scepterInfo)
        elif scepterInfo.id == "ways_win":
            self.__ways_win(scepterInfo)
        elif scepterInfo.id == "collect_coin":
            self.__collect_coin(scepterInfo)
        elif scepterInfo.id == "disappear_symbols":
            self.__disappear_symbols(scepterInfo)
        elif scepterInfo.id == "rotate_symbols":
            self.__rotate_symbols(scepterInfo)
        elif scepterInfo.id == "delay":
            delay = GV.OM[scepterInfo.info["info_dict"]["delay_amount"]]
            pyglet.clock.schedule_once(
                self.prepare_settle_visualization,
                delay,
                scepterInfo,
            )
        elif SIT.DRAW_ANIMATION in scepterInfo.types and scepterInfo.id == "manual_spin":
            if self.play_state.autoplay:
                self.prepare_settle_visualization(0, scepterInfo)
            else:
                self.saved_scepterinfo = scepterInfo
        elif SIT.STATS_PAYLOAD in scepterInfo.types:
            self.prepare_settle_visualization(0, scepterInfo)
        elif SIT.VISUALIZE_METERS in scepterInfo.types:
            self.meter_updater(scepterInfo.info[SII.METERS_TO_UPDATE])
            self.prepare_settle_visualization(0, scepterInfo)
        else:
            self.prepare_settle_visualization(0, scepterInfo)
            
    def __rotate_single_step(self, dt, object, rotation_angle):
        object.rotation = rotation_angle
        
    def __rotate_symbols(self, scepterInfo):
        places = scepterInfo.info["info_dict"]["places"]
        objects_to_rotate = []
        for reel_idx, row_idx in places:
            objects_to_rotate.append(self.grid_objects.get(f"reel_sym_{reel_idx}_{row_idx}"))
        num_steps = round(GV.OM["ROTATE"] * GV.OM["FRAMERATE"])
        for frame in range(num_steps):
            for object in objects_to_rotate:
                pyglet.clock.schedule_once(
                    self.__rotate_single_step,
                    GV.OM["ROTATE"]*frame/num_steps,
                    object,
                    360*(frame+1)/num_steps
                )
        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            GV.OM["ROTATE"] + 0.01,
            scepterInfo,
        )

    def reshape_single_step(self, dt, object, original_relative_dimensions, relative_size):
        object.r_width = original_relative_dimensions[0] * relative_size
        object.r_height = original_relative_dimensions[1] * relative_size

    def __disappear_symbols(self, scepterInfo):
        places = scepterInfo.info["info_dict"]["places"]
        objects = []
        for place in places:
            objects.append(self.grid_objects.get(f"reel_sym_{place[0]}_{place[1]}"))
        num_steps = round(GV.OM["DISAPPEAR"] * GV.OM["FRAMERATE"])
        for object in objects:
            original_relative_dimensions = (object.r_width, object.r_height)
            for step_idx in range(num_steps):
                relative_size = (num_steps - step_idx - 1)/num_steps
                pyglet.clock.schedule_once(
                    self.reshape_single_step,
                    step_idx * GV.OM["DISAPPEAR"] / GV.OM["FRAMERATE"],
                    object,
                    original_relative_dimensions,
                    relative_size
                )
        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            GV.OM["DISAPPEAR"],
            scepterInfo,
        )

    def __heartbeat_symbols(self, scepterInfo):
        places = scepterInfo.info["info_dict"]["places"]
        objects = []
        for reel_idx, row_idx in places:
            objects.append(self.grid_objects.get(f"reel_sym_{reel_idx}_{row_idx}"))
        num_steps = round(GV.OM["HEARTBEAT"] * GV.OM["FRAMERATE"])
        for object in objects:
            original_relative_dimensions = (object.r_width, object.r_height)
            for step  in range(num_steps):
                dt = (step+1) / GV.OM["FRAMERATE"]
                relative_size = 1 + 0.25 * math.sin(math.pi * dt / GV.OM["HEARTBEAT"])
                pyglet.clock.schedule_once(
                    self.reshape_single_step,
                    dt,
                    object,
                    original_relative_dimensions,
                    relative_size,
                )
        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            dt + 0.01,
            scepterInfo,
        )

    def move_single_step(self, dt, objects, dx, dy):
        for object in objects:
            object.r_y -= dy 
            object.r_x -= dx
        
    def __shake_symbols(self, scepterInfo):
        places = scepterInfo.info["info_dict"]["places"]
        objects = []
        for reel_idx, row_idx in places:
            objects.append(self.grid_objects.get(f"reel_sym_{reel_idx}_{row_idx}"))
        num_steps = round(GV.OM["SHAKE"] * GV.OM["FRAMERATE"])
        prev_x = 0
        prev_y = 0
        for step  in range(num_steps):
            dt = GV.OM["SHAKE"] * step / GV.OM["FRAMERATE"]
            rand_x = np.random.uniform(-0.03, 0.03)
            rand_y = np.random.uniform(-0.03, 0.03)
            pyglet.clock.schedule_once(
                self.move_single_step,
                dt,
                objects,
                rand_x - prev_x if step != num_steps-1 else - prev_x,
                rand_y - prev_y if step != num_steps-1 else - prev_y,
            )
            prev_x = 1 * rand_x
            prev_y = 1 * rand_y
        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            self.dt + 0.01,
            scepterInfo,
        )

    def __line_win(self, scepterInfo):
        line_win_coordinates = scepterInfo.info["info_dict"]["line_win_coordinates"]
        length = scepterInfo.info["info_dict"]["length"]
        reelpicture = scepterInfo.info["info_dict"]["reelpicture"]
        # draw gray rp
        for reel_idx, reel in enumerate(reelpicture):
            for row_idx, sym in enumerate(reel):
                obj = self.grid_objects.get(f"reel_sym_{reel_idx}_{row_idx}")
                obj.color = (60, 60, 60)
        for reel_idx, row_idx in enumerate(line_win_coordinates):
            if reel_idx < length:
                obj = self.grid_objects.get(f"reel_sym_{reel_idx}_{row_idx}")
                obj.color = (255, 255, 255)
            self.draw_sprite_centered(
                grid_object_id = f"win_eval_marked_cell_{reel_idx}_{row_idx}",
                sprite_name = "grid_frame_win" if reel_idx < length else "grid_frame_no_win", 
                position=(reel_idx + 0.5, row_idx + 0.5),
                grid_id = Grid_ID.MAIN.value,
                group = GC.FRAMES
            )
        pyglet.clock.schedule_once(
            self.__reset_rp,
            .5,
            scepterInfo,
        )

    def __ways_win(self, scepterInfo):
        ways_win_coordinates = scepterInfo.info["info_dict"]["ways_win_coordinates"]
        length = scepterInfo.info["info_dict"]["length"]
        reelpicture = scepterInfo.info["info_dict"]["reelpicture"]
        # draw gray rp
        for reel_idx, reel in enumerate(reelpicture):
            for row_idx, sym in enumerate(reel):
                obj = self.grid_objects.get(f"reel_sym_{reel_idx}_{row_idx}")
                obj.color = (60, 60, 60)
        for pos in ways_win_coordinates:
            reel_idx, row_idx = pos[0], pos[1]
            if reel_idx < length:
                obj = self.grid_objects.get(f"reel_sym_{reel_idx}_{row_idx}")
                obj.color = (255, 255, 255)
            self.draw_sprite_centered(
                grid_object_id = f"win_eval_marked_cell_{reel_idx}_{row_idx}",
                sprite_name = "grid_frame_win" if reel_idx < length else "grid_frame_no_win",
                position=(reel_idx + 0.5, row_idx + 0.5),
                grid_id = Grid_ID.MAIN.value,
                group = GC.FRAMES
            )
        pyglet.clock.schedule_once(
            self.__reset_rp,
            self.GV.OM["LINE_SHOW_LENGTH"],
            scepterInfo,
        )
           
    def __reset_rp(self, dt, scepterInfo):
        reelpicture = scepterInfo.info["info_dict"]["reelpicture"]
        for reel_idx, reel in enumerate(reelpicture):
            for row_idx, sym in enumerate(reel):
                self.draw_sprite_centered(
                    grid_object_id = f"reel_sym_{reel_idx}_{row_idx}",
                    sprite_name = GV.ETS[sym], 
                    position=(reel_idx + 0.5, row_idx + 0.5),
                    grid_id = Grid_ID.MAIN.value,
                    group = GC.REEL_SYMBOLS
                )
        self.prepare_settle_visualization(0, scepterInfo)
        
    def __collect_coin(self, scepterInfo):
        reel_idx, row_idx = scepterInfo.info["info_dict"]["coin_place"]
        object = self.grid_objects.get(f"reel_label_{reel_idx}_{row_idx}")
        objects_to_move = [object]
        move_from_coords = [(object.r_x, object.r_y)]
        move_to_coords = [(2.5, -1)]
        move_grid_objects(
            objects=objects_to_move,
            from_coordinates=move_from_coords,
            to_coordinates=move_to_coords,
            duration=GV.OM["COLLECT_COIN"] + 0.01,
            steps=int(GV.OM["FRAMERATE"]*GV.OM["COLLECT_COIN"]),
            next_function_to_call=self.prepare_settle_visualization,
            args=[scepterInfo],
            kargs={},
            delay=0,
        )

    def proceed_with_next_game(self):
        scepterinfo_to_proceed = deepcopy(self.saved_scepterinfo)
        self.saved_scepterinfo = None
        self.prepare_settle_visualization(0, scepterinfo_to_proceed)

    def on_key_release(self, symbol, modifiers):
        if self.saved_scepterinfo is None:
            super().on_key_release(symbol, modifiers)
        else:
            if symbol==pyglet.window.key.SPACE:
                self.proceed_with_next_game()

    def on_basecontrol_release(self, button_id):
        if self.saved_scepterinfo is None:
            super().on_basecontrol_release(button_id)
        else:
            if button_id == BaseControlIds.PLAY:
                self.proceed_with_next_game()
    
    def play_sound(self, dt, sound_string):
        GV.SOUNDS_DICT[sound_string].play()

    def settle_visualization(self, scepterInfo):
        self.grid_objects.delete(to_delete_sub_string="win_eval_marked_cell")
        self.prepare_finish_visualization(None, scepterInfo)

    def finish_visualization(self, dt):
        pass
    
    def do_nothing(self, dt = 0):
        pass

    def refresh_visualization(self):
        pass
