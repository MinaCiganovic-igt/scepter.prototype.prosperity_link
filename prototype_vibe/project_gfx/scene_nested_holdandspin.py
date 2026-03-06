import numpy as np
import pyglet
from scepter.gfx.grid_objects.grid_sprite import GridSprite
from scepter.common.constants import BatchTypes as BT
from scepter.gfx.accessories import colors as clrs
from global_variables import GlobalConfig as GV
from global_variables import GroupConstants as GC
from ..project_gfx.scene_template import Grid_ID

def spin_nested_bonus(self, scene, scepterInfo):
        """
        Spins the given positions (list of (reel_idx, row_idx)) in the 3x3 grid.
        Each position will animate from first_symbol to last_symbol.
        """
        mini_reelpicture = scepterInfo.info["info_dict"]["mini_reelpicture"]
        places_to_spin = scepterInfo.info["info_dict"]["places_to_spin"]
        current_coinpicture = scepterInfo.info["info_dict"]["current_coinpicture"]
        nested_bonus_spins = scepterInfo.info["info_dict"]["nested_bonus_spins"]

        

        self.mini_reels_to_spin = np.zeros_like(self.reels_to_spin, shape=(3, 3))  
        self.mini_reels_to_spin[:, :] = 1

        self.grid_objects.delete(to_delete_sub_string=f"mini_spin_sym_")
        for reel_idx, row_idx in places_to_spin:
            symbols_to_spin = self.create_mini_symbols_to_spin(
                (reel_idx, row_idx), 
                first_element= "_BLN_2_",
                last_element=GV.ETS[mini_reelpicture[reel_idx, row_idx]]
            )
            time = 0
            pyglet.clock.schedule_once(
                self.__mini_first_pass,
                self.timer.time_span(time),
                (reel_idx, row_idx),
                symbols_to_spin[0],
                0,
            )
            for sym_idx, symbol_to_spin in enumerate(symbols_to_spin[1:]):
                pyglet.clock.schedule_once(
                    self.__mini_single_pass,
                    self.timer.time_span(time),
                    (reel_idx, row_idx),
                    symbol_to_spin,
                    sym_idx + 1,
                )
                time += GV.OM["MINIREELS_SPEED"]
            pyglet.clock.schedule_once(
                self.__draw_mini_reel_sym,
                self.timer.time_span(time),
                (reel_idx, row_idx),
                mini_reelpicture[reel_idx, row_idx],
                current_coinpicture[reel_idx, row_idx],
            )

        self.update_mini_spin_counter(nested_bonus_spins)

        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            self.timer.time_span(round((3 * (GV.NUM_OF_REELS-1) + (3-1)) * GV.OM["MINIREELS_SPEED"] + GV.OM["HOLDANDSPIN"])),
            scepterInfo,
        )
        
def update_mini_spin_counter(self, count):
        self.grid_objects.delete(to_delete=["mini_spin_counter"])
        self.draw_string_centered(
                grid_object_id = f"mini_spin_counter",
                label = f"Spins: {count}",
                position= (5, 3),
                grid_id=Grid_ID.MAIN,
                group=21,
            )
        
def __create_nested_bonus(self, scepterInfo):
        """
        Creates a 3x3 reels grid on the MAIN grid and draws default symbols.
        """

        mini_reelpicture = scepterInfo.info["info_dict"]["mini_reelpicture"]
        self.draw_sprite_centered(
            grid_object_id = f"mini_reels_back_has",
            sprite_name = "mini_reels_back_has", 
            position=(3, 3),
            grid_id = Grid_ID.MAIN,
            group = GC.DASHBOARD_BLOCKER,
            symbol_size= (3,3),
        )

        # Draw the 3x3 grid symbols
        for reel_idx, reel in enumerate(mini_reelpicture):
            for row_idx, symbol in enumerate(reel):
                self.draw_sprite_centered(
                    grid_object_id = f"mini_spin_sym_{reel_idx}_{row_idx}",
                    sprite_name = "_BLN_2_",
                    position = (reel_idx + 2, row_idx + 2),
                    grid_id = Grid_ID.MAIN,
                    group = 10,
                )

        #Draw wheel symbol in middle
        self.draw_sprite_centered(
            grid_object_id = f"mini_wheel_sym_{1}_{1}",
            sprite_name = "SC",
            position = (1 + 2, 1 + 2),
            grid_id = Grid_ID.MAIN,
            group = 12,
        )

        #Draw spin counter background
        self.draw_sprite_centered(
            grid_object_id = f"mini_spin_background_counter",
            sprite_name = "test_square",
            position = (5, 1 + 2),
            grid_id = Grid_ID.MAIN,
            group = 20,
        )

        self.update_mini_spin_counter(3)



        pyglet.clock.schedule_once(
            self.prepare_settle_visualization,
            self.timer.time_span(.5),
            scepterInfo,
        )
