import json
import shutil
from os import makedirs, path

from scepter.get_root_path import (
    get_project_gfx_source_path,
    get_project_gfx_target_path,
    get_root_path,
)
from scepter.library.image_creation.image_creator import SymbolImageCreator
from scepter.library.image_creation.wheel_image_creator import WheelImageCreator, WheelWedge

from prototype_vibe.project_logic import project_logic


class GameGfxSymbols:
    def create(self, logic_data):
        scepter_asset_dir_path = path.join(get_root_path(), "gfx", "assets")
        # starting_point_game\scepter\scepter\gfx\assets
        source_dir_path = get_project_gfx_source_path()
        # starting_point_game\starting_point_game\project_gfx\assets
        target_dir_path = get_project_gfx_target_path()
        # starting_point_game\starting_point_game\project_gfx\generated
        makedirs(path.join(target_dir_path, "symbols"), exist_ok=True)
        # makedirs(path.join(target_dir_path, "tracksymbols"), exist_ok=True)
        pic_correspondence = {}
        sic = SymbolImageCreator()
        orig_pic = {}
        
        generate_subsymbols(source_dir_path, target_dir_path, sic)
        generate_wheel(target_dir_path, logic_data)
        
        pass
        

def generate_subsymbols(source_dir_path, target_dir_path, sic):
    symbols_source_dir = path.join(source_dir_path, "symbols")
    subsymbols_target_dir = path.join(target_dir_path, "symbols")
    makedirs(subsymbols_target_dir, exist_ok=True)
    
    if path.exists(symbols_source_dir):
        from os import listdir
        from PIL import Image, ImageDraw
        symbol_files = [f for f in listdir(symbols_source_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        for symbol_file in symbol_files:
            symbol_path = path.join(symbols_source_dir, symbol_file)
            output_file = f"subsymbol_{symbol_file}"
            try:
                bg_img = Image.open(symbol_path)
                if bg_img.mode != 'RGBA':
                    bg_img = bg_img.convert('RGBA')
                temp_bg_path = path.join(subsymbols_target_dir, f"temp_{symbol_file}")
                bg_img.save(temp_bg_path)
                
                sic.create(
                    width=100,
                    height=100,
                    color="#000000",
                    background_color=None,
                    background_image=temp_bg_path,
                    symbol_text="",
                    text_size=64,
                    output_file=output_file,
                )
                generated_img_path = path.join(subsymbols_target_dir, output_file)
                if path.exists(generated_img_path):
                    subsymbol_img = Image.open(generated_img_path)
                    width, height = subsymbol_img.size
                    draw = ImageDraw.Draw(subsymbol_img)
                    draw.rectangle(
                        [(width // 2, height // 2), (width, height)],
                        fill=(255, 0, 0)  # Red
                    )
                    subsymbol_img.save(generated_img_path, "PNG")
                
                path_module = __import__('os').path
                if path_module.exists(temp_bg_path):
                    __import__('os').remove(temp_bg_path)
            except Exception as e:
                print(f"Error processing {symbol_file}: {e}")
                
    pass

def generate_wheel(target_dir_path, logic_data):
    dir_path = path.join(target_dir_path, "wheel")

    wheel_wedges = logic_data["wheel_wedges"]
    wedge_text = wheel_wedges.results
    number_of_wedges = len(wedge_text)
    makedirs(dir_path, exist_ok=True)
    wheel_pic_correspondence = {}
    output_file = f"wheel_sprite.png"
    wheel_pic_correspondence[f"wheel_sprite"] = output_file
    for wheel_index in enumerate(wedge_text):
        if not path.exists(path.join(dir_path, output_file)):
            wedges = [WheelWedge(
                text= str(wedge_text[wedge_index]) + " ",
                text_color= "#000000",
                wedge_color= "#afffbf",
                border_color="#000000",
            ) for wedge_index in range(number_of_wedges)]
            wheel_img = WheelImageCreator().create(wedges)
            wheel_img.save(path.join(dir_path, output_file), "PNG")
    
    pass



        