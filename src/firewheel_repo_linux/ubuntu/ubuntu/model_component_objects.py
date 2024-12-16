import os
import warnings
from pathlib import Path

from linux.base_objects import LinuxHost

from firewheel.control.experiment_graph import require_class


@require_class(LinuxHost)
class UbuntuHost:
    """
    This object provides a generic abstraction for all Ubuntu-based VMs.
    Any VM resource or method that could apply broadly to Ubuntu systems
    should be contained within this MC.
    """

    default_user = "ubuntu"
    home_path = Path(f"/home/{default_user}")

    def __init__(self):
        """
        By default, we need to stop/disable the apt daily task, if allowed to run
        it will prevent other packages from being installed.
        """
        # Apt scheduled task interferes with dpkg use. Disable it.
        self.run_executable(-300, "stop_apt_daily.sh", vm_resource=True)

    def add_default_profiles(self):
        """
        Adds default ssh keys, .bashrc, .vimrc, etc.
        Also configures the VM to allow the ubuntu user to use passwordless `sudo`.
        """
        self.run_executable(
            -250,
            "echo",
            f"'{self.default_user} ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers",
            vm_resource=False,
        )
        # drop configs and profiles
        vmr_profile_archive = "combined_profiles.tgz"
        # root profiles
        vm_root_profile_archive = Path("/root") / vmr_profile_archive
        self.drop_file(-249, f"{vm_root_profile_archive}", vmr_profile_archive)
        self.run_executable(
            -248, "chown", f"-R root:root {vm_root_profile_archive}", vm_resource=False
        )
        self.run_executable(
            -247, "tar", f"--no-same-owner -C /root/ -xf {vm_root_profile_archive}"
        )
        self.run_executable(-246, "rm", f"-f {vm_root_profile_archive}")

        # User profiles
        vm_user_profile_archive = self.home_path / vmr_profile_archive
        self.drop_file(-249, f"{vm_user_profile_archive}", vmr_profile_archive)
        self.run_executable(
            -248,
            "chown",
            f"-R {self.default_user}:{self.default_user} {vm_user_profile_archive}",
            vm_resource=False,
        )
        self.run_executable(
            -247,
            "su",
            f'{self.default_user} -c "tar -C {self.home_path} -xf {vm_user_profile_archive}"',
        )
        self.run_executable(-246, "rm", f"-f {vm_user_profile_archive}")

    def add_debug_debs(self):
        """
        Installs debian packages that are useful for debugging purposes,
        including htop and parallel-ssh.
        """
        self.install_debs(-245, "htop-1_0_2_debs.tgz")
        self.install_debs(-244, "pssh_2.3.1-1_all_debs.tgz")

    def install_debs(self, time, debfile):
        """
        Installs a debian package.

        Arguments:
            time (int): Experiment time at which to install the package.
            debfile (str): The file to be installed. This can be either a ``.deb``
                file or a tarball containing multiple ``.deb`` files. No additional
                path information should be provided. However, the ``.deb`` file/tarball
                **must** be provided by a model component used in the experiment
                (i.e. it must be referenced in a MANIFEST file).
        """
        if debfile != os.path.basename(debfile):
            msg = str(
                "When using `install_debs`, path information should not"
                " be provided, only the file name. Found potential path information"
                f" for provided file: {debfile}"
            )
            warnings.warn(msg, stacklevel=2)
            self.log.warning(msg)
        self.add_vm_resource(time, "install_debs.sh", None, debfile)


@require_class(UbuntuHost)
class UbuntuServer:
    """
    This is an abstract decorator which can be used to distinguish if a VM
    is running a Ubuntu Desktop or Server.
    """

    def __init__(self):
        """An unused init method."""


@require_class(UbuntuHost)
class UbuntuDesktop:
    """
    This is an abstract decorator which can be used to distinguish if a VM
    is running a Ubuntu Desktop or Server.
    """

    def __init__(self):
        """An unused init method."""
