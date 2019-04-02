import os
import sys
from shutil import copyfile, rmtree
import pkg_resources

from . import build
from . recipe import Recipe


def return_hello():
    """ This is a test function for our unittest setup and should be removed when we start using the test setup"""
    return "hello"


def main(bioconda_recipe_path):
    # Setup variables
    name = "kallisto2"
    src = "https://github.com/pachterlab/kallisto/archive/v0.45.0.tar.gz"
    path = "%s/recipes/%s" % (bioconda_recipe_path, name)

    os.mkdir(path)

    # Copy recipe to into Bioconda
    resource_package = __name__
    resource_path = '/'.join(('recipes','meta.yaml'))
    meta_template = pkg_resources.resource_string(resource_package, resource_path)
    with open('%s/%s' % (path, 'meta.yaml'), 'wb') as fp:
        fp.write(meta_template)
    resource_path = '/'.join(('recipes','build.sh'))
    build_template = pkg_resources.resource_string(resource_package, resource_path)
    with open('%s/%s' % (path, 'build.sh'), 'wb') as fp:
        fp.write(build_template)
    try:
        recipe = Recipe(path + "/meta.yaml")

        proc = build.bioconda_utils_build(name, bioconda_recipe_path)
        for line in proc.stdout.split("\n"):
            print(line)
        print("return code: " + str(proc.returncode) + "\n")
        if proc.returncode != 0:
            # Check for dependencies
            for line in proc.stdout.split("\n"):
                line_norma = line.lower()
                if "missing" in line_norma:
                    print(line_norma)
                    if "hdf5" in line_norma:
                        recipe.add_requirement("hdf5", "host")

            # after new requirements are added: write new recipe to meta.yaml
            recipe.write_recipe_to_meta_file()
        else:
            print("Build succeded")
            sys.exit(0)

        # TODO: Try to iterate alpine image build
        proc = build.alpine_build(src)
        for line in proc.stdout.split("\n"):
            print(line)

        proc = build.bioconda_utils_build(name, bioconda_recipe_path)
        for line in proc.stdout.split("\n"):
            print(line)
    finally:
        # clean up
        rmtree(path)
