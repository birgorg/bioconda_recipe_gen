import pkg_resources


class BuildScript:
    """ Represents a build.sh """

    def __init__(self, name, path, template, filesystem):
        self.name = name
        self._path = path
        self._lines = list()
        self._filesystem = filesystem

        build_template_file = pkg_resources.resource_filename(
            __name__, "recipes/%s" % template
        )
        with open(build_template_file, "r") as template:
            self._lines = template.readlines()

    def __eq__(self, other):
        """ Overwrite default implementation. Compare _lines instead of id """
        if isinstance(other, BuildScript):
            return self._lines == other._lines
        return False

    @property
    def path(self):
        return self._path

    @property
    def filesystem(self):
        return self._filesystem

    def write_build_script_to_file(self):
        """ Write build script to path/build.sh """
        lines_to_write = ['#!/bin/bash\n'] + self._lines
        with open("%s/build.sh" % self._path, 'w') as fp:
            for line in lines_to_write:
                fp.write(line + "\n")

    def add_cmake_flags(self, flags):
        """ Add flags to the cmake call """
        for i, line in enumerate(self._lines):
            if line.startswith("cmake .."):
                self._lines[i] = "cmake .. %s" % flags

    def add_moving_bin_files(self):
        """ Add lines to make sure the bin files are moved """
        self._lines.append("mkdir -p $PREFIX/bin")
        self._lines.append("cp bin/%s $PREFIX/bin" % self.name)
