# InstallAdmin CustomTkinter Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create a Python desktop application using CustomTkinter that lists installed winget packages, allows uninstall/update per package, and provides search with autocomplete for discovering new packages.

**Architecture:** Single-window CustomTkinter app with three main areas: top search bar with autocomplete (winget search), middle package list with per-row actions (uninstall/update), bottom status/log area. Uses subprocess for winget CLI calls, async/threading for non-blocking operations.

**Tech Stack:** Python 3.10+, CustomTkinter, winget CLI, threading/asyncio for background operations.

---

### Task 1: Project Setup & Dependencies

**Objective:** Initialize Python project with CustomTkinter and create basic project structure.

**Files:**
- Create: `requirements.txt`
- Create: `src/install_admin/__init__.py`
- Create: `src/install_admin/main.py`
- Create: `src/install_admin/ui/main_window.py`
- Create: `src/install_admin/core/winget.py`
- Create: `src/install_admin/models/package.py`

**Step 1: Write requirements.txt**
```text
customtkinter>=5.2.0
pillow>=10.0.0
```

**Step 2: Create project structure**
```bash
mkdir -p src/install_admin/ui src/install_admin/core src/install_admin/models
```

**Step 3: Verify**
```bash
pip install -r requirements.txt
python -c "import customtkinter; print('OK')"
```

---

### Task 2: Package Data Model

**Objective:** Define Package dataclass for installed and available packages.

**Files:**
- Create: `src/install_admin/models/package.py`

**Implementation:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Package:
    name: str
    id: str
    version: str
    source: str
    is_installed: bool = True
    available_version: Optional[str] = None
    description: Optional[str] = None
    
    @property
    def has_update(self) -> bool:
        return self.available_version is not None and self.available_version != self.version
    
    def __str__(self) -> str:
        return f"{self.name} ({self.id}) v{self.version}"
```

---

### Task 3: Winget Core Module

**Objective:** Implement winget CLI wrapper for list, search, uninstall, upgrade commands.

**Files:**
- Create: `src/install_admin/core/winget.py`

**Implementation:**
```python
import subprocess
import json
import re
from typing import List, Optional
from ..models.package import Package

