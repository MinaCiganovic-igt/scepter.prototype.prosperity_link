# Copyright IGT 2021

import os
import shutil
import subprocess
import sys

from cx_Freeze import Executable, setup

import prototype_installer_components.derived_objects


def check_clean_git_working_directory():
    cmd = ["git", "status", "--porcelain"]
    proc = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=False
    )
    out, _ = proc.communicate()
    output = out.strip().decode("utf-8")

    if output != "":
        raise ChildProcessError(
            "You have uncommitted changes. "
            "Please clean up your working directory and try again."
        )


def check_unpushed_changes():
    cmd = ["git", "log", "origin/master..HEAD"]
    proc = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=False
    )
    out, _ = proc.communicate()
    output = out.strip().decode("utf-8")

    if output != "":
        raise ChildProcessError(
            "You have unpushed changes. " "Please push your commits and try again."
        )


def check_matching_tag(tag_name):
    cmd = ["git", "tag", "--points-at", "HEAD"]
    proc = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=False
    )
    out, _ = proc.communicate()
    output = out.strip().decode("utf-8").split()

    if tag_name not in output:
        raise ChildProcessError(
            "The release version does not match any tags. "
            "Please make sure you have checked out the revision with the tag and try again."
        )


def check_unpushed_tags():
    cmd = ["git", "push", "--tags", "--dry-run"]
    proc = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=False
    )
    _, err = proc.communicate()
    output = err.strip().decode("utf-8").split("\n")
    print(output)

    if len(output) != 1 or output[0] != "Everything up-to-date":
        raise ChildProcessError(
            "You have unpushed tags. " "Please push your tags and try again."
        )


def add_batch_file_content(game, file):
    # flnm = os.path.splitext(file)[0]
    pth = os.path.join("C:\\", "MathConcepts", game, file)
    ret = pth
    ret += "\npause"
    return ret


def build_exe(args=sys.argv[1:]):
    target_dir = os.path.join("dist", "instkit")
    temp_dir = os.path.join("dist", "temp")
    game, release_version, py_executable_pairs, include_files, exclude_files = args[1:]

    for py_exe_pair in py_executable_pairs:
        batch_file = ".".join((os.path.splitext(py_exe_pair[1])[0], "bat"))
        batch_file_path = os.path.join(temp_dir, batch_file)
        os.makedirs(os.path.dirname(batch_file_path), exist_ok=True)
        open(batch_file_path, "w").write(add_batch_file_content(game, py_exe_pair[1]))
        include_files.append(
            (batch_file_path, os.path.join("{}_assets".format(game), batch_file))
        )

    if os.getenv("GITHUB_ACTIONS") is None:
        check_clean_git_working_directory()
        check_matching_tag(release_version)
        check_unpushed_changes()
        check_unpushed_tags()

    print(("Following files included: ", include_files))
    print(("Following files excluded: ", exclude_files))

    build_exe_options = {
        "excludes": [],
        "bin_excludes": exclude_files,
        "include_files": include_files,
        "build_exe": target_dir,
        "packages": [
            "idna",
            "idna.idnadata",
        ],
        "zip_includes": [],
        "zip_include_packages": None,  # "*",
        "zip_exclude_packages": [],
        # we don't want to rely that the correct msvcr is installed, thus include it ...
        "include_msvcr": True,
        "optimize": 1,  # we cannot use optimize=2 here, because numpy needs the doc strings :(
    }
    sys.path.insert(0, os.getcwd())
    env_path = (
        os.path.join(
            os.getenv("ENVKIT_ENVROOT"),
            *[path_component.strip(":") for path_component in os.getcwd().split(os.sep)]
        )
        if os.getenv("ENVKIT_ENVROOT") is not None
        else ""
    )
    setup(
        name=prototype_installer_components.derived_objects.PROGRAM_NAME,
        version=release_version,
        description=prototype_installer_components.derived_objects.PROGRAM_DESCRIPTION,
        options={"build_exe": build_exe_options},
        executables=[
            Executable(py_exe_pair[0], target_name=py_exe_pair[1])
            for py_exe_pair in py_executable_pairs
        ]
        + [
            Executable(
                os.path.join(
                    env_path,
                    ".py3_conda",
                    "scepter_env",
                    "Lib",
                    "site-packages",
                    "scepter",
                    "gfx",
                    "entrypoint",
                    "open_helpscreen.py",
                ),
                target_name="open_helpscreen.exe",
            )
        ],
        packages=[],
        script_args=[args[0]],
    )
    shutil.copy(
        os.path.join(os.path.dirname(sys.executable), "vcruntime140_1.dll"),
        os.path.join(target_dir, "lib"),
    )
