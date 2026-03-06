# Copyright IGT 2022

import argparse
import json
import os
import string
import sys

import prototype_installer_config

GAME = prototype_installer_config.GAME


def GetReleaseLabel():
    return "SCEPTER_PROTOTYPE_" + GAME.upper()


def get_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--version", dest="version")
    parser.add_argument("--template", dest="infile")
    parser.add_argument("--output", dest="output")
    args = parser.parse_args()
    return args


def main():
    # Use utf-8 for all outputs to stdout and stderr.
    sys.stdout.reconfigure(encoding="utf-8", errors="surrogateescape")
    sys.stderr.reconfigure(encoding="utf-8", errors="surrogateescape")

    args = get_arguments()

    with open(args.infile) as f:
        template = string.Template(f.read())

    result = template.safe_substitute(
        product_name=json.dumps(GAME),
        version=json.dumps(args.version),
        mfw_tag=json.dumps(GetReleaseLabel()),
        install_package=json.dumps(
            os.path.join(os.getenv("DIST_DIR"), f"{GAME}_setup_{args.version}.exe")
        ),
    )

    with open(args.output, mode="w") as f:
        f.write(result)

    return 0


if __name__ == "__main__":
    returncode = main()
    sys.exit(returncode)
