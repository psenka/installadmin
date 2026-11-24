import customtkinter as ctk
from typing import Callable, Optional
from install_admin.models.package import Package
from install_admin.core.winget import WingetClient


class PackageRow(ctk.CTkFrame):
    def __init__(self, master, package: Package, on_refresh: Callable[[], None], on_status: Callable[[str], None]):
        super().__init__(master, fg_color=("gray90", "gray20"))
        self.package = package
        self.on_refresh = on_refresh
        self.on_status = on_status
        self.winget = WingetClient()
        self.checking_update = False
        self.action_in_progress = False

        self.grid_columnconfigure(1, weight=1)

        # Name & ID
        name_label = ctk.CTkLabel(self, text=package.name, font=ctk.CTkFont(weight="bold"), anchor="w")
        name_label.grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")

        id_label = ctk.CTkLabel(self, text=package.id, text_color="gray", anchor="w", font=ctk.CTkFont(size=11))
        id_label.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")

        # Version info
        version_frame = ctk.CTkFrame(self, fg_color="transparent")
        version_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=8, sticky="e")

        self.version_label = ctk.CTkLabel(version_frame, text=f"v{package.version}", anchor="e")
        self.version_label.pack(side="left", padx=5)

        self.update_indicator = ctk.CTkLabel(version_frame, text="", text_color="orange", font=ctk.CTkFont(size=11))
        self.update_indicator.pack(side="left", padx=5)

        # Buttons frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=8, sticky="e")

        self.uninstall_btn = ctk.CTkButton(
            self.btn_frame, text="Odinstalovat", width=100,
            fg_color="#D32F2F", hover_color="#B71C1C",
            command=self._uninstall
        )
        self.uninstall_btn.pack(side="left", padx=5)

        self.update_btn = ctk.CTkButton(
            self.btn_frame, text="Aktualizovat", width=100,
            command=self._upgrade
        )
        if not package.has_update:
            self.update_btn.pack_forget()
        else:
            self.update_btn.pack(side="left", padx=5)

        self.check_update_btn = ctk.CTkButton(
            self.btn_frame, text="Zkontrolovat", width=100,
            command=self._check_update
        )
        self.check_update_btn.pack(side="left", padx=5)

        self.progress = ctk.CTkProgressBar(self.btn_frame, width=100, mode="indeterminate")

    def _check_update(self):
        if self.checking_update or self.action_in_progress:
            return
        self.checking_update = True
        self.check_update_btn.configure(state="disabled", text="Kontroluji...")
        self.on_status(f"Kontroluji aktualizace pro {self.package.name}...")

        def on_version(version: Optional[str]):
            self.checking_update = False
            self.check_update_btn.configure(state="normal", text="Zkontrolovat")
            if version and version != self.package.version:
                self.package.available_version = version
                self.update_indicator.configure(text=f"→ {version}", text_color="orange")
                self.update_btn.pack(side="left", padx=5)
                self.on_status(f"Nalezena nová verze {version} pro {self.package.name}")
            else:
                self.update_indicator.configure(text="Aktuální", text_color="green")
                self.on_status(f"{self.package.name} je aktuální")

        self.winget.get_available_version_async(self.package.id, on_version)

    def _uninstall(self):
        if self.action_in_progress:
            return
        self._set_busy(True, "Odinstaluji...")
        self.on_status(f"Odinstaluji {self.package.name}...")

        def on_done(success: bool):
            self._set_busy(False)
            if success:
                self.on_status(f"{self.package.name} odinstalován")
                self.on_refresh()
            else:
                self.on_status(f"Chyba při odinstalování {self.package.name}")

        self.winget.uninstall_async(self.package.id, on_done)

    def _upgrade(self):
        if self.action_in_progress or not self.package.has_update:
            return
        self._set_busy(True, "Aktualizuji...")
        self.on_status(f"Aktualizuji {self.package.name} na v{self.package.available_version}...")

        def on_done(success: bool):
            self._set_busy(False)
            if success:
                self.on_status(f"{self.package.name} aktualizován na v{self.package.available_version}")
                self.on_refresh()
            else:
                self.on_status(f"Chyba při aktualizaci {self.package.name}")

        self.winget.upgrade_async(self.package.id, on_done)

    def _set_busy(self, busy: bool, text: str = ""):
        self.action_in_progress = busy
        state = "disabled" if busy else "normal"
        self.uninstall_btn.configure(state=state)
        self.check_update_btn.configure(state=state)
        if self.package.has_update:
            self.update_btn.configure(state=state)
        if busy:
            self.progress.pack(side="left", padx=5)
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.pack_forget()