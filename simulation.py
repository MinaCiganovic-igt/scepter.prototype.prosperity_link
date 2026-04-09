import multiprocessing as mp
import os
import sys

from global_variables import GlobalConfig as GV
import prototype_installer_config
from joblib import Parallel, delayed
from global_variables import BonusNames as BN

mp.freeze_support()
import pickle

from prosperity_link.project_logic.project_logic import MyLogic
from scepter.common.comm_event_loop_dispatcher import CommEventLoopDispatcher
from scepter.common.comm_objects import CommGfxLoadFromExcel
from scepter.communication_pipeline import CommunicationPipeline
from simulation_lib.sim_project_logic import play_batch ,create_fsd
from tqdm import tqdm
from scepter.common.constants import ScepterInfoType as SIT

assert prototype_installer_config, "installer_config imported for execution"

from collect_results import collect_results
from run import meters, project_dashboard_blueprint, scene_blueprints


def def_value():
    return 0

scepterinfos_to_track = {
    (SIT.BONUS_TRIGGER, BN.FREEGAME): "1_FG_",
    (SIT.BONUS_TRIGGER, BN.FREEGAME_RE_TRIG): "2_FG_Re-Trig",
    (SIT.BONUS_TRIGGER, BN.HOLDANDSPIN): "3_Hold_and_Spin",
    (SIT.BONUS_TRIGGER, BN.WHEEL): "4_Wheel",
}

def main():
    try:
        sys.argv[1]
        GV.NUM_OF_GAMES = int(sys.argv[1])
    except:
        GV.NUM_OF_GAMES = 100000 #bilo 1_000_000
    GV.NUM_OF_BATCHES = int(GV.NUM_OF_GAMES / GV.BATCH_SIZE) 
    
    mylogic = MyLogic(meters=meters)
    gameparts = mylogic.gameparts
    
    comm_pipeline = CommunicationPipeline(
        CommEventLoopDispatcher(),
        CommEventLoopDispatcher(),
        play_logic=mylogic,
        scepterinfos_to_track=scepterinfos_to_track,
        project_name="Vibe Template Game",
        width=610,
        scene_blueprints=scene_blueprints,
        dashboard_blueprint=project_dashboard_blueprint,
    )

    comm_pipeline.core_communication_layer.playmode_handler.active_playmode.load_xls(load_xls_obj=CommGfxLoadFromExcel())

    excel_data_dict = comm_pipeline.core_communication_layer.playmode_handler.active_playmode.logic.data
    exceL_path = comm_pipeline.core_communication_layer.playmode_handler.active_playmode.logic.excel_path

    for folder_name in ["batch_results", "sibl_files"]:
        try:
            os.makedirs(folder_name)
        except:
            pass

    if GV.PARALLEL_COMPUTING and not GV.CREATE_OUTCOMES and not GV.PRIZE_FIRST:
        inputs_zip = zip(
            [i for i in range(GV.NUM_OF_BATCHES)],
            [excel_data_dict for _ in range(GV.NUM_OF_BATCHES)],
            [gameparts for _ in range(GV.NUM_OF_BATCHES)],
        )
        if os.cpu_count() < 60:
            with mp.Pool(processes=int(os.cpu_count())) as pool:
                pool.starmap(
                    play_batch,
                    tqdm(
                        inputs_zip,
                        total=GV.NUM_OF_BATCHES,
                        desc="Outcomes computation",
                    ),
                    chunksize=1,
                )
        else:
            Parallel(n_jobs = -1)(delayed(play_batch)(*inputs) for inputs in tqdm(inputs_zip, total=GV.NUM_OF_BATCHES, desc="Outcomes computation",))
    else:
        for batch_id in range(GV.NUM_OF_BATCHES):
            print("batch_id", batch_id)
            play_batch(batch_id, excel_data_dict, gameparts)

    
    # RESULT COLLECTION

    if GV.PRIZE_FIRST and GV.CREATE_OUTCOMES:
        with open(f"outcomes_dict.pkl", "wb") as f:
            pickle.dump(GV.OUTCOMES_DICT, f)
        create_fsd("Template_Final_Seed_Data_L25C1TB25.csv")
        
    else:
        collect_results(excel_path=exceL_path)


if __name__ == "__main__":
    main()
