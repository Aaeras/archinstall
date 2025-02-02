from pathlib import Path

from archinstall import Installer, disk, models, profile
from archinstall.default_profiles.desktops.sway import SwayProfile

# we're creating a new ext4 filesystem installation
fs_type = disk.FilesystemType('ext4')
device_path = Path('/dev/sda')

# get the physical disk device
device = disk.device_handler.get_device(device_path)

if not device:
	raise ValueError('No device found for given path')

# create a new modification for the specific device
device_modification = disk.DeviceModification(device, wipe=True)

# create a new boot partition
boot_partition = disk.PartitionModification(
	status=disk.ModificationStatus.Create,
	type=disk.PartitionType.Primary,
	start=disk.Size(1, disk.Unit.MiB, device.device_info.sector_size),
	length=disk.Size(512, disk.Unit.MiB, device.device_info.sector_size),
	mountpoint=Path('/boot'),
	fs_type=disk.FilesystemType.Fat32,
	flags=[disk.PartitionFlag.BOOT]
)
device_modification.add_partition(boot_partition)

# create a root partition
root_partition = disk.PartitionModification(
	status=disk.ModificationStatus.Create,
	type=disk.PartitionType.Primary,
	start=disk.Size(513, disk.Unit.MiB, device.device_info.sector_size),
	length=disk.Size(20, disk.Unit.GiB, device.device_info.sector_size),
	mountpoint=None,
	fs_type=fs_type,
	mount_options=[],
)
device_modification.add_partition(root_partition)

start_home = root_partition.length
length_home = device.device_info.total_size - start_home

# create a new home partition
home_partition = disk.PartitionModification(
	status=disk.ModificationStatus.Create,
	type=disk.PartitionType.Primary,
	start=start_home,
	length=length_home,
	mountpoint=Path('/home'),
	fs_type=fs_type,
	mount_options=[]
)
device_modification.add_partition(home_partition)

disk_config = disk.DiskLayoutConfiguration(
	config_type=disk.DiskLayoutType.Default,
	device_modifications=[device_modification]
)


# initiate file handler with the disk config and the optional disk encryption config
fs_handler = disk.FilesystemHandler(disk_config)

# perform all file operations
# WARNING: this will potentially format the filesystem and delete all data
fs_handler.perform_filesystem_operations(show_countdown=False)

mountpoint = Path('/tmp')

with Installer(
	mountpoint,
	disk_config,
	kernels=['linux']
) as installation:
	installation.mount_ordered_layout()
	installation.base_installation(hostname='arch')
	installation.add_additional_packages(['nano', 'wget', 'git', 'timeshift'])

# Optionally, install a profile of choice.
profile_config = profile.ProfileConfiguration(SwayProfile())
profile.profile_handler.install_profile_config(installation, profile_config)
passwd = ""
user = models.User('aaeras', passwd, True)
installation.create_users(user)
