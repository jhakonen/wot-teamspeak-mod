from setuptools.command.build_py import build_py
import os
from glob import glob

class GenerateInFilesCommand(build_py):
    """
    Converts .py.in files to .py files.
    """

    def run(self):
        options = {name[4:]: method() for name, method in self.distribution.__dict__.iteritems() if name.startswith('get_')}
        if self.packages:
            for package in self.packages:
                package_dir = self.get_package_dir(package)
                module_files = glob(os.path.join(package_dir, "*.py.in"))
                for module_file in module_files:
                    package = package.split('.')
                    module = os.path.basename(module_file).split('.')[0]
                    outfile = self.get_module_outfile(self.build_lib, package, module)
                    self.mkpath(os.path.dirname(outfile))
                    with open(module_file, 'r') as input_file:
                        with open(outfile, 'w') as output_file:
                            output_file.write(input_file.read().format(**options))
        build_py.run(self)
