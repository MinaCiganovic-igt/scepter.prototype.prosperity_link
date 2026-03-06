# Copyright IGT 2021

import os
import sys

from mdk_updater import installers

import prototype_installer_components.derived_objects
import prototype_installer_config

GAME = prototype_installer_config.GAME
RELEASE_VERSION = prototype_installer_config.RELEASE_VERSION

SETUP_EXECUTABLE = "{}_setup_{}.exe".format(
    GAME,
    RELEASE_VERSION,
)


def ListFiles():
    with open(os.path.join("dist", "instkit", "frozen_files.txt"), "w") as o:
        cwd = os.path.join(os.getcwd(), "dist", "instkit")
        for root, dirs, files in os.walk(cwd, topdown=False):
            for name in files:
                file_relpath = os.path.join(os.path.relpath(root, cwd), name)
                print(file_relpath)
                o.write("%s\n" % file_relpath)


def CreateInstaller():
    ListFiles()
    installer = installers.NsisInstaller()
    conf = installers.InstallerConfig()
    conf.ProgramName = prototype_installer_components.derived_objects.PROGRAM_NAME
    conf.VersionName = RELEASE_VERSION
    conf.InputDir = os.path.join("dist", "instkit")
    conf.OutputFile = os.path.join("dist", SETUP_EXECUTABLE)

    conf.DefaultTargetPath = os.path.join(
        os.path.normpath(os.getenv("SYSTEMDRIVE", "C:")),
        os.sep,
        "MathConcepts",
        conf.ProgramName,
    )

    conf.ProgramExecutable = prototype_installer_config.PROGRAM_EXECUTABLE_0

    conf.StartMenuFolder = None
    conf.HeaderBitmap = None
    conf.HeaderBitmapRight = True
    conf.SuppressLocationSelection = True
    conf.installer_configMajor = RELEASE_VERSION
    conf.Comments = prototype_installer_components.derived_objects.PROGRAM_DESCRIPTION

    conf.AdditionalCleanupFiles = []
    conf.URIProtocolHandlers = []
    return installer.MakeInstallerExt(conf)


def DeleteTemporaryFiles():
    dir_name = os.path.join(
        os.getcwd(),
        "dist",
        "temp",
    )
    dir_content = os.listdir(dir_name)
    for item in dir_content:
        os.remove(os.path.join(dir_name, item))
    os.rmdir(dir_name)


if __name__ == "__main__":
    if "--create-frozen-files-list" in sys.argv:
        sys.exit(ListFiles())
    if "--create-installer" in sys.argv:
        CreateInstaller()
        sys.exit(DeleteTemporaryFiles())
