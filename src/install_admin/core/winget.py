import subprocess
import re
import threading
from typing import List, Optional, Callable
from ..models.package import Package


class WingetClient:
    def __init__(self):
        self.timeout = 120

    def _run(self, args: List[str], elevated: bool = False) -> subprocess.CompletedProcess:
        cmd = ["winget"] + args
        if elevated:
            ps_cmd = f"Start-Process winget -ArgumentList '{' '.join(args)}' -Verb RunAs -Wait -PassThru"
            cmd = ["powershell", "-Command", ps_cmd]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)

    def list_installed(self) -> List[Package]:
        result = self._run(["list"])
        if result.returncode != 0:
            raise RuntimeError(f"winget list failed: {result.stderr}")
        return self._parse_list_output(result.stdout)

    def list_installed_async(self, callback: Callable[[List[Package]], None], error_callback: Callable[[Exception], None] = None):
        def worker():
            try:
                packages = self.list_installed()
                callback(packages)
            except Exception as e:
                if error_callback:
                    error_callback(e)
                else:
                    callback([])
        threading.Thread(target=worker, daemon=True).start()

    def _parse_list_output(self, output: str) -> List[Package]:
        packages = []
        lines = output.strip().split('\n')

        header_idx = -1
        for i, line in enumerate(lines):
            if 'Name' in line and 'Id' in line and 'Version' in line:
                header_idx = i
                break

        if header_idx == -1:
            return packages

        sep_idx = header_idx + 1
        while sep_idx < len(lines) and lines[sep_idx].startswith('-'):
            sep_idx += 1

        for line in lines[sep_idx:]:
            if not line.strip():
                continue

            # Fixed-width columns from header: Name(69), Id(86), Version(21), Available(14), Source(rest)
            name = line[0:69].strip()
            pkg_id = line[69:155].strip()
            version = line[155:176].strip()
            available = line[176:190].strip()
            source = line[190:].strip()

            pkg = Package(
                name=name,
                id=pkg_id,
                version=version,
                source=source,
                is_installed=True
            )
            if available and available != version:
                pkg.available_version = available
            packages.append(pkg)

        return packages

    def search(self, query: str) -> List[Package]:
        result = self._run(["search", query])
        if result.returncode != 0:
            return []
        return self._parse_search_output(result.stdout)

    def search_async(self, query: str, callback: Callable[[List[Package]], None]):
        def worker():
            results = self.search(query)
            callback(results)
        threading.Thread(target=worker, daemon=True).start()

    def _parse_search_output(self, output: str) -> List[Package]:
        packages = []
        lines = output.strip().split('\n')

        header_idx = -1
        for i, line in enumerate(lines):
            if 'Name' in line and 'Id' in line and 'Version' in line:
                header_idx = i
                break

        if header_idx == -1:
            return packages

        sep_idx = header_idx + 1
        while sep_idx < len(lines) and lines[sep_idx].startswith('-'):
            sep_idx += 1

        for line in lines[sep_idx:]:
            line = line.strip()
            if not line:
                continue

            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 3:
                name = parts[0].strip()
                pkg_id = parts[1].strip()
                version = parts[2].strip()
                source = parts[3].strip() if len(parts) > 3 else ''

                packages.append(Package(
                    name=name,
                    id=pkg_id,
                    version=version,
                    source=source,
                    is_installed=False
                ))

        return packages

    def uninstall(self, package_id: str, elevated: bool = True) -> bool:
        result = self._run(["uninstall", "--id", package_id, "--silent", "--accept-source-agreements"], elevated)
        return result.returncode == 0

    def uninstall_async(self, package_id: str, callback: Callable[[bool], None], elevated: bool = True):
        def worker():
            success = self.uninstall(package_id, elevated)
            callback(success)
        threading.Thread(target=worker, daemon=True).start()

    def upgrade(self, package_id: str, elevated: bool = True) -> bool:
        result = self._run(["upgrade", "--id", package_id, "--silent", "--accept-source-agreements"], elevated)
        return result.returncode == 0

    def upgrade_async(self, package_id: str, callback: Callable[[bool], None], elevated: bool = True):
        def worker():
            success = self.upgrade(package_id, elevated)
            callback(success)
        threading.Thread(target=worker, daemon=True).start()

    def get_available_version(self, package_id: str) -> Optional[str]:
        result = self._run(["show", "--id", package_id, "--versions"])
        if result.returncode != 0:
            return None
        return self._parse_show_versions(result.stdout)

    def get_available_version_async(self, package_id: str, callback: Callable[[Optional[str]], None]):
        def worker():
            version = self.get_available_version(package_id)
            callback(version)
        threading.Thread(target=worker, daemon=True).start()

    def _parse_show_versions(self, output: str) -> Optional[str]:
        lines = output.strip().split('\n')
        # Output format:
        # Found Git [Git.Git]
        # Version
        # --------
        # 2.56.1
        # 2.56.0.4
        # ...
        for line in lines:
            line = line.strip()
            if line and not line.startswith('Found') and not line.startswith('Version') and not line.startswith('-'):
                # First non-header line is the latest version
                return line
        return None
