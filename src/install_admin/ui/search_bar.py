import customtkinter as ctk
import threading
from typing import List, Callable, Optional
from install_admin.core.winget import WingetClient
from install_admin.models.package import Package


class SearchBar(ctk.CTkFrame):
    def __init__(self, master, on_search: Callable[[str], None], on_select: Callable[[Package], None], get_installed_ids: Callable[[], set] = None, get_source_filter: Callable[[], Optional[str]] = None):
        super().__init__(master, fg_color="transparent")
        self.winget = WingetClient()
        self.on_search = on_search
        self.on_select = on_select
        self.get_installed_ids = get_installed_ids or (lambda: set())
        self.get_source_filter = get_source_filter or (lambda: None)
        self.debounce_timer = None
        self.dropdown_visible = False

        # Search entry
        self.entry = ctk.CTkEntry(self, placeholder_text="Vyhledat balíčky...", width=400, height=36)
        self.entry.pack(side="left", padx=(0, 10), pady=10, fill="x", expand=True)
        self.entry.bind("<KeyRelease>", self._on_keyrelease)
        self.entry.bind("<Down>", self._focus_dropdown)
        self.entry.bind("<Escape>", lambda e: self._hide_dropdown())
        self.entry.bind("<FocusOut>", self._on_focus_out)

        # Dropdown for autocomplete
        self.dropdown = ctk.CTkScrollableFrame(self, width=400, height=200, fg_color=("gray95", "gray15"))

    def _on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Left", "Right", "Escape", "Return", "Tab"):
            return
        if self.debounce_timer:
            self.debounce_timer.cancel()
        query = self.entry.get().strip()
        if len(query) >= 2:
            self.debounce_timer = threading.Timer(0.3, lambda: self._search(query))
            self.debounce_timer.start()
        else:
            self._hide_dropdown()

    def _search(self, query: str):
        self.on_search(query)

        def on_results(packages: List[Package]):
            self.after(0, lambda: self._show_dropdown(packages))

        source_filter = self.get_source_filter()
        self.winget.search_async(query, on_results, source_filter)

    def _show_dropdown(self, packages: List[Package]):
        for widget in self.dropdown.winfo_children():
            widget.destroy()

        if not packages:
            self._hide_dropdown()
            return

        installed_ids = self.get_installed_ids()
        
        # Sort: installed packages first, then by name
        sorted_packages = sorted(packages, key=lambda p: (p.id not in installed_ids, p.name.lower()))

        for pkg in sorted_packages[:10]:
            is_installed = pkg.id in installed_ids
            text = f"{pkg.name} ({pkg.id}) v{pkg.version}"
            if is_installed:
                text += " ✓ nainstalováno"
            
            btn = ctk.CTkButton(
                self.dropdown,
                text=text,
                anchor="w",
                height=32,
                command=lambda p=pkg: self._on_package_click(p),
                fg_color=("gray85", "gray25") if is_installed else None,
                text_color=("green", "lightgreen") if is_installed else None,
            )
            btn.pack(fill="x", padx=5, pady=2)

        if not self.dropdown_visible:
            self.dropdown.pack(side="left", padx=10, pady=(0, 10), fill="y", after=self.entry)
            self.dropdown_visible = True
            self.dropdown.lift()

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

    def _on_focus_out(self, event):
        # Delay hide to allow clicks on dropdown
        self.after(150, self._hide_dropdown)

    def get_query(self) -> str:
        return self.entry.get().strip()


class ThemeToggle(ctk.CTkFrame):
    def __init__(self, master, on_toggle: Callable[[], None]):
        super().__init__(master, fg_color="transparent")
        self.on_toggle = on_toggle
        self.current_mode = ctk.get_appearance_mode()

        self.btn = ctk.CTkButton(
            self,
            text=self._get_icon(),
            width=36,
            height=36,
            command=self._toggle,
            fg_color="transparent",
            hover_color=("gray85", "gray25")
        )
        self.btn.pack(pady=10, padx=10)

    def _get_icon(self) -> str:
        return "☀" if self.current_mode == "Dark" else "🌙"

    def _toggle(self):
        new_mode = "Light" if self.current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        self.current_mode = new_mode
        self.btn.configure(text=self._get_icon())
        self.on_toggle()