from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.commands import (
    fastboot_boot,
    fastboot_erase,
    fastboot_flashing,
    fastboot_flash,
    fastboot_flashall,
    fastboot_format,
    fastboot_getvar_all,
    fastboot_oem,
    fastboot_reboot,
    fastboot_set_active,
    fastboot_wipe,
)
from core.utils import file_size, format_size, sha256_file
from ui.widgets import OutputPanel
from .base import BasePage

PARTITIONS = [
    "boot", "init_boot", "recovery", "vendor_boot", "dtbo", "vbmeta", "vbmeta_system",
    "system", "system_ext", "vendor", "product", "odm", "radio", "bootloader",
    "super", "metadata", "userdata", "cache", "misc",
]


class FastbootPage(BasePage):
    page_title = "Fastboot console"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.queue: list[dict] = []
        self.busy = False

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="Fastboot console", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        self.target_label = ctk.CTkLabel(header, text="No device selected", text_color="gray")
        self.target_label.pack(side="left", padx=14)
        ctk.CTkButton(header, text="Getvar all", command=self.getvar).pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(left, text="Image flash", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(12, 6)
        )
        ctk.CTkLabel(left, text="Partition").grid(row=1, column=0, sticky="w", padx=14, pady=4)
        self.partition = ctk.CTkComboBox(left, values=PARTITIONS, width=180)
        self.partition.set("boot")
        self.partition.grid(row=1, column=1, columnspan=2, sticky="ew", padx=8, pady=4)

        ctk.CTkLabel(left, text="Image").grid(row=2, column=0, sticky="w", padx=14, pady=4)
        self.image = ctk.CTkEntry(left, placeholder_text="Select an image file")
        self.image.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        ctk.CTkButton(left, text="Browse", width=80, command=self.browse_image).grid(row=2, column=2, padx=8, pady=4)

        ctk.CTkButton(left, text="Add to queue", command=self.add_to_queue).grid(row=3, column=1, sticky="ew", padx=8, pady=8)
        ctk.CTkButton(left, text="Flash now", fg_color="#2563eb", command=self.flash_now).grid(
            row=3, column=2, sticky="ew", padx=8, pady=8
        )

        queue_frame = ctk.CTkFrame(left)
        queue_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=12, pady=(4, 12))
        queue_frame.grid_columnconfigure(0, weight=1)
        queue_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(queue_frame, text="Flash queue", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(8, 2)
        )
        self.queue_box = ctk.CTkTextbox(queue_frame, font=ctk.CTkFont("Consolas", 11))
        self.queue_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 6))
        self.queue_box.configure(state="disabled")
        queue_actions = ctk.CTkFrame(queue_frame, fg_color="transparent")
        queue_actions.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        ctk.CTkButton(queue_actions, text="Flash queue", command=self.flash_queue, fg_color="#16a34a").pack(side="left", padx=4)
        ctk.CTkButton(queue_actions, text="Remove last", command=self.remove_last, fg_color="transparent").pack(side="left", padx=4)
        ctk.CTkButton(queue_actions, text="Clear", command=self.clear_queue, fg_color="transparent").pack(side="left", padx=4)
        left.grid_rowconfigure(4, weight=1)

        right = ctk.CTkFrame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        self.output = OutputPanel(right, height=260)
        self.output.grid(row=0, column=0, sticky="nsew")

        advanced = ctk.CTkFrame(right)
        advanced.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        advanced.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkLabel(advanced, text="Advanced operations", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(12, 6)
        )

        ctk.CTkButton(advanced, text="Boot image", command=self.boot_image).grid(row=1, column=0, padx=6, pady=5)
        ctk.CTkButton(advanced, text="Flash all folder", command=self.flash_all).grid(row=1, column=1, padx=6, pady=5)
        ctk.CTkButton(advanced, text="Getvar all", command=self.getvar).grid(row=1, column=2, padx=6, pady=5)

        ctk.CTkButton(advanced, text="Erase partition", fg_color="#b45309", command=self.erase).grid(row=2, column=0, padx=6, pady=5)
        ctk.CTkButton(advanced, text="Format partition", fg_color="#b45309", command=self.format_partition).grid(
            row=2, column=1, padx=6, pady=5
        )
        ctk.CTkButton(advanced, text="Wipe", fg_color="#dc2626", command=self.wipe).grid(row=2, column=2, padx=6, pady=5)

        ctk.CTkButton(advanced, text="Unlock", fg_color="#dc2626", command=self.unlock).grid(row=3, column=0, padx=6, pady=5)
        ctk.CTkButton(advanced, text="Lock", fg_color="#dc2626", command=self.lock).grid(row=3, column=1, padx=6, pady=5)
        self.slot = ctk.CTkComboBox(advanced, values=["a", "b"], width=70)
        self.slot.set("a")
        self.slot.grid(row=3, column=2, padx=6, pady=5)
        ctk.CTkButton(advanced, text="Set active", command=self.set_active).grid(row=4, column=2, padx=6, pady=5)

        self.oem_entry = ctk.CTkEntry(advanced, placeholder_text="OEM command, for example device-info")
        self.oem_entry.grid(row=4, column=0, columnspan=2, sticky="ew", padx=6, pady=5)
        ctk.CTkButton(advanced, text="OEM", command=self.oem).grid(row=4, column=2, padx=6, pady=5)

        reboot_row = ctk.CTkFrame(advanced, fg_color="transparent")
        reboot_row.grid(row=5, column=0, columnspan=3, sticky="ew", padx=6, pady=(6, 12))
        for text, mode in [
            ("Reboot", None),
            ("Bootloader", "bootloader"),
            ("Recovery", "recovery"),
            ("Fastboot", "fastboot"),
        ]:
            ctk.CTkButton(
                reboot_row,
                text=text,
                width=100,
                fg_color="transparent",
                command=lambda m=mode: self.reboot(m),
            ).pack(side="left", padx=3)

        self.progress = ctk.CTkLabel(self, text="No image size limit. Verify every image before flashing.", text_color="gray")
        self.progress.grid(row=2, column=0, sticky="w", pady=(8, 0))

    def on_show(self) -> None:
        self.target_label.configure(text=self.app.target())

    def on_devices_changed(self, devices) -> None:
        self.target_label.configure(text=self.app.target())

    # ---------- queue helpers ----------

    def browse_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select image",
            filetypes=[("Image files", "*.img *.bin *.elf"), ("All files", "*.*")],
            initialdir=self.app.settings.get("last_image_folder") or None,
        )
        if path:
            self.image.delete(0, "end")
            self.image.insert(0, path)
            self.app.settings.set("last_image_folder", str(Path(path).parent))

    def add_to_queue(self) -> None:
        partition = self.partition.get().strip()
        path = self.image.get().strip()
        if not partition or not path or not Path(path).is_file():
            messagebox.showwarning("Missing image", "Select a valid image file.")
            return
        entry = {
            "partition": partition,
            "image": path,
            "size": format_size(file_size(path)),
            "sha256": "hashing...",
        }
        self.queue.append(entry)
        self._render_queue()

        def hash_done(digest: str) -> None:
            entry["sha256"] = digest
            self._render_queue()

        self.app.run_async(lambda p=path: sha256_file(p), on_done=hash_done)

    def remove_last(self) -> None:
        if self.queue:
            self.queue.pop()
            self._render_queue()

    def clear_queue(self) -> None:
        self.queue.clear()
        self._render_queue()

    def _render_queue(self) -> None:
        lines = []
        for index, entry in enumerate(self.queue, 1):
            lines.append(
                f"{index}. {entry['partition']:<16} {entry['size']:<12} {entry['sha256']}\n   {entry['image']}"
            )
        text = "\n\n".join(lines) if lines else "Queue is empty."
        self.queue_box.configure(state="normal")
        self.queue_box.delete("1.0", "end")
        self.queue_box.insert("end", text)
        self.queue_box.configure(state="disabled")

    # ---------- operations ----------

    def _flash_one(self, entry: dict, on_complete) -> None:
        serial = self.app.require_serial("fastboot")
        if not serial:
            on_complete(False)
            return
        self.progress.configure(text=f"Flashing {entry['partition']} from {Path(entry['image']).name}")
        args = fastboot_flash(serial, entry["partition"], entry["image"])
        self.app.run_command(
            args,
            f"Flash {entry['partition']}",
            on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            on_done=lambda result: on_complete(result.ok),
            confirm=True,
        )

    def flash_now(self) -> None:
        partition = self.partition.get().strip()
        path = self.image.get().strip()
        if not partition or not path or not Path(path).is_file():
            messagebox.showwarning("Missing image", "Select a valid image file.")
            return
        self._flash_one({"partition": partition, "image": path}, lambda ok: None)

    def flash_queue(self) -> None:
        if self.busy:
            return
        if not self.queue:
            messagebox.showinfo("Empty queue", "Add at least one image to the queue.")
            return
        self.busy = True
        self._run_queue(0)

    def _run_queue(self, index: int) -> None:
        if index >= len(self.queue):
            self.busy = False
            self.progress.configure(text="Flash queue completed.")
            return

        def next_step(success: bool) -> None:
            if not success:
                self.busy = False
                self.progress.configure(text=f"Flash queue stopped at step {index + 1}.")
                return
            self._run_queue(index + 1)

        self.progress.configure(text=f"Queue {index + 1}/{len(self.queue)}")
        self._flash_one(self.queue[index], next_step)

    def boot_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select boot image",
            filetypes=[("Image files", "*.img"), ("All files", "*.*")],
            initialdir=self.app.settings.get("last_image_folder") or None,
        )
        serial = self.app.require_serial("fastboot")
        if not serial or not path:
            return
        self.app.run_command(
            fastboot_boot(serial, path),
            "Boot image",
            confirm=True,
            on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
        )

    def flash_all(self) -> None:
        folder = filedialog.askdirectory(title="Select folder containing flashall images")
        serial = self.app.require_serial("fastboot")
        if not serial or not folder:
            return
        self.app.run_command(
            fastboot_flashall(serial, folder),
            "Flash all images from folder",
            confirm=True,
            on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
        )

    def getvar(self) -> None:
        serial = self.app.require_serial("fastboot")
        if not serial:
            return

        def finish(result) -> None:
            self.output.set_text(result.output)

        self.app.run_command(fastboot_getvar_all(serial), "Read fastboot variables", on_done=finish)

    def erase(self) -> None:
        serial = self.app.require_serial("fastboot")
        partition = self.partition.get().strip()
        if serial and partition:
            self.app.run_command(
                fastboot_erase(serial, partition),
                f"Erase {partition}",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )

    def format_partition(self) -> None:
        serial = self.app.require_serial("fastboot")
        partition = self.partition.get().strip()
        if serial and partition:
            self.app.run_command(
                fastboot_format(serial, partition),
                f"Format {partition}",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )

    def wipe(self) -> None:
        serial = self.app.require_serial("fastboot")
        if serial:
            self.app.run_command(
                fastboot_wipe(serial),
                "Wipe device",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )

    def unlock(self) -> None:
        serial = self.app.require_serial("fastboot")
        if serial:
            self.app.run_command(
                fastboot_flashing(serial, "unlock"),
                "Unlock bootloader",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )

    def lock(self) -> None:
        serial = self.app.require_serial("fastboot")
        if serial:
            self.app.run_command(
                fastboot_flashing(serial, "lock"),
                "Lock bootloader",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )

    def set_active(self) -> None:
        serial = self.app.require_serial("fastboot")
        if serial:
            self.app.run_command(
                fastboot_set_active(serial, self.slot.get()),
                f"Set active slot {self.slot.get()}",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )

    def oem(self) -> None:
        serial = self.app.require_serial("fastboot")
        command = self.oem_entry.get().strip()
        if serial and command:
            self.app.run_command(
                fastboot_oem(serial, command),
                f"OEM {command}",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )

    def reboot(self, mode: str | None) -> None:
        serial = self.app.require_serial("fastboot")
        if serial:
            label = "Reboot" if mode is None else f"Reboot to {mode}"
            self.app.run_command(
                fastboot_reboot(serial, mode),
                label,
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )
