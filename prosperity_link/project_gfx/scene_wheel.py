import math
import random
import os

from global_variables import GlobalConfig as GV
import numpy as np
import pyglet
from global_variables import GroupConstants as GC
from scepter.common.constants import BatchTypes as BT
from scepter.common.constants import MeterConstants as MC
from scepter.common.constants import Paths as PT
from scepter.get_root_path import get_root_path
from scepter.gfx.accessories import colors as clrs
from scepter.gfx.grid.grid import Grid
from scepter.gfx.grid_object_manipulations.move_grid_objects import \
    move_grid_objects
from scepter.gfx.scenes.scene import Scene
from scepter.gfx.grid_objects.grid_sprite import GridSprite
from ..project_gfx.scene_template import Grid_ID, SceneGamepartTemplate

y_HEIGHT = 5
x_WIDTH = 4

BY = 0.06
TY = 0.5
LX = 0.0176
RX = 0.0178

class SceneWheel(SceneGamepartTemplate):
     def __init__(self, **kwargs):
        super().__init__(
            height_to_width=(1/2+y_HEIGHT+1/2) / (1/2+1+x_WIDTH+1+1/2),
            **kwargs
        )
        self.grids.add(
            Grid_ID.WHEEL.value,
            Grid(
                left_cells = 1/2+1,
                x_cells = x_WIDTH,
                right_cells = 1/2+1,
                bottom_cells = 1/2,
                y_cells = y_HEIGHT,
                top_cells = 1/2,
            ),
            grid_objects=self.grid_objects,
            batches=self.batches,
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
        self.saved_scepterinfo = None
        GV.my_scenes["wheel"] = self

     def initialize_visualization(self, meter_updater=None):
        self.grid_objects.add(
            "bkgrnd_overlay",
            GridSprite(
                r_x=-1/2-1,
                r_y=0,
                r_width=x_WIDTH+2/2+2,
                r_height=y_HEIGHT+4/2,
                pict=pyglet.image.load(
                    os.path.join(get_root_path(), PT.BACKGROUND_BLUEISH.value)
                ),
                whiteboard=self,
                batch_id=BT.BASE.value,
                group_idx=2,
                grid_id=Grid_ID.MAIN.value,
            )
        )

        self.draw_string_centered(
            grid_object_id= f"prize_pointer",
            label = "<",
            position=(4, 1.7),
            grid_id= Grid_ID.WHEEL.value,
            group= GC.REEL_LABELS,
            color= clrs.Red,
        )

        self.load_the_dashboard()
        self.meter_updater = meter_updater
        meters_to_update = {"RANDOM_SEED": GV.RANDOM_SEED}
        self.meter_updater(meters_to_update)

     def start_visualization(self, scepterInfo):
        # sounds
        if "info_dict" in scepterInfo.info and "sound" in scepterInfo.info["info_dict"]:
            self.play_sound(0, scepterInfo.info["info_dict"]["sound"])
            
        # game specific scepterinfos
        if scepterInfo.id == "reset_wheel":
            self.__reset_wheel(scepterInfo)
        elif scepterInfo.id == "wheel_spin_start":
            self.__spin_wheel(scepterInfo)
        elif scepterInfo.id == "wheel_spin_stop":
            self.__stop_wheel(scepterInfo)
        elif scepterInfo.id == "wheel_exit":
            self.__wheel_exit(scepterInfo)
        # standardized scepterinfos
        else:
            self.standard_scepterinfo(scepterInfo)


     def __reset_wheel(self, scepterInfo):
        self.grid_objects.delete(to_delete=["wheel"])
        self.draw_generated_sprite_centered(
            grid_object_id = f"wheel",
            sprite_name = "wheel_sprite.png",
            folder_name = "wheel",
            position=(.25,3.5),
            grid_id = Grid_ID.WHEEL.value,
            group = GC.REELS_FRONT,
            symbol_size=(3.5,3.5),
        )
        wheel = self.grid_objects.get("wheel")

        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            self.timer.time_span(2),
            scepterInfo,
        )

     def __spin_wheel(self, scepterInfo):
        steps = 100
        spin_duration = 3
        self.spin_progress = 0
        pyglet.clock.schedule_interval(self.rotate_wheel, self.timer.time_span(spin_duration/steps), scepterInfo, self.timer.time_span(spin_duration))
        pyglet.clock.schedule_once(self.prepare_settle_visualization, self.timer.time_span(spin_duration), scepterInfo)

     def __stop_wheel(self, scepterInfo):
        stop_angle = scepterInfo.info["info_dict"]["stop_angle"]
        wheel = self.grid_objects.get("wheel")
        wheel.rotate_degrees(stop_angle-wheel.rotation)
        self.prepare_settle_visualization(0, scepterInfo)

     def rotate_wheel(self, dt, scepterInfo, duration):
        exp_lambda = 8
        total_rotation = scepterInfo.info["info_dict"]["rotation"]
        self.spin_progress += dt/duration
        wheel_grid_obj: GridSprite = self.grid_objects.get("wheel")
        prev_rotation = wheel_grid_obj.rotation
        current_rotation = total_rotation * (1-math.exp(-exp_lambda * self.spin_progress))
        # print(total_rotation, self.spin_progress, current_rotation, prev_rotation)
        wheel_grid_obj.rotate_degrees(
            delta_rotation=current_rotation-prev_rotation,
        )

     def __wheel_exit(self, scepterInfo):
        #Can add mathbox here

        pyglet.clock.unschedule(self.rotate_wheel)
        
        pyglet.clock.schedule_once(
            self.prepare_finish_visualization,
            self.timer.time_span(2),
            scepterInfo,
        )