class WingetClient:
    def __init__(self):
        self.timeout = 60
    
    def _run(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = ["winget"] + args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
    
    def list_installed(self) -> List[Package]:
        result = self._run(["list", "--json"])
        if result.returncode != 0:
            raise RuntimeError(f"winget list failed: {result.stderr}")
        data = json.loads(result.stdout)
        packages = []
        for item in data:
            packages.append(Package(
                name=item.get("Name", ""),
                id=item.get("Id", ""),
                version=item.get("Version", ""),
                source=item.get("Source", ""),
                is_installed=True
            ))
        return packages
    
    def search(self, query: str) -> List[Package]:
        result = self._run(["search", query, "--json"])
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        packages = []
        for item in data:
            packages.append(Package(
                name=item.get("Name", ""),
                id=item.get("Id", ""),
                version=item.get("Version", ""),
                source=item.get("Source", ""),
                is_installed=False,
                description=item.get("Description", "")
            ))
        return packages
    
    def uninstall(self, package_id: str) -> bool:
        result = self._run(["uninstall", "--id", package_id, "--silent", "--accept-source-agreements"])
        return result.returncode == 0
    
    def upgrade(self, package_id: str) -> bool:
        result = self._run(["upgrade", "--id", package_id, "--silent", "--accept-source-agreements"])
        return result.returncode == 0
    
    def get_available_version(self, package_id: str) -> Optional[str]:
        result = self._run(["show", "--id", package_id, "--json"])
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        versions = data.get("Versions", [])
        if versions:
            return versions[0].get("Version")
        return None
```

---

### Task 4: Main Window UI - Search Bar

**Objective:** Create top search bar with autocomplete using CustomTkinter.

**Files:**
- Modify: `src/install_admin/ui/main_window.py`

**Implementation:**
```python
import customtkinter as ctk
import threading
from typing import List, Callable
from ...core.winget import WingetClient
from ...models.package import Package

class SearchBar(ctk.CTkFrame):
    def __init__(self, master, on_search: Callable[[str], None], on_select: Callable[[Package], None]):
        super().__init__(master)
        self.winget = WingetClient()
        self.on_search = on_search
        self.on_select = on_select
        self.debounce_timer = None
        
        self.entry = ctk.CTkEntry(self, placeholder_text="Vyhledat balíčky...", width=400)
        self.entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        self.entry.bind("<KeyRelease>", self._on_keyrelease)
        self.entry.bind("<Down>", self._focus_dropdown)
        
        self.dropdown = ctk.CTkScrollableFrame(self, width=400, height=200)
        self.dropdown_visible = False
        
    def _on_keyrelease(self, event):
        if self.debounce_timer:
            self.debounce_timer.cancel()
        query = self.entry.get().strip()
        if len(query) >= 2:
            self.debounce_timer = threading.Timer(0.3, lambda: self._search(query))
            self.debounce_timer.start()
        else:
            self._hide_dropdown()
    
    def _search(self, query: str):
        def worker():
            results = self.winget.search(query)
            self.after(0, lambda: self._show_dropdown(results))
        threading.Thread(target=worker, daemon=True).start()
    
    def _show_dropdown(self, packages: List[Package]):
        for widget in self.dropdown.winfo_children():
            widget.destroy()
        for pkg in packages[:10]:
            btn = ctk.CTkButton(
                self.dropdown,
                text=f"{pkg.name} ({pkg.id}) v{pkg.version}",
                anchor="w",
                command=lambda p=pkg: self._on_package_click(p)
            )
            btn.pack(fill="x", padx=5, pady=2)
        if not self.dropdown_visible:
            self.dropdown.pack(side="left", padx=10, pady=(0, 10), fill="y")
            self.dropdown_visible = True
    
    def _hide_dropdown(self):
        if self.dropdown_visible:
            self.dropdown.pack_forget()
            self.dropdown_visible = False
    
    def _focus_dropdown(self, event):
        if self.dropdown_visible:
            children = self.dropdown.winfo_children()
            if children:
                children[0].focus_set()
    
    def _on_package_click(self, pkg: Package):
        self._hide_dropdown()
        self.entry.delete(0, "end")
        self.on_select(pkg)
```

---

### Task 5: Package List Row Component

**Objective:** Create a row widget for each installed package with uninstall/update buttons.

**Files:**
- Create: `src/install_admin/ui/package_row.py`

**Implementation:**
```python
import customtkinter as ctk
import threading
from typing import Callable
from ...models.package import Package
from ...core.winget import WingetClient

class PackageRow(ctk.CTkFrame):
    def __init__(self, master, package: Package, on_refresh: Callable[[], None]):
        super().__init__(master)
        self.package = package
        self.on_refresh = on_refresh
        self.winget = WingetClient()
        self.checking_update = False
        
        self.grid_columnconfigure(1, weight=1)
        
        # Name & ID
        name_label = ctk.CTkLabel(self, text=package.name, font=ctk.CTkFont(weight="bold"), anchor="w")
        name_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        id_label = ctk.CTkLabel(self, text=package.id, text_color="gray", anchor="w")
        id_label.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")
        
        # Version info
        version_frame = ctk.CTkFrame(self, fg_color="transparent")
        version_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=5, sticky="e")
        
        self.version_label = ctk.CTkLabel(version_frame, text=f"v{package.version}", anchor="e")
        self.version_label.pack(side="left", padx=5)
        
        self.update_indicator = ctk.CTkLabel(version_frame, text="", text_color="orange")
        self.update_indicator.pack(side="left", padx=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=5, sticky="e")
        
        self.uninstall_btn = ctk.CTkButton(
            btn_frame, text="Odinstalovat", width=100,
            fg_color="#D32F2F", hover_color="#B71C1C",
            command=self._uninstall
        )
        self.uninstall_btn.pack(side="left", padx=5)
        
        self.update_btn = ctk.CTkButton(
            btn_frame, text="Aktualizovat", width=100,
            state="disabled",
            command=self._upgrade
        )
        self.update_btn.pack(side="left", padx=5)
        
        self.check_update_btn = ctk.CTkButton(
            btn_frame, text="Zkontrolovat", width=100,
            command=self._check_update
        )
        self.check_update_btn.pack(side="left", padx=5)
        
        self.progress = ctk.CTkProgressBar(btn_frame, width=100, mode="indeterminate")
        
    def _check_update(self):
        if self.checking_update:
            return
        self.checking_update = True
        self.check_update_btn.configure(state="disabled", text="Kontroluji...")
        
        def worker():
            version = self.winget.get_available_version(self.package.id)
            self.after(0, lambda: self._on_version_check(version))
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_version_check(self, version: str):
        self.checking_update = False
        self.check_update_btn.configure(state="normal", text="Zkontrolovat")
        if version and version != self.package.version:
            self.package.available_version = version
            self.update_indicator.configure(text=f"→ {version}")
            self.update_btn.configure(state="normal")
        else:
            self.update_indicator.configure(text="Aktuální", text_color="green")
    
    def _uninstall(self):
        self._set_busy(True, "Odinstaluji...")
        def worker():
            success = self.winget.uninstall(self.package.id)
            self.after(0, lambda: self._on_action_done(success, "odinstalován"))
        threading.Thread(target=worker, daemon=True).start()
    
    def _upgrade(self):
        self._set_busy(True, "Aktualizuji...")
        def worker():
            success = self.winget.upgrade(self.package.id)
            self.after(0, lambda: self._on_action_done(success, "aktualizován"))
        threading.Thread(target=worker, daemon=True).start()
    
    def _set_busy(self, busy: bool, text: str = ""):
        self.uninstall_btn.configure(state="disabled" if busy else "normal")
        self.update_btn.configure(state="disabled" if busy else ("normal" if self.package.has_update else "disabled"))
        self.check_update_btn.configure(state="disabled" if busy else "normal")
        if busy:
            self.progress.pack(side="left", padx=5)
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.pack_forget()
    
    def _on_action_done(self, success: bool, action: str):
        self._set_busy(False)
        if success:
            self.on_refresh()
        else:
            # Show error in status bar via callback
            pass
