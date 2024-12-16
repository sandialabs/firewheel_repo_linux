#!/usr/bin/env python
import os
import sys
import pickle
from subprocess import PIPE, Popen


# pylint: disable=useless-object-inheritance
class ConfigureNginx(object):
    """
    Add files to customize the configuration of nginx and restart the service
    so the changes take effect.

    This agent is Ubuntu 14.04 specific.

    There are 2 types of file that can modify the configuration for nginx:
        - site
        - conf
    Both of these are used as a set of files in the directories:
        - /etc/nginx/sites-enabled
        - /etc/nginx/conf.d
    Respectively.

    We represent the contents of new files for these locations using a pickled
    ASCII argument file. The file contains a dictionary which outlines
    configuration information and locations::

        {
            'sites': {
                        'example': "<file contents>"
                    },
            'conf': {
                    'more_conf.conf': "<file contents>"
                    }
        }

    This dictionary would result in the creation of 3 files:
        - /etc/nginx/sites-available/example
        - (symlink) /etc/nginx/sites-enabled/example -> /etc/nginx/sites-available/example
        - /etc/nginx/conf.d/more_conf.conf

    This agent removes the default site from sites-enabled, but leaves the file
    in sites-available for reference.

    """

    def __init__(self, ascii_file=None):
        """
        Enable the ``ascii_file`` path to become available to the VMR.

        Arguments:
            ascii_file (str): The string to the file containing configuration options.
        """
        self.ascii_file = ascii_file

    def run(self):
        """
        The primary function which properly configures nginx on Ubuntu 14.04.
        """
        config = None
        with open(self.ascii_file, "r") as f:
            config = pickle.load(f)

        if not config:
            print("Could not load pickled data")
            return

        # Delete the default site
        default_file = "/etc/nginx/sites-enabled/default"
        try:
            os.remove(default_file)
        except OSError as exp:
            print("Warning: Unable to remove default site: %s" % exp)

        # Handle sites
        if config.get("sites"):
            for site in config["sites"].keys():
                sites_available_dir = os.path.join("/etc", "nginx", "sites-available")
                sites_available = os.path.join(sites_available_dir, site)
                sites_enabled_dir = os.path.join("/etc", "nginx", "sites-enabled")
                sites_enabled = os.path.join(sites_enabled_dir, site)

                # Make sure that needed directories exist
                if not os.path.exists(sites_available_dir):
                    try:
                        os.makedirs(sites_available_dir)
                    except OSError:
                        print("Unable to create directory: %s" % sites_available_dir)

                if not os.path.exists(sites_enabled_dir):
                    try:
                        os.makedirs(sites_enabled_dir)
                    except OSError:
                        print("Unable to create directory: %s" % sites_enabled_dir)

                # Put the file in sites-available with the right permission
                with open(sites_available, "w") as f:
                    f.write(config["sites"][site])

                try:
                    os.chmod(sites_available, int("0644", 8))
                except OSError as exp:
                    print("Error: sites_available chmod failed: %s" % exp)

                # Link the file to sites-enabled with the correct permissions.
                try:
                    os.symlink(sites_available, sites_enabled)
                except OSError as exp:
                    print("Error: Unable to create symlink in sites_enabled: %s" % exp)

                try:
                    os.chmod(sites_enabled, int("0644", 8))
                except OSError as exp:
                    print("Error: sites_enabled chmod failed: %s" % exp)

        # Handle conf
        if config.get("conf"):
            for conf in config["conf"].keys():
                conf_path = os.path.join("/etc", "nginx", "conf.d", conf)

                with open(conf_path, "w") as f:
                    f.write(config["conf"][conf])

        # Restart the service
        # pylint: disable=consider-using-with
        restart = Popen(["service", "nginx", "restart"], stdout=PIPE, stderr=PIPE)
        output = restart.communicate()
        if restart.returncode != 0:
            print("Unable to restart nginx service")
            print(output[1])


if __name__ == "__main__":
    # Only takes an ascii file
    configure = ConfigureNginx(sys.argv[1])
    configure.run()
