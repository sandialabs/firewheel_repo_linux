from linux.ubuntu import UbuntuHost, UbuntuServer, UbuntuDesktop
from linux.base_objects import LinuxNetplanHost

from firewheel.control.experiment_graph import require_class


@require_class(LinuxNetplanHost)
@require_class(UbuntuHost)
class Ubuntu1804Host:
    """
    A general class to provide an abstraction between Ubuntu Server and Desktop
    """

    def __init__(self):
        """This abstraction is not needed"""


@require_class(Ubuntu1804Host)
@require_class(UbuntuServer)
class Ubuntu1804Server:
    """
    The Model Component for the Ubuntu1804Server image.
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
            self.vm["mem"] = 512
        if "drives" not in self.vm:
            self.vm["drives"] = [
                {
                    "db_path": "ubuntu-18.04.5-server-amd64.qcow2.tgz",
                    "file": "ubuntu-18.04.5-server-amd64.qcow2",
                }
            ]
        if "vga" not in self.vm:
            self.vm["vga"] = "std"

        self.set_image("ubuntu1804server")


@require_class(Ubuntu1804Host)
@require_class(UbuntuDesktop)
class Ubuntu1804Desktop:
    """
    The Model Component for the Ubuntu1804Desktop image.
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
                    "db_path": "ubuntu-18.04.5-desktop-amd64.qcow2.tgz",
                    "file": "ubuntu-18.04.5-desktop-amd64.qcow2",
                }
            ]
        if "vga" not in self.vm:
            self.vm["vga"] = "std"

        self.set_image("ubuntu1804Desktop")
