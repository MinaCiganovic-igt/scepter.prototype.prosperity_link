# Copyright IGT 2018 - 2019

import datetime
import os
import shutil
import sys

import prototype_installer_config

GAME = prototype_installer_config.GAME


def DeployInstaller():
    installers_folder = r"\\bswntp12\\prod\\Team\\SW Tools\\Public\\Scepter\\installers"
    release_version = os.getenv("RELEASE_VERSION")
    src_installer = os.path.join("dist", f"{GAME}_setup_{release_version}.exe")
    dest_installer = os.path.join(
        installers_folder, GAME, f"{GAME}_setup_{release_version}.exe"
    )
    try:
        with open(
            os.path.join(installers_folder, "deployments.txt"), "a"
        ) as deployments_file:
            deployments_file.write(
                f"{datetime.datetime.utcnow()}, {GAME}, {release_version}\n"
            )
    except Exception as e:
        print("Exception on updating deployment list:")
        print(e)
        return 1
    try:
        os.makedirs(os.path.dirname(dest_installer), exist_ok=True)
        shutil.copyfile(src_installer, dest_installer)
    except Exception as e:
        print("Exception on deploying installer:")
        print(e)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(DeployInstaller())
