#!/usr/bin/env python

import os
import sys
import pickle
import tarfile
import tempfile
import subprocess


# pylint: disable=useless-object-inheritance
class InstallLinuxService(object):
    """
    This VMR is responsible for unpacking a tarball containing ``.deb`` files.
    The agent then installs all of those files (similar to ``install_debs.py``.
    It is important to note that if any of the deb files need user interaction,
    this agent will fail. Any services that need user interaction (mysql, postfix,
    etc) should have their own VMR. Additionally, this agent will move a configuration file
    into place and restart the service.

    Note:
        This uses ``sudo service x restart`` (where ``x`` is the service). Therefore, if
        another method of restarting (after configuration changes happen) a different
        VMR should be created.

    """

    def __init__(self, ascii_file=None, binary_file=None):
        """
        Initialize the necessary parameters.

        Arguments:
            ascii_file (str): The path to a file containing any VMR variables.
                The contents of this file should be a pickled dictionary. This
                dictionary contains key/values that are used by the VMR. At a
                minimum it must have:
                - ``conf_dir`` - The directory where the configuration file is placed.
                - ``conf_files`` - a dictionary of files/content that will be replaced.
                - ``service_name`` - the name of the service that needs to be restarted
                    when the configuration changes.
                If any of these variables are missing the VMR will exit, and assume
                that the generated configuration file will be present.
            binary_file (str): The path to a tarball containing all of the debian packages
                that are needed to install one (or many) Linux programs.
        """
        self.tar_file = binary_file
        self.variables_file = ascii_file

    def run(self):
        """
        Run the agent: Extract the binary argument and install the debs it
        contains.
        """
        tar_path = tempfile.mkdtemp()
        self.untar_binary(self.tar_file, tar_path)
        self.install_deb(tar_path)

        # Check to see if there is a variables file
        if not self.variables_file or self.variables_file == "None":
            print("An ascii file was not provided")
            sys.exit()
        else:
            # Make sure that the Pickle is formated correctly
            try:
                with open(self.variables_file, "r") as in_file:
                    variables = pickle.load(in_file)
            except (OSError, pickle.UnpicklingErrorException) as exp:
                print(
                    "An error occurred reading the variables file. "
                    "Continuing without substitutions."
                )
                print(exp)
                variables = {}

        # If they user did not provide the needed information (as described in
        # the agent documentation then use the default config file and exit.
        if "conf_dir" not in variables or not variables["conf_dir"]:
            print("Needs a configuration directory. (conf_dir)")
        elif "conf_files" not in variables or not variables["conf_files"]:
            print(
                "You did not provide any configuration files! (conf_files) Using the default."
            )
        elif "service_name" not in variables or not variables["service_name"]:
            print("Needs the name of the service to restart. (service_name)")
        else:
            conf_dir = os.path.abspath(variables["conf_dir"])
            self.make_confs(
                variables["conf_files"], conf_dir, variables["service_name"]
            )

    def untar_binary(self, tar_file, tar_path):
        """
        Unpack the given tar file.

        Arguments:
            tar_file (str): A tar file, using a compression compatible with Python's
                decompression system (e.g. none, gzip).
            tar_path (str): Path to extract the file's contents to.
        """
        with tarfile.open(tar_file) as tar:
            tar.extractall(path=tar_path)

    def install_deb(self, setup_location):
        """
        Install all debian files in a given directory.

        Arguments:
            setup_location (str): A directory containing debian files to install.
        """
        # Install deb packages
        cmd = ["sudo", "dpkg", "-i", "-R", setup_location]
        self.popen(cmd)

        cmd = ["sudo", "apt-get", "-f", "install"]
        self.popen(cmd)

    def make_confs(self, files, conf_dir, service_name):
        """
        If configuration files are provided by the user the old file is
        moved and the new file is written to disk. Then the services is
        restarted restarted.

        Arguments:
            files (dict): A dictionary keyed on the filename with the value being the
                new configuration.
            conf_dir (str): Where the configuration files are located
            service_name (str): The name of the service that needs to be restarted
        """
        for f in files:
            conf = os.path.join(conf_dir, f)
            old_conf = os.path.join(conf_dir, "%s_old" % f)

            # Move the generated config
            cmd = ["sudo", "mv", conf, old_conf]
            self.popen(cmd)

            # Write the new configuration
            with open(conf, "w") as new_file:
                new_file.write(files[f])

        # Reload the service
        cmd = ["sudo", "service", service_name, "restart"]
        self.popen(cmd)

    def popen(self, cmd):
        """
        A self-defined :py:class:`subprcess.Popen` function that has a few built in
        features and will return the output.

        Arguments:
            cmd (list): The command to run (as a list).

        Returns:
            str: Any output from the process.
        """
        # pylint: disable=consider-using-with
        command = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = command.communicate()
        if command.returncode != 0:
            print(output[1])
            return None
        return output[0]


# pylint: disable=invalid-name
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        ascii_arg = sys.argv[1]
        binary_arg = sys.argv[2]
    else:
        ascii_arg = None
        binary_arg = None

    if not binary_arg or binary_arg == "None":
        print("Must have a binary file")
        sys.exit(1)

    agent = InstallLinuxService(ascii_arg, binary_arg)
    agent.run()
