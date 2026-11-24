import customtkinter as ctk
from typing import List
from .search_bar import SearchBar, ThemeToggle
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

        # Top bar with search and theme toggle
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_bar.grid_columnconfigure(0, weight=1)

        self.search_bar = SearchBar(top_bar, on_search=self._on_search, on_select=self._on_package_selected)
        self.search_bar.grid(row=0, column=0, sticky="ew")

        self.theme_toggle = ThemeToggle(top_bar, on_toggle=self._on_theme_change)
        self.theme_toggle.grid(row=0, column=1, sticky="e")

        # Package list (scrollable)
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Nainstalované aplikace")
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.list_frame.grid_columnconfigure(0, weight=1)

        # Status bar
        self.status_var = ctk.StringVar(value="Připraveno")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", height=30, font=ctk.CTkFont(size=11))
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Bottom bar with refresh button
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.refresh_btn = ctk.CTkButton(bottom_bar, text="🔄 Obnovit seznam", command=self._load_packages, width=150)
        self.refresh_btn.pack(side="right")

    def _load_packages(self):
        self.status_var.set("Načítám nainstalované balíčky...")
        self.refresh_btn.configure(state="disabled")

        def on_loaded(packages: List[Package]):
            self.packages = packages
            self._render_package_list()
            self.status_var.set(f"Nalezeno {len(packages)} balíčků")
            self.refresh_btn.configure(state="normal")

        self.winget.list_installed_async(on_loaded)

    def _render_package_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        sorted_packages = sorted(self.packages, key=lambda p: (not p.has_update, p.name.lower()))

        for pkg in sorted_packages:
            row = PackageRow(self.list_frame, pkg, on_refresh=self._load_packages, on_status=self._set_status)
            row.pack(fill="x", padx=5, pady=5)

    def _on_search(self, query: str):
        self.status_var.set(f"Vyhledávám: {query}...")

    def _on_package_selected(self, pkg: Package):
        self.status_var.set(f"Vybran: {pkg.name} ({pkg.id}) v{pkg.version}")
        # Could add install action here in future

    def _on_theme_change(self):
        self.status_var.set(f"Téma: {ctk.get_appearance_mode()}")

    def _set_status(self, message: str):
        self.status_var.set(message)


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = MainWindow()
    app.mainloop()