import multiprocessing as mp
import os
import sys

from global_variables import GlobalConfig as GV
import prototype_installer_config
from joblib import Parallel, delayed

mp.freeze_support()
import pickle

from prototype_vibe.project_logic.project_logic import MyLogic
from scepter.common.comm_event_loop_dispatcher import CommEventLoopDispatcher
from scepter.common.comm_objects import CommGfxLoadFromExcel
from scepter.communication_pipeline import CommunicationPipeline
from simulation_lib.sim_project_logic import play_batch ,create_fsd
from tqdm import tqdm
import random
assert prototype_installer_config, "installer_config imported for execution"
import numpy as np
from collect_results import collect_results
from run import meters, project_dashboard, scenes

from autotuning_lib.calculate_base import calculate_reelstrip_at, NUM_WEIGHTSTRIPS, calculate_desirability, return_better_desirability, overall_calculation, write_result


def def_value():
    return 0

def main():

    mylogic = MyLogic(meters=meters)
    gameparts = mylogic.gameparts

    comm_pipeline = CommunicationPipeline(
        CommEventLoopDispatcher(),
        CommEventLoopDispatcher(),
        play_logic=mylogic,
        scepterinfos_to_track={},
        project_name="Vibe Template Game",
        width=900,
        scenes=scenes,
        dashboard=project_dashboard,
    )

    comm_pipeline.core_communication_layer.playmode_handler.active_playmode.load_xls(load_xls_obj=CommGfxLoadFromExcel())

    excel_data_dict = comm_pipeline.core_communication_layer.playmode_handler.active_playmode.logic.data
    exceL_path = comm_pipeline.core_communication_layer.playmode_handler.active_playmode.logic.excel_path

    reelstrip = excel_data_dict["reelsets"]["Base Game"][0]
    reelstrip_shape = np.shape(reelstrip)
    at_weightstrips = [np.ones((reelstrip_shape[0], reelstrip_shape[1])) for _ in range(NUM_WEIGHTSTRIPS)]

    changes = {}
    for base_idx in range(NUM_WEIGHTSTRIPS):
        changes[base_idx] = []
        for reel_idx in range(reelstrip_shape[0]):
            for row_idx in range(reelstrip_shape[1]):
                changes[base_idx].append((reel_idx, row_idx))
                # at_weightstrips[base_idx][reel_idx][row_idx] = random.choice([30, 50, 100])
    step = 0
    while True:
        for base_idx in range(NUM_WEIGHTSTRIPS):
            write_result(at_weightstrips)
            step_calculation = []
            print(f"Calculating step {step}")
            # for weightstrip in at_weightstrips:
            #     step_calculation.append(calculate_reelstrip_at(excel_data_dict, reelstrip, weightstrip))
            inputs_zip = zip(
                [excel_data_dict for _ in at_weightstrips],
                [reelstrip for _ in at_weightstrips],
                at_weightstrips,
            )
            if os.cpu_count() < 60:
                with mp.Pool(processes=int(os.cpu_count())) as pool:
                    step_calculation = pool.starmap(
                        calculate_reelstrip_at,
                        inputs_zip,
                    )
            else:
                step_calculation = Parallel(n_jobs = -1)(delayed(calculate_reelstrip_at)(*inputs) for inputs in inputs_zip)
            print(overall_calculation(step_calculation))
            step_desirability = calculate_desirability(step_calculation)
            print("step_desirability", step_desirability)
            # for change in changes_to_apply:
            #     return_better_desirability(base_idx, excel_data_dict, step_calculation, step_desirability, change, reelstrip, at_weightstrips)
            changes_to_apply = changes[base_idx]
            inputs_zip = zip(
                [base_idx for _ in changes_to_apply],
                [excel_data_dict for _ in changes_to_apply],
                [step_calculation for _ in changes_to_apply],
                [step_desirability for _ in changes_to_apply],
                changes_to_apply,
                [reelstrip for _ in changes_to_apply],
                [at_weightstrips for _ in changes_to_apply],
            )
            if os.cpu_count() < 60:
                with mp.Pool(processes=int(os.cpu_count())) as pool:
                    outputs = pool.starmap(
                        return_better_desirability,
                        tqdm(
                            inputs_zip,
                            total=len(changes[base_idx]),
                            desc="Calculating all changes for a base",
                        ),
                        chunksize=1,
                    )
            else:
                outputs = Parallel(n_jobs = -1)(delayed(return_better_desirability)(*inputs) for inputs in tqdm(inputs_zip, total=len(changes[base_idx]), desc="Calculating all changes for a base",))
            for (reel_idx, row_idx), change in outputs:
                at_weightstrips[base_idx][reel_idx][row_idx] = at_weightstrips[base_idx][reel_idx][row_idx] * (1 + change)
                at_weightstrips[base_idx][reel_idx] = at_weightstrips[base_idx][reel_idx] / np.sum(at_weightstrips[base_idx][reel_idx])
            write_result(at_weightstrips)
            step += 1

if __name__ == "__main__":
    main()
