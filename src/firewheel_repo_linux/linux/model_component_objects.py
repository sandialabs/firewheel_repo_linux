import json
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path

from base_objects import VMEndpoint, AbstractUnixEndpoint

from firewheel.control.experiment_graph import (
    IncorrectConflictHandlerError,
    require_class,
)


class TarCompression(StrEnum):
    """
    Supported compression formats for tar archive extraction.
    """
    AUTO = "auto"
    NONE = "none"
    GZIP = "gzip"
    XZ = "xz"
    BZIP2 = "bzip2"
    ZSTD = "zstd"

    @property
    def cli_options(self) -> tuple[str, ...]:
        """Return the tar command-line options for this compression format."""
        match self:
            case TarCompression.AUTO | TarCompression.NONE:
                return ()
            case TarCompression.GZIP:
                return ("--gzip",)
            case TarCompression.XZ:
                return ("--xz",)
            case TarCompression.BZIP2:
                return ("--bzip2",)
            case TarCompression.ZSTD:
                return ("--zstd",)
        raise RuntimeError(f"Unhandled tar compression: {self!r}")

    @classmethod
    def coerce(cls, value) -> "TarCompression":
        """
        Convert a string or ``TarCompression`` value into a ``TarCompression``.

        Raises:
            ValueError: If the value is not a supported compression format.
        """
        try:
            return cls(value)
        except ValueError:
            supported_compression_methods = [f"'{method.value}'" for method in cls]
            raise ValueError(
                f"Unsupported tar compression '{value}'. "
                f"Supported values are: {', '.join(supported_compression_methods)}."
            ) from None


