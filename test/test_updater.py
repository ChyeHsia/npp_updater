import unittest
from unittest.mock import patch, MagicMock
import src.npp_update as npp_update

class TestNPPUpdater(unittest.TestCase):

    def test_compare_version(self):
        #positive cases
        self.assertEqual(npp_update.compare_version("7.1.2", "8.6"), -1)
        self.assertEqual(npp_update.compare_version("8.9.4", "8.5"), 1)
        self.assertEqual(npp_update.compare_version("8.6.4", "8.6.4"), 0)
        #negative_cases
        self.assertNotEqual(npp_update.compare_version("8.4.4", "8.4.4"), -1)
        self.assertNotEqual(npp_update.compare_version("7.9.4", "3.5"), 0)
        self.assertNotEqual(npp_update.compare_version("3.9.4", "8.5"), 1)

    @patch('npp_update.winreg.OpenKey')
    @patch('npp_update.winreg.QueryValueEx')
    def test_get_arch_x64(self, mock_query, mock_open):
        mock_query.return_value = ("Notepad++ (x64)",)
        arch, path = npp_update.get_arch()
        self.assertEqual(arch, "x64")
        self.assertIn("Uninstall\\Notepad++", path)

    @patch('npp_update.winreg.OpenKey', side_effect=FileNotFoundError)
    def test_get_arch_registry_missing(self, mock_open):
        arch, path = npp_update.get_arch()
        self.assertIsNone(arch)
        self.assertEqual(path, '')

    @patch('npp_update.winreg.OpenKey')
    @patch('npp_update.winreg.QueryValueEx')
    def test_get_current_version(self, mock_query, mock_open):
        mock_query.side_effect = [("Notepad++ (x64)",), ("8.6.2",)]
        version, arch = npp_update.get_current_version()
        self.assertEqual(version, "8.6.2")
        self.assertEqual(arch, "x64")
    
    @patch('npp_update.get_arch', return_value=("x64", "Invalid\\Path"))
    @patch('npp_update.winreg.OpenKey', side_effect=FileNotFoundError)
    def test_get_current_version_missing_registry(self, mock_query, mock_open):
        version, arch = npp_update.get_current_version()
        self.assertIsNone(version)
        self.assertIsNone(arch)

    @patch('npp_update.requests.get')
    def test_get_latest_version(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"tag_name": "v8.6.3"}
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        version = npp_update.get_latest_version()
        self.assertEqual(version, "8.6.3")
    
    @patch('npp_update.requests.get')
    def test_get_latest_version_invalid_json(self,mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = lambda: None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        version = npp_update.get_latest_version()
        self.assertIsNone(version)

    @patch('npp_update.requests.get')
    def test_get_installer(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "assets": [
                {"name": "npp.8.6.3.Installer.x64.exe", "browser_download_url": "http://example.com/npp.exe"}
            ]
        }
        mock_response.raise_for_status = lambda: None
        mock_get.side_effect = [mock_response, MagicMock(raw=b'binarydata', raise_for_status=lambda: None)]
        
        with patch("builtins.open", new_callable=unittest.mock.mock_open()),patch("shutil.copyfileobj"):
            installer = npp_update.get_installer("x64")
            self.assertEqual(installer, "npp_installer_x64.exe")
    
    @patch('npp_update.requests.get')
    def test_get_installer_no_match(self,mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = lambda: None
        mock_response.json.return_value = {
            "assets": [{"name": "unrelated-file.zip"}]
        }
        mock_get.return_value = mock_response

        result = npp_update.get_installer("x64")
        self.assertIsNone(result)

    @patch('npp_update.subprocess.run')
    @patch('npp_update.os.remove')
    def test_run_installer_success(self, mock_remove, mock_run):
        mock_run.return_value = None
        result = npp_update.run_installer("npp_installer.exe")
        self.assertTrue(result)

    @patch('npp_update.subprocess.run', side_effect=OSError("Failure"))
    def test_run_installer_failure(self, mock_run):
        result = npp_update.run_installer("npp_installer_x64.exe")
        self.assertFalse(result)
    
    @patch('src.npp_update.get_current_version', return_value=(None, None))
    def test_main_notepad_missing(self,mock_get):
        self.assertEqual(npp_update.main(), 2)

    @patch('src.npp_update.get_current_version', return_value=("8.6", "x64"))
    @patch('src.npp_update.get_latest_version', return_value=None)
    def test_main_latest_version_fail(self,mock_latest, mock_current):
        self.assertEqual(npp_update.main(), 3)

    @patch('src.npp_update.get_current_version', return_value=("8.6", "x64"))
    @patch('src.npp_update.get_latest_version', return_value="8.6.9")
    @patch('src.npp_update.get_installer', return_value=None)
    def test_main_download_fail(self,mock_installer, mock_latest, mock_current):
        self.assertEqual(npp_update.main(), 4)

    @patch('src.npp_update.get_current_version', return_value=("8.6", "x64"))
    @patch('src.npp_update.get_latest_version', return_value="8.6.3")
    @patch('src.npp_update.get_installer', return_value="npp_installer_64.exe")
    @patch('src.npp_update.run_installer', return_value=False)
    def test_main_install_fail(self,mock_run, mock_installer, mock_latest, mock_current):
        self.assertEqual(npp_update.main(), 5)
    
    @patch('src.npp_update.get_current_version', return_value=("8.6", "x64"))
    @patch('src.npp_update.get_latest_version', return_value="8.6")
    def test_main_no_install(self, mock_latest, mock_current):
        self.assertEqual(npp_update.main(), 0)
    
    @patch('src.npp_update.get_current_version', return_value=("4.5.1", "x64"))
    @patch('src.npp_update.get_latest_version', return_value="8.6.3")
    @patch('src.npp_update.get_installer', return_value="npp_installer_x64.exe")
    @patch('src.npp_update.run_installer', return_value=True)
    def test_main_install_success(self,mock_run, mock_installer, mock_latest, mock_current):
        self.assertEqual(npp_update.main(), 1)

if __name__ == "__main__":
    unittest.main()