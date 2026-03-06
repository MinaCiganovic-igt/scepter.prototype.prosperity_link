import pyglet
from scepter.gfx.grid_objects.grid_sprite import GridSprite
from scepter.common.constants import BatchTypes as BT
from scepter.gfx.accessories import colors as clrs
from global_variables import GlobalConfig as GV
from global_variables import GroupConstants as GC
from ..project_gfx.scene_template import Grid_ID

CORNER_MARGIN = 0.25

def draw_multiplier_side(scene, multipliers, side: str = "left"):
    if not multipliers:
        return
    for row_idx, val in enumerate(multipliers):
        pos_x = GV.HNS_COLS - CORNER_MARGIN
        pos_y = row_idx + 1 - CORNER_MARGIN
        border_color = clrs.rgb_to_rgba(clrs.Black)
        border_image = pyglet.image.SolidColorImagePattern(border_color).create_image(1, 1)
        box_width = 0.6
        box_height = 0.6
        border_thickness = 0.05
        scene.grid_objects.add(
            f"mult_border_{row_idx}",
            GridSprite(
                r_x=pos_x-.25,
                r_y=pos_y-1.75,
                r_width=box_width,
                r_height=box_height,
                pict=border_image,
                whiteboard=scene,
                batch_id=BT.BASE.value,
                group_idx=GC.REEL_LABELS - 1,
                grid_id=Grid_ID.MAIN.value,
            ),
        )
        
        scene.draw_label_centered(
            grid_object_id=f"mult_{row_idx}",
            label=str(val),
            position=(pos_x, pos_y),
            color=clrs.Red,
            grid_id=Grid_ID.MAIN.value,
            group=GC.REEL_LABELS,
        )

def draw_top_counters(scene, counters):
    grid = scene.grids.get(Grid_ID.MAIN.value)
    bg_color = clrs.rgb_to_rgba(clrs.Silver)
    bg_image = pyglet.image.SolidColorImagePattern(bg_color).create_image(1, 1)
    top_pos_y = -0.6
    box_w, box_h = 0.6, 0.35
    for i in range(5):
        #Here you can customize the label text as needed
        label_text = f"P{i+1}: " + str(counters[i]) if i < len(counters) else "0"
        pos_x = i + 0.5
        pos_y = top_pos_y
        bg_id = f"topbox_bg_{i}"
        scene.grid_objects.delete(to_delete_sub_string=bg_id)
        scene.grid_objects.add(
            bg_id,
            GridSprite(
                r_x=pos_x,
                r_y=grid.y_cells - pos_y,
                r_width=box_w,
                r_height=box_h,
                pict=bg_image,
                whiteboard=scene,
                batch_id=BT.BASE.value,
                group_idx=GC.TOP_SCREEN,
                grid_id=Grid_ID.MAIN.value,
            ),
        )
        scene.draw_label_centered(
            grid_object_id=f"topbox_label_{i}",
            label=label_text,
            position=(pos_x + 0.18, pos_y- .2),
            color=clrs.Black,
            size=(0.28, 0.28),
            grid_id=Grid_ID.MAIN.value,
            group=GC.REEL_LABELS,
        )

def draw_locked_row_dimmers(scene, dimmed_reels):
    if not dimmed_reels:
        return
    grid = scene.grids.get(Grid_ID.MAIN.value)
    base = clrs.rgb_to_rgba(clrs.Black)
    alpha = 200
    overlay_color = (base[0], base[1], base[2], alpha)
    overlay_image = pyglet.image.SolidColorImagePattern(overlay_color).create_image(1, 1)
    # Draw one overlay per cell across all reels for each dimmed row
    for row_idx in dimmed_reels:
        for reel_idx in range(GV.HNS_COLS):
            r_x = reel_idx
            r_y = grid.y_cells - (row_idx+1)
            scene.grid_objects.delete(to_delete_sub_string=f"dimmer_{reel_idx}_{row_idx}")
            scene.grid_objects.add(
                f"dimmer_{reel_idx}_{row_idx}",
                GridSprite(
                    r_x=r_x,
                    r_y=r_y,
                    r_width=1.0,
                    r_height=1.0,
                    pict=overlay_image,
                    whiteboard=scene,
                    batch_id=BT.BASE.value,
                    group_idx=GC.REEL_LABELS - 1,
                    grid_id=Grid_ID.MAIN.value,
                ),
            )