@require_class(VMEndpoint)
@require_class(AbstractUnixEndpoint)
class LinuxHost:
    """
    A class with functionality common to all Linux Hosts.
    """

    def __init__(self, name=None):
        """
        Sets a few of the basic options for new Linux-based VMs.

        Arguments:
            name (str): The name of the VM.

        Raises:
            RuntimeError: If no name is given to the VM (or provided earlier).
        """
        self.type = "host"
        self.name = getattr(self, "name", name)
        if not self.name:
            raise RuntimeError("LinuxHost needs a name!")

        self.set_hostname()
        self.add_root_profiles()

    def set_hostname(self, start_time=-250):
        """
        Wrapper to run the vm_resource that sets the hostname of the VM

        Args:
            start_time (int, optional): The start time to configure the VM's
                hostname (default=-250)
        """
        self.run_executable(start_time, "set_hostname.sh", self.name, vm_resource=True)

    def change_password(self, start_time, username, password):
        """
        Wrapper to change passwords for Linux VMs.

        Arguments:
            start_time (int): The schedule time to configure the VM's password.
            username (str): The username whose password should change.
            password (str): The new password.
        """
        self.run_executable(
            start_time,
            "chpasswd.sh",
            "{} {}".format(username, password),
            vm_resource=True,
        )

    def cleanup(self, start_time=1):
        """
        Clean up the FIREWHEEL artifacts from the VM (e.g. the ``/var/launch`` folder).

        Arguments:
            start_time (int): The start time to remove the artifacts. Default is 1.
        """
        self.run_executable(start_time, "/bin/rm", "-rf /var/launch")

    def increase_ulimit(self, fd_limit=102400):
        """
        This helps users adjust common `ulimit <https://ss64.com/bash/ulimit.html>`_
        parameters that typically impact experiments.

        Depending on how a process was created, the limit which impacts that process differs
        therefore, it is sometimes difficult to discern how to properly increase limits.
        Users whom are logged in via the PAM module might see a limit set by ``limits.conf``
        whereas system services have a different limit altogether. This method is a best
        effort to increase the limits in various locations. Currently, we only increase
        the number of file descriptors open, but this method can be extended in the future
        for other ``ulimit`` parameters.

        .. seealso::

            - https://wiki.archlinux.org/title/Limits.conf
            - https://www.cyberciti.biz/faq/linux-increase-the-maximum-number-of-open-files/
            - https://pubs.opengroup.org/onlinepubs/009695399/functions/getrlimit.html
            - https://www.scivision.dev/platform-independent-ulimit-number-of-open-files-increase/
            - https://man.archlinux.org/man/systemd-system.conf.5

        Arguments:
            fd_limit (int): The maximum number of open file descriptors. Defaults to 102400.
        """
        start_time = -900

        # Set the default nofile ulimit
        self.run_executable(
            start_time,
            "set_ulimit.sh",
            arguments=f"{fd_limit}",
            vm_resource=True,
        )

    def add_root_profiles(self):
        """
        Adds default ssh keys, .bashrc, .vimrc, etc. for the ``root`` user.
        """
        # root
        self.drop_file(-249, "/root/combined_profiles.tgz", "combined_profiles.tgz")
        self.run_executable(
            -248, "chown", "-R root:root /root/combined_profiles.tgz", vm_resource=False
        )
        self.run_executable(
            -247, "tar", "--no-same-owner -C /root/ -xf /root/combined_profiles.tgz"
        )
        self.run_executable(-246, "rm", "-f /root/combined_profiles.tgz")

    def configure_ips(self, start_time=-200):
        """
        Configure the IP addresses of the VM

        Args:
            start_time (int): The start time to configure the VM's hostname (default=-200)

        Returns:
            bool: True if successful, False otherwise.
        """
        self.interfaces = getattr(self, "interfaces", None)
        if not self.interfaces:
            return False

        try:
            nameservers = self.dns_nameservers
            if isinstance(nameservers, list):
                nameservers = " ".join(nameservers)
        except AttributeError:
            nameservers = ""

        config = ""
        for iface in self.interfaces.interfaces:
            if (
                "mac" in iface
                and "address" in iface
                and iface["address"]
                and "netmask" in iface
                and iface["netmask"]
            ):
                config += "%s %s %s %s %s" % (
                    iface["switch"].name,
                    iface["mac"],
                    str(iface["address"]),
                    str(iface["netmask"]),
                    str(iface["network"].prefixlen),
                )

                # Add default gateway if there is one
                gateway = getattr(self, "default_gateway", None)
                if gateway and not iface["control_network"]:
                    config += f" {gateway}"
                config += "\n"

        if not config:
            return

        config = f"{nameservers}\n{config}"

        self.add_vm_resource(start_time, "configure_ips.sh", config)

        return True

    def unpack_tar(
        self,
        time: int,
        archive: str | Path,
        *,
        compression: TarCompression | str = TarCompression.GZIP,
        directory: str | Path | None = None,
        extra_args: Sequence[str] = (),
        vm_resource: bool = False,
    ):
        """
        Unpack the tar archive.

        This unpacks the tar archive, optionally into a specified
        directory. By default, the archive is treated as gzip-compressed.
        To unpack an xz-compressed archive, pass ``compression="xz"`` or
        ``compression=TarCompression.XZ``.

        Less-common tar extraction options can be supplied with
        ``extra_args``.

        Args:
            time (int): The schedule time (positive or negative) at
                which the tarball will be unpacked.
            archive (str, pathlib.Path): The location of the archive
                file to be unpacked on the VM (or, if ``vm_resource`` is
                :py:data:`True`, the name of the VM resource). Unless
                ``vm_resource`` is :py:data:`True`, it is safest to
                specify the absolute path of the archive on the VM.
            compression (str, TarCompression): The compression format of
                the tar archive. Supported values are ``"auto"``,
                ``"none"``, ``"gzip"``, ``"xz"``, ``"bzip2"``, and
                ``"zstd"``. This may also be provided as a
                :class:`TarCompression` value.
            directory (str or pathlib.Path, optional): A directory where
                the archiving utility will move before unpacking the
                archive. Specifying a directory is recommended when
                running with ``vm_resource`` set to :py:data:`True`.
            extra_args (list[str], optional):
                Additional arguments to pass directly to ``tar``. These
                should usually not include operation flags such as
                ``--extract``, archive-file flags such as ``--file``, or
                compression flags such as ``--gzip``/``--xz``, since this
                method manages those directly. Defaults to an empty
                sequence.
            vm_resource (bool, optional): A flag indicating whether the
                archive is a VM resource and needs to be loaded onto the
                VM before it is unpacked. Defaults to :py:data:`False`.
        """
        # Parse/identify arguments
        compression_method = TarCompression.coerce(compression)
        # Map arguments to the correct CLI invocation
        tar_arguments = ["--extract", *compression_method.cli_options]
        if directory is not None:
            tar_arguments.extend(["--directory", str(directory)])
        tar_arguments.extend(str(arg) for arg in extra_args)
        tar_arguments.extend(["--file", str(archive)])
        # Handle VMR execution (including loading known VMRs onto the VM)
        exec_vm_resource = self.run_executable(time, "tar", arguments=tar_arguments)
        if vm_resource:
            exec_vm_resource.add_file(archive, archive)


