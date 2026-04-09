import prototype_installer_config
from prosperity_link.project_gfx.scene_wheel import SceneWheel
import pyglet
from global_variables import GlobalConfig as GV
import pickle
from global_variables import BonusNames as BN
from prosperity_link.project_gfx.scene_basegame import SceneBaseGame
from prosperity_link.project_gfx.scene_freegame import SceneFreeGame
from prosperity_link.project_gfx.scene_holdandspin import SceneHoldAndSpin
from prosperity_link.project_logic.project_logic import MyLogic
from scepter.common.comm_event_loop_dispatcher import CommEventLoopDispatcher
from scepter.common.comm_objects import CommGfxLoadFromExcel
from scepter.common.constants import MeterConstants as MC
from scepter.common.constants import ScepterInfoType as SIT
from scepter.communication_pipeline import CommunicationPipeline
from scepter.core.logic.meter import Meter
from scepter.gfx.dashboard.dashboard import DashboardBlueprint, DashboardParameters
from scepter.gfx.scenes.scene_handler import SceneBlueprint, SceneParameters
from scepter.trigger_handler import TriggerHandler
from prosperity_link.project_gfx.project_image_creation import (
    GameGfxSymbols,
)

assert prototype_installer_config, "installer_config imported for execution"

# i am just testing if i have access to make changes to the repo
meters = {
    mc: Meter()
    for mc in [
        "RANDOM_SEED",
        MC.CREDITS, 
        MC.WIN, 
        MC.TOTAL_BET, 
        MC.FREE_GAMES, 
        MC.SPIN_COUNTER,
    ]
}

class ImageGenerator:
    def __init__(self, data_getter=lambda: None):
        self.__symbols = GameGfxSymbols()
        self.__data_getter = data_getter

    def create(self):
        self.__symbols.create(self.__data_getter())

# SILENT TRIGGERS

trigger_handler = TriggerHandler()

trigger_handler.add_trigger(
    pyglet.window.key._1, 0, helptext=f"any_win",
    callback=lambda sib: (any([(f"any_win" in si.id) for si in sib.scepterinfos])),
)
trigger_handler.add_trigger(
    pyglet.window.key._2, 0, helptext=f"bg_tension_spin",
    callback=lambda sib: (any([(f"bg_tension_spin" in si.id) for si in sib.scepterinfos])),
)
trigger_handler.add_trigger(
    pyglet.window.key._3, 0, helptext=f"fg_tension_spin",
    callback=lambda sib: (any([(f"fg_tension_spin" in si.id) for si in sib.scepterinfos])),
)
trigger_handler.add_trigger(
    pyglet.window.key._4, 0, helptext=f"trigger_fg",
    callback=lambda sib: (any([(f"trigger_fg" in si.id) for si in sib.scepterinfos])),
)
trigger_handler.add_trigger(
    pyglet.window.key._5, 0, helptext=f"retrigger_fg",
    callback=lambda sib: (any([(f"retrigger_fg" in si.id) for si in sib.scepterinfos])),
)
trigger_handler.add_trigger(
    pyglet.window.key._6, 0, helptext=f"trigger_has_from_bg",
    callback=lambda sib: (any([(f"trigger_has_from_bg" in si.id) for si in sib.scepterinfos])),
)
trigger_handler.add_trigger(
    pyglet.window.key._7, 0, helptext=f"trigger_has_from_fg",
    callback=lambda sib: (any([(f"trigger_has_from_fg" in si.id) for si in sib.scepterinfos])),
)
trigger_handler.add_trigger(
    pyglet.window.key._8, 0, helptext=f"full_grid_has",
    callback=lambda sib: (any([(f"full_grid_has" in si.id) for si in sib.scepterinfos])),
)
trigger_handler.add_trigger(
    pyglet.window.key._9, 0, helptext=f"trigger_bn",
    callback=lambda sib: (any([(f"trigger_bn" in si.id) for si in sib.scepterinfos])),
)
    
