# Notepad++ Auto Updater

## Project Overview

This Python script automatically checks for updates to Notepad++ on Windows systems. If a newer version is available, it downloads the correct installer for your system architecture (`x86` or `x64`) and runs the update silently in the background.

---

## Installation Instructions

### Prerequisites

- **Operating System**: Windows 10/11
- **Python**: Version 3.8+
- **Permissions**: Administrator privileges (required to access the Windows Registry and install software)

### Setup Steps

1. Clone or download this repository:

```bash
git clone https://github.com/ChyeHsia/npp_updater.git
cd npp_updater
```
2. Install required packagers

```bash
pip install -r requrements.txt
```
---
## Usage Instructions

To run the updater script

**Terminal must be run as admin**
```bash
python src\npp_update.py
```
---
## Design Decisions

The general direction of this script is to minimize the need of user interaction as well as accomodating to the flexibility of existing versions in mind.

- Windows Registry Access: The script identifies Notepad++ installation and version info directly from the Registry, avoiding reliance on file paths or shortcuts in the event of installation in custom locations.

- Architecture Detection: Handles both x86 and x64 installations by scanning both standard and WOW6432Node registry paths.

- GitHub API: Uses Github Releases API to query the latest release based on version tag and assest list.

- Silent Installation: The update process is non-intrusive, designed to run without user interaction using the /S flag.

- Modular Design: Each logical unit (version checking, installer fetching, installation) is encapsulated in its own function for readability and maintainability. 

---

## Testing Approach

Due to the encapsulated nature each step in the script (get versions, download installer, run installation), testing was primarily focused on the output each functions provided.

To run the test:

```bash
python -m pytest test/test_update.py
```

#### Test cases summarised as below:

| **Test Method**                             | **Description**                                                                 |
|--------------------------------------------|---------------------------------------------------------------------------------|
| `test_compare_version`                     | Validates correct version comparison results (older, newer, equal).            |
| `test_get_arch_x64`                        | Mocks registry to simulate 64-bit Notepad++ detection.                         |
| `test_get_arch_registry_missing`           | Tests behavior when registry keys are not found.                               |
| `test_get_current_version`                 | Retrieves mocked version and architecture from registry.                       |
| `test_get_current_version_missing_registry`| Handles failure in reading registry path gracefully.                           |
| `test_get_latest_version`                  | Mocks successful GitHub API call to retrieve latest version.                   |
| `test_get_latest_version_invalid_json`     | Tests error handling on invalid JSON response from GitHub.                     |
| `test_get_installer`                       | Downloads mocked installer and confirms correct file naming.                   |
| `test_get_installer_no_match`              | Handles case when no matching installer is found in GitHub release assets.     |
| `test_run_installer_success`               | Verifies successful execution and cleanup of installer.                        |
| `test_run_installer_failure`               | Simulates a failed installer run and checks error handling.                    |
| `test_main_notepad_missing`                | Verifies flow when Notepad++ is not detected on the system.                   |
| `test_main_latest_version_fail`            | Tests failure when latest version cannot be fetched.                           |
| `test_main_download_fail`                  | Simulates a scenario where the installer download fails.                       |
| `test_main_install_fail`       | Installer runs but fails (returns `False`).                                    |
| `test_main_no_install`   | Notepad++ is already up to date — no update performed.                         |
| `test_main_install_success`       | Full flow success: older version detected, update installed.                   |


---
## Challenges Faced
Throughout the project, the general challenge is to familiarise with the concept of writing in a high-level development perspective. The differences can be seen in the following aspect:

1. Working with Remote APIs and JSON
Unlike local hardware interactions, where it is connected via cable or wireless, as long as the port or connection is stable and established, the rest of the interaction is just streams of data coming in from the I/O.
But the concept of GitHub's REST API and JSON responses are relatively new and it seems more abstract to obtain the required information.

2. Testing Without Affecting the System
Since the script interacts with real system files, processes, and even installs software, running tests directly would be risky. Hence, to test it, I had to mock all dangerous operations: registry access, subprocess execution, HTTP calls, file writes, etc. 
This abstraction layer felt unnatural at first compared to the direct cause-effect flow of low-level programming, where you know exactly what your code touches and direct testing on actual hardware connections is often required.

