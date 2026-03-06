import os
import sys

from scepter import installer_config

GAME = os.path.basename(os.getcwd()).split(".")[-1]
installer_config.GAME = GAME
RELEASE_VERSION = os.getenv("RELEASE_VERSION")

PROGRAM_EXECUTABLE_0 = f"play_{GAME}.exe"
PROGRAM_EXECUTABLE_1 = f"simulation.exe"
PROGRAM_EXECUTABLE_2 = f"calculation.exe"
PROGRAM_EXECUTABLE_3 = f"machine_build.exe"

ALL_PY_FILES_TO_EXECUTABLE_PAIRS = (
    ("run.py", PROGRAM_EXECUTABLE_0),
    ("simulation.py", PROGRAM_EXECUTABLE_1),
    ("calculation.py", PROGRAM_EXECUTABLE_2),
    ("machine_build.py", PROGRAM_EXECUTABLE_3),
)
##############################################################
# A batch file for each executable will automatically be added to the {GAME}_assests folder
# Don't add them manually to the include_files_without_executable_batch_files
include_files_without_executable_batch_files = [
    (
        os.path.join("{}".format(GAME), "protoype_belgrade.xlsm"),
        os.path.join("{}_assets".format(GAME), "protoype_belgrade.xlsm"),
    ),
]

exclude_files = []

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "spec":
        import prototype_installer_components.spec

        prototype_installer_components.spec.build_exe(
            [
                "build_exe",
                GAME,
                RELEASE_VERSION,
                ALL_PY_FILES_TO_EXECUTABLE_PAIRS,
                include_files_without_executable_batch_files,
                exclude_files,
            ]
        )
    if len(sys.argv) > 1 and sys.argv[1] == "makeinst":
        import prototype_installer_components.make_installer

        prototype_installer_components.make_installer.CreateInstaller()
        sys.exit(prototype_installer_components.make_installer.DeleteTemporaryFiles())
