import hashlib
import os
import io
import tarfile
import subprocess
import logging
import docker
from shutil import rmtree, copy2
from copy import deepcopy
from .utils import copytree
from .str_to_pkg import str_to_pkg


def bioconda_utils_build(package_name, bioconda_recipe_path):
    """ Build a bioconda package with bioconda-utils and return the standard output
    
    Args:
        package_name: Name of the package to build
    """
    wd = os.getcwd()
    os.chdir(bioconda_recipe_path)
    cmd = [
        "bioconda-utils",
        "build",
        "recipes/",
        "config.yml",
        "--packages",
        package_name,
    ]
    proc = subprocess.run(cmd, encoding="utf-8", stdout=subprocess.PIPE)
    os.chdir(wd)
    return proc


def mini_build_setup(recipe, build_script):
    """ Write build.sh and meta.yaml recipe path. """
    recipe.write_recipe_to_meta_file()
    build_script.write_build_script_to_file()
    os.mkdir("%s/output" % recipe.path)


def run_conda_build_mini(recipe_path, build_only=True):
    """ Run docker run and build the package in a docker mini image"""
    # Setup image
    client = docker.from_env()
    # Run docker image
    flag = "--build-only" if build_only else ""
    container = client.containers.run(
        "perhogfeldt/conda-build-mini:latest",
        "conda build %s --output-folder /home/output /mnt/recipe " % flag,
        volumes={recipe_path: {"bind": "/mnt/recipe", "mode": "ro"}},
        detach=True,
    )
    result = container.wait()
    stdout = container.logs().decode("utf-8")
    if result["StatusCode"] is 0:
        for line in stdout.split("\n"):
            if "anaconda upload " in line:
                output_file = line.split()[2]
                stream, info = container.get_archive(output_file)
                fd = io.BytesIO()
                for b in stream:
                    fd.write(b)
                fd.seek(0)
                tar_file = tarfile.open(mode="r", fileobj=fd)
                tar_file.extractall("%s/output" % recipe_path)
    container.remove()
    return (result, stdout)


def run_conda_build_mini_test(recipe_path):
    """ Call run_mini_build with the build_only parameter as False """
    return run_conda_build_mini(recipe_path, False)


def mini_iterative_build(recipe, build_script):
    """ Build a bioconda package with a Docker mini image and try to find missing packages,
        return a tupple with the last standard output and a list of found dependencies.
    
    Args:
        src: A link to where the source file can be downloaded
    """

    mini_build_setup(recipe, build_script)
    print("mini setup done")
    c = 0
    new_recipe = deepcopy(recipe)
    return_code = 1
    while return_code != 0:
        result, stdout = run_conda_build_mini(recipe.path)
        for line in stdout.split("\n"):
            line_normalized = line.lower()
            print(line)
            for err_msg, (pkg_name, dep_type) in str_to_pkg.items():
                if err_msg in line_normalized:
                    new_recipe.add_requirement(pkg_name, dep_type)

        if new_recipe == recipe:
            break
        else:
            recipe = deepcopy(new_recipe)
            recipe.write_recipe_to_meta_file()
        return_code = result["StatusCode"]
        c += 1
        print("%s iteration" % c)

        if not logging.getLogger().disabled:
            src = "%s/output" % recipe.path
            dst = "%s/debug_output_files/build_iter%d" % (recipe.path, c)
            os.mkdir(dst)
            copytree(src, dst)

    return ((result, stdout), recipe, build_script)


def mini_iterative_test(recipe, build_script):
    print("mini iterative test started")
    new_recipe = deepcopy(recipe)
    new_build_script = deepcopy(build_script)
    c = 0
    return_code = 1
    while return_code != 0:
        result, stdout = run_conda_build_mini_test(recipe.path)
        for line in stdout.split("\n"):
            line_normalized = line.lower()
            print(line)
            for err_msg, (pkg_name, dep_type) in str_to_pkg.items():
                if err_msg in line_normalized:
                    new_recipe.add_requirement(pkg_name, dep_type)

            if "%s: command not found" % recipe.name in line_normalized:
                new_build_script.add_moving_bin_files()

        if new_recipe == recipe and new_build_script == build_script:
            break
        else:
            recipe = deepcopy(new_recipe)
            recipe.write_recipe_to_meta_file()
            build_script = deepcopy(new_build_script)
            build_script.write_build_script_to_file()
        return_code = result["StatusCode"]
        c += 1
        print("%s iteration" % c)

    if not logging.getLogger().disabled:
        src = "%s/output" % recipe.path
        dst = "%s/debug_output_files/test_iter1" % recipe.path
        os.mkdir(dst)
        copytree(src, dst)

    return (result, stdout), recipe


def mini_sanity_check(bioconda_recipe_path, recipe):
    """ Copy build.sh and meta.yaml templates to cwd. Return a Recipe object based on the templates. """
    recipe.increment_build_number()
    temp_folder_name = hashlib.md5(recipe.name.encode("utf-8")).hexdigest()
    recipes_pkg_path = "%s/recipes/%s/" % (bioconda_recipe_path, temp_folder_name)
    try:
        os.mkdir(recipes_pkg_path)
        current_recipe_path = "%s/%s/" % (os.getcwd(), recipe.name)

        for item in os.listdir(current_recipe_path):
            s = os.path.join(current_recipe_path, item)
            d = os.path.join(recipes_pkg_path, item)

            if not os.path.isdir(s):
                copy2(s, d)
            elif item != "output":
                copytree(s, d)

        # Try to build the package
        proc = bioconda_utils_build(temp_folder_name, bioconda_recipe_path)
        for line in proc.stdout.split("\n"):
            print(line)
        if proc.returncode == 0:
            return True
        else:
            return False
    finally:
        rmtree(recipes_pkg_path)