```

---

### Task 6: Main Window Assembly

**Objective:** Assemble main window with search bar, package list, and status bar.

**Files:**
- Modify: `src/install_admin/ui/main_window.py`

**Implementation:**
```python
import customtkinter as ctk
import threading
from typing import List
from .package_row import PackageRow
from ..core.winget import WingetClient
from ..models.package import Package

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("InstallAdmin")
        self.geometry("1000x700")
        self.minsize(800, 500)
        
        self.winget = WingetClient()
        self.packages: List[Package] = []
        
        self._setup_ui()
        self._load_packages()
    
    def _setup_ui(self):
        # Grid config
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Search bar
        self.search_bar = SearchBar(self, on_search=self._on_search, on_select=self._on_package_selected)
        self.search_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Package list (scrollable)
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Nainstalované aplikace")
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        # Status bar
        self.status_var = ctk.StringVar(value="Připraveno")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", height=30)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(self, text="🔄 Obnovit seznam", command=self._load_packages)
        self.refresh_btn.grid(row=3, column=0, pady=(0, 10))
    
    def _load_packages(self):
        self.status_var.set("Načítám nainstalované balíčky...")
        self.refresh_btn.configure(state="disabled")
        
        def worker():
            try:
                packages = self.winget.list_installed()
                self.after(0, lambda: self._on_packages_loaded(packages))
            except Exception as e:
                self.after(0, lambda: self._on_load_error(str(e)))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _on_packages_loaded(self, packages: List[Package]):
        self.packages = packages
        self._render_package_list()
        self.status_var.set(f"Nalezeno {len(packages)} balíčků")
        self.refresh_btn.configure(state="normal")
    
    def _on_load_error(self, error: str):
        self.status_var.set(f"Chyba: {error}")
        self.refresh_btn.configure(state="normal")
    
    def _render_package_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        for pkg in self.packages:
            row = PackageRow(self.list_frame, pkg, on_refresh=self._load_packages)
            row.pack(fill="x", padx=5, pady=5)
    
    def _on_search(self, query: str):
        self.status_var.set(f"Vyhledávám: {query}...")
    
    def _on_package_selected(self, pkg: Package):
        self.status_var.set(f"Vybran: {pkg.name} ({pkg.id})")
        # Could open detail dialog or auto-install

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = MainWindow()
    app.mainloop()
```

---

### Task 7: Entry Point

**Objective:** Create main entry point.

**Files:**
- Modify: `src/install_admin/main.py`

**Implementation:**
```python
from .ui.main_window import MainWindow

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
```

---

### Task 8: Packaging & Verification

**Objective:** Create pyproject.toml, test run, verify all features work.

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`

**pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "install-admin"
version = "1.0.0"
description = "GUI pro správu winget balíčků"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "customtkinter>=5.2.0",
    "pillow>=10.0.0",
]

[project.scripts]
install-admin = "install_admin.main:main"

[tool.setuptools.packages.find]
where = ["src"]
```

**Verification Steps:**
```bash
pip install -e .
install-admin
```
Expected: Window opens, lists installed packages, search works with autocomplete, uninstall/update buttons function.

---

### Risks & Open Questions

1. **winget JSON output format** - May vary by version; need to handle gracefully
2. **Admin rights** - winget uninstall/upgrade may require elevation; may need runas
3. **Performance** - Loading many packages could block UI; threading mitigates
4. **Autocomplete source** - winget search is slow; debouncing helps but may need caching
5. **Windows-only** - winget is Windows-specific; document clearly