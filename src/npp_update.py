"""
Notepad++ Updater
------------------

This script checks the currently installed version of Notepad++ on a Windows system,
compares it with the latest release available on GitHub, and automatically updates Notepad++
if a newer version is available.

Features:
- Reads the installed Notepad++ version from the Windows Registry.
- Fetches the latest release version from the Notepad++ GitHub repository.
- Downloads the latest installer silently if an update is available.
- Installs the update in the background.

Requirements:
- Python 3.x
- requests
- packaging

Usage:
1. Make sure Python is installed on your system.
2. Install the required dependencies with: pip install -r requirements.txt
3. Run the script as Administrator (required for registry access and installing software):
   python npp_updater.py

Note:
- This script is intended for Windows systems only.
- Admin privileges are required to install Notepad++ and access HKLM registry keys.
- Designed for use with the official Notepad++ installer from GitHub.

Author: ChyeHsia Chiam
Date: April 2025
"""

import winreg
import shutil
import subprocess
import os
import sys
from typing import Tuple, Optional

import requests
from packaging.version import parse


GITHUB_RELEASES_URL = \
    "https://api.github.com/repos/notepad-plus-plus/notepad-plus-plus/releases/latest"

def compare_version(current_version: str, latest_version:str ) -> int:
    '''
        Compares two strings and returns integer indicating version relationship.

        Args:
            current_version (str) : Current version installed in system
            latest_version (str) : Latest available version
        
        Return:
            int: -1 if current < latest, 1 if current > latest, 0 if equal.
    '''
    v1 = parse(current_version)
    v2 = parse(latest_version)

    if v1 < v2:
        return -1
    if v1 > v2:
        return 1
    return 0

def get_arch() -> Tuple[Optional[str], str]:
    '''
    Retrieves system architecture type for Notepad++ installation from Windows Registry

    Returns:
        tuple[str | None, str]: Architecture ('x86', 'x64', or None) and registry path
    '''
    #Two possible registry path for Notepad++ in a 64-bit system.
    npp_reg_paths = [r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Notepad++",
                     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Notepad++"]

    for path in npp_reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                display_name = winreg.QueryValueEx(key, "DisplayName")[0]
                arch = "x64" if "x64" in display_name else "x86"

                return arch, path
        except WindowsError:
            continue

    return None, ""

def get_current_version() -> Tuple[Optional[str], Optional[str]]:
    '''
    Retrieves installed version of Notepad++

    Returns:
        tuple[str | None, str | None]: Installed version and architecture, or None if not found.

    '''
    arch, reg_path = get_arch()
    if not arch:
        return None, None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            version = winreg.QueryValueEx(key, "DisplayVersion")[0]
            return version,arch
    except (FileNotFoundError, OSError) as e:
        print(f"Error accessing registry key: {e}")
        return None, None

def get_latest_version() -> Optional[str]:
    '''
        Fetches the latest Notepad++ version from Github

        Returns:
            str | None : Latest version string or None if fails to fetchs
    '''
    try:
        res = requests.get(GITHUB_RELEASES_URL, timeout = 10)
        res.raise_for_status()
        version = res.json()['tag_name'].lstrip('v') # Remove leading 'v' of version
        return str(version)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest version from Github: {e}")
    except ValueError as e:
        print(f"Error parsing JSON response {e}")
    return None

def get_installer(arch: str) -> Optional[str]:
    '''
        Download relevant Notepad++ installer from Github as npp_installer.exe

        Args:
            arch (str): Architecture type of system ('x64' or 'x86)
        
        Returns:
            str | None: Path for installer to be downloaded or None on failure
    '''
    try:
        res = requests.get(GITHUB_RELEASES_URL, timeout = 10)
        res.raise_for_status()
        assets = res.json()['assets']
        download_url = None

        # Determine correct installer based on architecture
        for asset in assets:

            if (asset['name'].endswith(arch + ".exe") and arch == "x64") \
                or (asset['name'].endswith("Installer.exe") and arch == "x86"):
                download_url = asset['browser_download_url']
                break

        if not download_url:
            print("No suitable installer found")
            return None

        filepath = f'npp_installer_{arch}.exe'

        # Stream the download
        with requests.get(download_url, stream = True, timeout = 10) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as file:
                shutil.copyfileobj(r.raw, file)
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Network error while downloading installer: {e}")
        return None
    except IOError as e:
        print(f"File I/O error while saving installer: {e}")
        return None

def run_installer(path: str) -> bool:
    '''
        Run the installation in the background and deletes installer when done

        Args:
            path (str): Path to installer file

        Returns:
            bool: False if installation failed, True if installation succeeds
        
        
    '''
    print("Running installer...")
    try:
        subprocess.run([path, "/S"], check = True)
        print("Update complete")
        if os.path.exists(path):
            os.remove(path)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Installer failed: {e}")
        if os.path.exists(path):
            os.remove(path)
        return False
    except OSError as e:
        print(f"Windows error: {e}")
        if os.path.exists(path):
            os.remove(path)
        return False

def main() -> int:
    '''
        Main function for the update process of Notepad++
        This function is intended to be run as the entry point of the script

        Returns:
            int: Exit code indicating outcome.
            0 - Success (no update needed)
            1 - Update installed successfully
            2 - Notepad++ not found on the system
            3 - Failed to retrieve latest version
            4 - Installer download failed
            5 - Installation failed

    '''

    current_version, arch = get_current_version()
    if not current_version or not arch:
        print("Notepad++ not installed on system")
        return 2

    latest_version = get_latest_version()
    if not latest_version:
        print("Unable to retrieve latest verision")
        return 3

    result = compare_version(current_version, latest_version)
    if result < 0:
        print(f"Update available: {current_version} -> {latest_version}")
        installer = get_installer(arch)

        if not installer:
            print("Installer download failed")
            return 4
        succeed = run_installer(installer)
        return 1 if succeed else 5

    print("Notepad++ is already up to date.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
