from glob import iglob
import pyudev
import subprocess
import time
import logging
import os.path as path
import gi
from gi.repository import Gio
from gi.repository.Gio import DBusProxy, BusType, DBusProxyFlags, DBusCallFlags
from gi.repository.GLib import Variant

# Prerequisites:
# * pip install pyudev
# * apt install mplayer

# UDisks2 Docs: http://storaged.org/doc/udisks2-api/2.10.1/
# pyudev Docs: https://pyudev.readthedocs.io/en/latest/
# Raspberry Pi OS does not allow users to mount using udisks2,
# fix polkit policy: https://github.com/coldfix/udiskie/wiki/Permissions but remove if and always return policy.

UDISKS2_BUS = 'org.freedesktop.UDisks2'
FILE_SYSTEM_IFACE = 'org.freedesktop.UDisks2.Filesystem'

def get_floppy_disk_devices():
    """Returns an array of all floppy disk devices. Note that the devices may or may not have a floppy disk inserted"""
    context = pyudev.Context()
    devices = context.list_devices(subsystem='block', DEVTYPE='disk')
    return [d for d in devices if is_floppy_disk_device(d)]

def is_floppy_disk_device(device):
    """Tests if the given device is a floppy disk device"""
    return 'ID_TYPE' in device.properties and device.properties['ID_TYPE'] == 'floppy'

def has_disk_inserted(device):
    """Tests if the given device has a floppy disk inserted"""
    size = device.attributes.asint('size')
    return size > 0

def get_udisk_block_device_as_file_system(device):
    """Gets the block device associated with the given device as file system"""
    return DBusProxy.new_for_bus_sync(
        BusType.SYSTEM,
        DBusProxyFlags.NONE,
        None,
        UDISKS2_BUS,
        f'/org/freedesktop/UDisks2/block_devices/{device.sys_name}',
        FILE_SYSTEM_IFACE, None)

def mount(device):
    """Mounts a device and returns the mount path"""
    file_system = get_udisk_block_device_as_file_system(device)
    mount_path, = file_system.call_sync('Mount', Variant("(a{sv})", ({},)), DBusCallFlags.NONE, -1, None).unpack()
    return mount_path

def unmount(device):
    """Unmounts a device"""
    file_system = get_udisk_block_device_as_file_system(device)
    return file_system.call_sync('Unmount', Variant("(a{sv})", ({},)), DBusCallFlags.NONE, -1, None)

def get_mount_points(device):
    """Gets a list of mount points for the given device"""
    file_system = get_udisk_block_device_as_file_system(device)
    return decode_mount_points(file_system.get_cached_property('MountPoints'))

def decode_mount_points(mount_points):
    # The `MountPoints` property is an array of null-terminated byte arrays
    return [bytes(m).decode('utf-8').rstrip('\0') for m in mount_points]

def play_audio_files(directory):
    """Plays all audio files in the given directory"""
    for audio_file in iglob('*.mp3', root_dir=directory):
        audio_file_path = path.join(directory, audio_file)
        logging.info(f'Playing {audio_file_path}')
        try:
            subprocess.check_call(['mplayer', '-quiet', '--', audio_file_path])
        except e:
            logging.warn(f'Failed to play audio file {audio_file_path}: {e}')

logging.basicConfig(level=logging.INFO)

played = set()
# TODO: clear played when device itself is removed

while True:
    for device in get_floppy_disk_devices():
        has_disk = has_disk_inserted(device)
        has_played = device.sys_name in played

        if has_disk and not has_played:
            logging.info(f'Playing from {device.sys_name}')
            played.add(device.sys_name)
            mount_points = get_mount_points(device)
            mount_path = mount(device) if len(mount_points) == 0 else mount_points[0]
            play_audio_files(mount_path)
            unmount(device)
            logging.info(f'Finished playing from {device.sys_name}. You can remove the disk.')

        if not has_disk:
            played.discard(device.sys_name)

    time.sleep(5)

# while True:
#     for device in context.list_devices(subsystem='block', DEVTYPE='disk'):
#         if 'ID_TYPE' in device.properties and device.properties['ID_TYPE'] == 'floppy':
#             size = device.attributes.asint('size')
#             has_floppy_disk_inserted = size > 0

#             if has_floppy_disk_inserted:
#                 if device.sys_name in played:
#                     continue
#             else:
#                 played.discard(device.sys_name)
#                 continue

#             print(device.sys_name, device.device_type)
#             print(device.attributes.asint('size'))

#             block_device = bus.get_object('org.freedesktop.UDisks2', f'/org/freedesktop/UDisks2/block_devices/{device.sys_name}')
#             file_system = dbus.Interface(block_device, 'org.freedesktop.UDisks2.Filesystem')
#             properties = dbus.Interface(block_device, dbus.PROPERTIES_IFACE)

#             mount_points = get_mount_points(bus, device)
#             mount_path = file_system.Mount({}) if len(mount_points) == 0 else mount_points[0]
#             print(mount_path)

#             for audio_file in iglob('*.mp3', root_dir=mount_path):
#                 subprocess.check_call(['mplayer', f'{mount_path}/{audio_file}'])

#             played.add(device.sys_name)
#             print(file_system.Unmount({}))

#             # print(bytes(properties.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints')))

#             # mount_path = file_system.Mount({})
#             # print(mount_path)
            
#             # print(file_system.Mount({}))
#             # time.sleep(3)
#             # print(file_system.Unmount({}))

#             # pprint(file_system)

#             # print(proxy.GetBlockDevices())
#             # proxy.unmount()


#             # pprint({**device})
#             # udisksctl mount --block-device /dev/sda

#     time.sleep(5)
