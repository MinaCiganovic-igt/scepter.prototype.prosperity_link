import pickle

from global_variables import GlobalConfig as GV
import prototype_installer_config
import pyglet
from global_variables import BonusNames as BN
from prototype_vibe.project_gfx.scene_basegame import SceneBaseGame
from prototype_vibe.project_gfx.scene_freegame import SceneFreeGame
from prototype_vibe.project_logic.project_logic import MyLogic
from run import meters, project_dashboard, scenes, trigger_handler
from scepter.common.comm_event_loop_dispatcher import CommEventLoopDispatcher
from scepter.common.comm_objects import CommGfxLoadFromExcel
from scepter.common.constants import MeterConstants as MC
from scepter.communication_pipeline import CommunicationPipeline
from scepter.core.logic.meter import Meter
from scepter.gfx.dashboard.dashboard import Dashboard
from scepter.trigger_handler import TriggerHandler

assert prototype_installer_config, "installer_config imported for execution"

def main():
    GV.MACHINE_BUILD = True
    
    if GV.PRIZE_FIRST and not GV.CREATE_OUTCOMES:
        with open(f"outcomes_dict.pkl", "rb") as f:
            GV.OUTCOMES_DICT = pickle.load(f)
        
    mylogic = MyLogic(meters=meters)

    comm_pipeline = CommunicationPipeline(
        CommEventLoopDispatcher(),
        CommEventLoopDispatcher(),
        play_logic=mylogic,
        scepterinfos_to_track={},
        project_name="Vibe Template Game",
        width=550,
        scenes=scenes,
        dashboard=project_dashboard,
    )

    comm_pipeline.core_communication_layer.playmode_handler.active_playmode.load_xls(load_xls_obj=CommGfxLoadFromExcel())

    entry_point = comm_pipeline.gfx_communication_layer.entrypoint
    entry_point.set_visible(True)
    dashboard = entry_point.dashboard
    dashboard.update_visualization_of_meters({mn: int(mylogic.meters[mn].value) for mn in meters})

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