# SCENE AND DASHBOARD

scene_blueprints = {
    BN.BASEGAME: SceneBlueprint(
        scene_class=SceneBaseGame,
        scene_parameters=SceneParameters(
            special_meter_batches=["BASE"],
        )
    ),
    BN.FREEGAME: SceneBlueprint(
        scene_class=SceneFreeGame,
        scene_parameters=SceneParameters(
            special_meter_batches=["BASE", "FREEGAMES"],
        )
    ),
    BN.HOLDANDSPIN: SceneBlueprint(
        scene_class=SceneHoldAndSpin,
        scene_parameters=SceneParameters(
            special_meter_batches=["BASE", "HOLDANDSPIN"],
        )
    ),
    BN.WHEEL: SceneBlueprint(
        scene_class=SceneWheel,
        scene_parameters=SceneParameters(
            special_meter_batches=["BASE", "WHEEL"],
        )
    ),
}


project_dashboard_blueprint = DashboardBlueprint(
    dashboard_parameters=DashboardParameters(
        count_rows_lower_meter_section=1,
        count_rows_upper_meter_section=1,
    ),
    lower_board_meters=[
        (MC.FREE_GAMES, "FGs", 0, -1, 1, "FREEGAMES"),
        (MC.SPIN_COUNTER, "Spins", 0, -1, 1, "HOLDANDSPIN"),
    ],
    upper_board_meters=[
        ("RANDOM_SEED", "Random Seed", 0, -3, 3, "BASE"),
    ],
)

scepterinfos_to_track = {
    (SIT.BONUS_TRIGGER, BN.FREEGAME): "1_FG_",
    (SIT.BONUS_TRIGGER, BN.FREEGAME_RE_TRIG): "2_FG_Re-Trig",
    (SIT.BONUS_TRIGGER, BN.HOLDANDSPIN): "3_Hold_and_Spin",
    (SIT.BONUS_TRIGGER, BN.WHEEL): "4_Wheel",
}

def main():
    GV.MACHINE_BUILD = False
    
    if GV.PRIZE_FIRST and not GV.CREATE_OUTCOMES:
        with open(f"outcomes_dict.pkl", "rb") as f:
            GV.OUTCOMES_DICT = pickle.load(f)
        
    mylogic = MyLogic(meters=meters)

    comm_pipeline = CommunicationPipeline(
        CommEventLoopDispatcher(),
        CommEventLoopDispatcher(),
        play_logic=mylogic,
        scepterinfos_to_track=scepterinfos_to_track,
        project_name="Vibe Template Game",
        width=610,
        # width=1050,
        scene_blueprints=scene_blueprints,
        dashboard_blueprint=project_dashboard_blueprint,
    )

    comm_pipeline.core_communication_layer.playmode_handler.active_playmode.load_xls(load_xls_obj=CommGfxLoadFromExcel())

    symbolgenerator = ImageGenerator(lambda: mylogic.data)
    symbolgenerator.create()
    
    entry_point = comm_pipeline.gfx_communication_layer.entrypoint
    entry_point.set_visible(True)
    dashboard = entry_point.dashboard
    dashboard.update_visualization_of_meters({mn: int(mylogic.meters[mn].value) for mn in meters if mn!="FREE_GAMES_PLAYED"})

    def update_stake_change():
        pass

    entry_point.add_update_on_stake_change(update_stake_change)

    for stktp, _ in mylogic.stake_options.iter_selection(): 
        dashboard.add_stake_control(
            caption=stktp,
            value=0,
            callback=entry_point.deliver,
        )

    for trigger in trigger_handler.triggers:
        comm_pipeline.add_trigger(
            trigger["symbol"],
            trigger["modifiers"],
            trigger["helptext"],
            trigger["callback"],
        )

    comm_pipeline.establish_connection()
    pyglet.app.run()


if __name__ == "__main__":
    main()
