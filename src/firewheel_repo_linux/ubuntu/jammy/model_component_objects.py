"""This module contains all necessary Model Component Objects for linux.ubuntu2204."""

from linux.ubuntu import UbuntuHost, UbuntuServer, UbuntuDesktop
from linux.base_objects import LinuxNetplanHost

from firewheel.control.experiment_graph import (
    IncorrectConflictHandlerError,
    require_class,
)


def ubuntu_2204_conflict_handler(entry_name, _decorator_value, _current_instance_value):
    """
    The conflict handler for functions overwritten in
    :py:class`linux.ubuntu2204.Ubuntu2204Host` Ubuntu2204Host that are also implemented elsewhere

    Args:
        entry_name (str): A string describing the attribute that has a conflict
        _decorator_value (any): The value of the attribute from the class that it is trying to be decorated by
        _current_instance_value (any): The current value of the conflicting attribute

    Returns:
        function: The :py:class`linux.ubuntu2204.Ubuntu2204Host` version of the function if there are conflicts


    Raises:
        IncorrectConflictHandlerError: If the conflicting function is not ``"add_debug_debs”``.
    """
    if entry_name == "add_debug_debs":
        return Ubuntu2204Host.add_debug_debs
    raise IncorrectConflictHandlerError


@require_class(UbuntuHost, conflict_handler=ubuntu_2204_conflict_handler)
@require_class(LinuxNetplanHost)
class Ubuntu2204Host:
    """
    A general class to provide an abstraction between Ubuntu Server and Desktop
    """

    def __init__(self):
        """This abstraction is not needed"""

    def add_debug_debs(self):
        """
        Installs debian packages that are useful for debugging purposes,
        including parallel-ssh.
        """
        self.install_debs(-244, "pssh_2.3.4-2_all_debs.tgz")


@require_class(Ubuntu2204Host)
@require_class(UbuntuServer)
class Ubuntu2204Server:
    """
    The Model Component for the Ubuntu2204Server image.
    """

    def __init__(self):
        """
        Setting all of the required parameters for a new image
        """
        self.vm = getattr(self, "vm", {})

        if "architecture" not in self.vm:
            self.vm["architecture"] = "x86_64"
        if "vcpu" not in self.vm:
            self.vm["vcpu"] = {
                "model": "qemu64",
                "sockets": 1,
                "cores": 1,
                "threads": 1,
            }
        if "mem" not in self.vm:
            self.vm["mem"] = 1024
        if "drives" not in self.vm:
            self.vm["drives"] = [
                {
                    "db_path": "ubuntu-22.04-server-amd64.qcow2.tgz",
                    "file": "ubuntu-22.04-server-amd64.qcow2",
                }
            ]
        if "vga" not in self.vm:
            self.vm["vga"] = "std"

        self.set_image("ubuntu2204server")


@require_class(Ubuntu2204Host)
@require_class(UbuntuDesktop)
class Ubuntu2204Desktop:
    """
    The Model Component for the Ubuntu2204Desktop image.
    """

    def __init__(self):
        """
        Setting all of the required parameters for a new image
        """
        self.vm = getattr(self, "vm", {})

        if "architecture" not in self.vm:
            self.vm["architecture"] = "x86_64"
        if "vcpu" not in self.vm:
            self.vm["vcpu"] = {
                "model": "qemu64",
                "sockets": 1,
                "cores": 2,
                "threads": 1,
            }
        if "mem" not in self.vm:
            self.vm["mem"] = 2048
        if "drives" not in self.vm:
            self.vm["drives"] = [
                {
                    "db_path": "ubuntu-22.04-desktop-amd64.qcow2.tgz",
                    "file": "ubuntu-22.04-desktop-amd64.qcow2",
                }
            ]
        if "vga" not in self.vm:
            self.vm["vga"] = "std"

        self.set_image("ubuntu2204desktop")
