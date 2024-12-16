from linux.ubuntu import UbuntuHost, UbuntuServer, UbuntuDesktop

from firewheel.control.experiment_graph import require_class


@require_class(UbuntuHost)
class Ubuntu1404Host:
    """
    A general class to provide an abstraction between Ubuntu Server and Desktop
    """

    def __init__(self):
        """An unused init method."""


@require_class(Ubuntu1404Host)
@require_class(UbuntuServer)
class Ubuntu1404Server:
    """
    The Model Component for the Ubuntu1404Server image.
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
            self.vm["mem"] = 256
        if "drives" not in self.vm:
            self.vm["drives"] = [
                {
                    "db_path": "ubuntu-14.04.5-server-amd64.qc2.xz",
                    "file": "ubuntu-14.04.5-server-amd64.qc2",
                }
            ]
        if "vga" not in self.vm:
            self.vm["vga"] = "std"

        self.set_image("ubuntu1404server")


@require_class(Ubuntu1404Host)
@require_class(UbuntuDesktop)
class Ubuntu1404Desktop:
    """
    The Model Component for the Ubuntu1404Desktop image.
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
                    "db_path": "ubuntu-14.04.5-desktop-amd64.qcow2.xz",
                    "file": "ubuntu-14.04.5-desktop-amd64.qcow2",
                }
            ]
        if "vga" not in self.vm:
            self.vm["vga"] = "std"

        self.set_image("ubuntu1404desktop")