def configure_ip_conflict_handler(entry_name, _decorator_value, _current_instance_value):
    """
    The conflict handler for functions overwritten in LinuxNetplanHost that are
    also implemented in LinuxHost, i.e. the ``configure_ips`` function.

    Args:
        entry_name (str): A string describing the attribute that has a conflict
        _decorator_value (any): The value of the attribute from the class that it is trying to be decorated by
        _current_instance_value (any): The current value of the conflicting attribute

    Returns:
        function: A function to be used as the ``configure_ips`` function for Netplan-enabled hosts

    Raises:
        IncorrectConflictHandlerError: If the conflicting function is not ``"configure_ips"``.
    """
    if entry_name == "configure_ips":
        return LinuxNetplanHost.configure_ips
    raise IncorrectConflictHandlerError


@require_class(LinuxHost, conflict_handler=configure_ip_conflict_handler)
class LinuxNetplanHost:
    """
    A class that implements functionality for Linux machines that use `Netplan <https://netplan.io/>`__
    """

    def __init__(self):
        """
        Nothing to do here
        """

    def configure_ips(self, start_time=-200):
        """
        Configure the IP addresses of the VM using netplan

        Args:
            start_time (int): The start time to configure the VM's hostname (default=-200)

        Returns:
            bool: True if successful, False otherwise.
        """
        self.interfaces = getattr(self, "interfaces", None)
        if not self.interfaces:
            return False

        try:
            nameservers = self.dns_nameservers
            if isinstance(nameservers, str):
                nameservers = nameservers.split(" ")
        except AttributeError:
            nameservers = []

        ethernets = {}
        macs = []

        for iface in self.interfaces.interfaces:
            if "mac" in iface and "address" in iface and iface["address"]:
                ip_addr = str(iface["address"])
                prefixlen = str(iface["network"].prefixlen)
                address = f"{ip_addr}/{prefixlen}"
                mac = iface["mac"]
                macs.append(mac)

                ethernets[mac] = {
                    "addresses": [address],
                    "nameservers": {"addresses": nameservers},
                }
                if not iface["control_network"] and hasattr(self, "default_gateway"):
                    ethernets[mac]["gateway4"] = str(self.default_gateway)

        config = {"network": {"ethernets": ethernets, "version": 2}}

        if len(ethernets) == 0:
            return

        # Even though it uses YAML, we use JSON (since all JSON is valid YAML)
        # for ease of editing in other scripts if other settings need to be
        # applied
        self.drop_content(
            start_time - 1, "/etc/netplan/firewheel.yaml", json.dumps(config)
        )
        macs_str = " ".join(macs)
        self.run_executable(
            start_time,
            "set_netplan_interfaces.sh",
            arguments=f'"{macs_str}"',
            vm_resource=True,
        )

        return True
