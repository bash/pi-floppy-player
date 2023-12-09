#!/usr/bin/env python3

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

# UDisks2 Docs: http://storaged.org/doc/udisks2-api/2.10.1/
# pyudev Docs: https://pyudev.readthedocs.io/en/latest/

UDISKS2_BUS = 'org.freedesktop.UDisks2'
FILE_SYSTEM_IFACE = 'org.freedesktop.UDisks2.Filesystem'

def floppy_player():
    logging.basicConfig(level=logging.INFO)
    monitor_floppy_disk_devices(on_floppy_disk_device_changed)

def monitor_floppy_disk_devices(on_device_change):
    """Calls the provided callback when a floppy disk device is changed."""
    def _on_device_change(device):
        if is_floppy_disk_device(device):
            on_device_change(device)

    monitor = pyudev.Monitor.from_netlink(pyudev.Context())
    monitor.filter_by(subsystem='block', device_type='disk')
    observer = pyudev.MonitorObserver(monitor, callback=_on_device_change)
    observer.daemon = False
    observer.start()

def on_floppy_disk_device_changed(device):
    if is_disk_media_change(device) and has_disk_inserted(device):
        play_audio_files_from_device(device)

def play_audio_files_from_device(device):
    try:
        mount_path = mount(device)
        play_audio_files(mount_path)
        unmount(device)
    except e:
        logging.warn(f'Failed to play from {device.sys_name}: {e}')

def is_floppy_disk_device(device):
    """Tests if the given device is a floppy disk device"""
    return 'ID_TYPE' in device.properties and device.properties['ID_TYPE'] == 'floppy'

def is_disk_media_change(device):
    """Tests if the media of this device was changed"""
    return device.action == 'change' and 'DISK_MEDIA_CHANGE' in device.properties and device.properties['DISK_MEDIA_CHANGE'] == '1'

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

def play_audio_files(directory):
    """Plays all audio files in the given directory"""
    for audio_file in iglob('*.mp3', root_dir=directory):
        audio_file_path = path.join(directory, audio_file)
        logging.info(f'Playing {audio_file_path}')
        try:
            subprocess.check_call(['mplayer', '-quiet', '--', audio_file_path])
        except e:
            logging.warn(f'Failed to play audio file {audio_file_path}: {e}')

if __name__ == '__main__':
    floppy_player()
