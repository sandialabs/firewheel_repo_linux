#!/usr/bin/env python
import os
import sys
import json
import time
import tarfile
from subprocess import PIPE, Popen


# pylint: disable=useless-object-inheritance
class InstallDebs(object):
    """
    This VM Resource enables the installation of Debian packages on a given VM.
    This VMR has largely been replaced by the newer (but less configurable)
    ``install_debs.sh``.
    """

    dependency = False

    def __init__(self, ascii_file=None, binary_file=None):
        """
        Decompress the tarball of packages and read in any configuration.

        Arguments:
            ascii_file (str): A path to a JSON file which contains some possible
                configuration information.
            binary_file (str): A path to a tar-compressed file containing the debian
                packages which should be installed.

        Examples:
            An example configuration file::

                {
                    "dependency": "<path to file>",
                    "environment": "<string of environment variables>",
                }

            The ``dependency`` is the path to a file which is required to exist
            prior to the installation of the debian files. This could be useful
            if there are potential race conditions amongst VMRs.
            The ``environment`` is the environment which should be passed into the
            shell which executes the ``dpkg`` command.

        """
        # Split on '.' in an attempt to get the name of the binary
        # file without extensions. Binary files don't need extensions
        # though so default to just the binary_file name
        package_name = os.path.basename(binary_file)
        if "." in package_name:
            package_name = package_name.split(".")[0]

        self.touch_location = "/tmp/%s-installed" % package_name
        self.install_dir = "/tmp/%s-agent-install" % package_name
        self.untared_dir_name = package_name

        # don't need to check from /tmp/agents since this agent
        # is currently running there
        if not os.path.exists(self.install_dir):
            os.makedirs(self.install_dir)

        self.binary_file = binary_file

        data = {}
        if ascii_file and ascii_file != "None":
            with open(ascii_file, "r") as f_hand:
                content = f_hand.read()
                try:
                    data = json.loads(content)
                except ValueError:
                    data["dependency"] = content
        try:
            self.dependency = data["dependency"].strip()
        except KeyError:
            self.dependency = None

        try:
            self.environment = data["environment"]
        except KeyError:
            self.environment = None

        self.dpkg_lock = "/tmp/dpkg-lock"

    def run(self):
        """
        This method actually untars the debian files and installs them
        on the VM.

        Raises:
            OSError: If the tarfile list contains more than one directory.
        """
        # untar the binary files
        with tarfile.open(self.binary_file) as tar:
            tar.extractall(path=self.install_dir)

        if self.dependency:
            while not os.path.exists(self.dependency):
                time.sleep(1)

        # Verify our extract and get the directory name with actual .debs.
        untared_contents = os.listdir(self.install_dir)
        if len(untared_contents) != 1 or not os.path.isdir(
            os.path.join(self.install_dir, untared_contents[0])
        ):
            raise OSError("Invalid tarfile format: Need exactly 1 directory.")

        # Acquire a file-system lock for running dpkg
        while True:
            try:
                os.mkdir(self.dpkg_lock)
                break
            except OSError:
                time.sleep(1)

        # now that we have the files to install, install them
        binary_dir = os.path.join(self.install_dir, untared_contents[0])

        while True:
            env = dict(os.environ)
            if self.environment:
                env.update(self.environment)
            # pylint: disable=consider-using-with
            dpkg = Popen(
                ["dpkg", "-R", "--force-depends", "-i", binary_dir],
                stdout=PIPE,
                stderr=PIPE,
                env=env,
            )
            output = dpkg.communicate()
            if dpkg.returncode != 0:
                # Output is a tuple (<stdout>, <stderr>)
                print(output[1])
            else:
                break
            time.sleep(1)

        # Release the file-system dpkg lock
        os.rmdir(self.dpkg_lock)

        print("touching")
        # touch a file to indicate that the install is done
        # pylint: disable=consider-using-with
        touch = Popen(["touch", self.touch_location], stdout=PIPE, stderr=PIPE)

        output = touch.communicate()
        if touch.returncode != 0:
            # Output is a tuple (<stdout>, <stderr>)
            print(output[1])


if __name__ == "__main__":
    install = InstallDebs(sys.argv[1], sys.argv[2])
    install.run()
