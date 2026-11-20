from __future__ import annotations

import os
import threading
import tkinter.messagebox as messagebox
from tkinter import filedialog

import customtkinter as ctk

from core.tools import license_path
from core.vendor_tools import TOOLS, ToolStatus, VendorTool
from ui.tool_host import EmbeddedToolHost

from .base import BasePage

STATUS_COLORS = {
    "ready": "#16a34a",
    "bundled": "#2563eb",
    "setup": "#d97706",
    "missing": "#dc2626",
    "error": "#dc2626",
    "excluded": "gray",
}

GROUPS = ("All", "Core", "Drivers", "MediaTek", "Qualcomm", "Samsung", "Xiaomi", "Excluded")


class ToolsPage(BasePage):
    page_title = "Vendor tools"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._cards: dict[str, dict[str, object]] = {}
        self._filter = "All"
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Bundled vendor tools",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Click 'Open in app' and the tool opens inside this window. Installers and CLI tools open normally.",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65"),
        ).grid(row=1, column=0, sticky="w")
        ctk.CTkButton(
            header,
            text="Prepare all",
            width=110,
            command=self.unpack_all,
        ).grid(row=0, column=1, rowspan=2, padx=6)
        ctk.CTkButton(
            header,
            text="Notices",
            width=90,
            command=self.open_notices,
            fg_color="transparent",
        ).grid(row=0, column=2, rowspan=2, padx=6)
        ctk.CTkButton(
            header,
            text="Refresh",
            width=90,
            command=self.refresh,
            fg_color="transparent",
        ).grid(row=0, column=3, rowspan=2, padx=6)

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(filters, text="Group", width=60, anchor="w").pack(side="left", padx=(2, 6))
        self.group_combo = ctk.CTkComboBox(
            filters,
            values=list(GROUPS),
            width=150,
            command=self.set_filter,
        )
        self.group_combo.set("All")
        self.group_combo.pack(side="left", padx=4)
        ctk.CTkLabel(filters, text="Search", width=60, anchor="w").pack(side="left", padx=(18, 6))
        self.search = ctk.CTkEntry(filters, width=260, placeholder_text="Tool name or vendor")
        self.search.pack(side="left", padx=4)
        ctk.CTkButton(filters, text="Find", width=70, command=self.refresh).pack(side="left", padx=4)
        ctk.CTkButton(filters, text="Clear", width=70, fg_color="transparent", command=self.clear_search).pack(
            side="left", padx=4
        )

        self.scroll = ctk.CTkScrollableFrame(self, label_text="")
        self.scroll.grid(row=2, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

        host = ctk.CTkFrame(self, corner_radius=12)
        host.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        host.grid_columnconfigure(0, weight=1)
        host.grid_rowconfigure(1, weight=1)
        host_header = ctk.CTkFrame(host, fg_color="transparent")
        host_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        host_header.grid_columnconfigure(0, weight=1)
        self.host_title = ctk.CTkLabel(
            host_header,
            text="Tool window: none",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.host_title.grid(row=0, column=0, sticky="w")
        self.host_detail = ctk.CTkLabel(
            host_header,
            text="Compatible tools open here, inside FlashBridge PC.",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray65"),
        )
        self.host_detail.grid(row=1, column=0, sticky="w")
        self.close_tool = ctk.CTkButton(
            host_header,
            text="Close tool",
            width=90,
            state="disabled",
            command=self._close_tool,
        )
        self.close_tool.grid(row=0, column=1, rowspan=2, padx=6)

        self.embed_frame = ctk.CTkFrame(host, corner_radius=8, fg_color=("#e8f1ff", "#050914"), height=260)
        self.embed_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.embed_frame.grid_propagate(False)
        self.placeholder = ctk.CTkLabel(
            self.embed_frame,
            text="No tool is open.\nClick 'Open in app' on a tool card to show it here.",
            justify="center",
            text_color=("gray45", "gray65"),
        )
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
        self.host = EmbeddedToolHost(self.app, self.embed_frame, on_state=self._host_state)

        notice = ctk.CTkFrame(self, fg_color=("gray88", "gray15"))
        notice.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        ctk.CTkLabel(
            notice,
            text=(
                "Compatible tools are prepared automatically on first use and shown in the tool window. "
                "Installers need administrator approval. Mi tools require Xiaomi account permission. "
                "Odin has no official public package and is not bundled. Security bypass utilities are not included."
            ),
            wraplength=1100,
            justify="left",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=12, pady=8)

        self.refresh()

    # ---------- rendering ----------

    def on_show(self) -> None:
        self.refresh()

    def clear_search(self) -> None:
        self.search.delete(0, "end")
        self.group_combo.set("All")
        self._filter = "All"
        self.refresh()

    def set_filter(self, value: str) -> None:
        self._filter = value
        self.refresh()

    def visible_tools(self) -> list[VendorTool]:
        term = self.search.get().strip().lower()
        result = []
        for tool in TOOLS:
            if self._filter != "All" and tool.group != self._filter:
                continue
            haystack = f"{tool.name} {tool.group} {tool.version} {tool.summary}".lower()
            if term and term not in haystack:
                continue
            result.append(tool)
        return result

    def refresh(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        self._cards.clear()
        tools = self.visible_tools()
        for index, tool in enumerate(tools):
            status = self.app.vendor.status(tool, prepare=False)
            card = self._build_card(tool, status)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=6, pady=6)

    def _build_card(self, tool: VendorTool, status: ToolStatus):
        card = ctk.CTkFrame(self.scroll, corner_radius=10)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(card, text=tool.group, font=ctk.CTkFont(size=10, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=(14, 8), pady=(12, 0)
        )
        ctk.CTkLabel(card, text=tool.version, font=ctk.CTkFont(size=10)).grid(
            row=0, column=1, sticky="e", padx=8, pady=(12, 0)
        )
        ctk.CTkLabel(card, text=tool.name, font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=14, pady=(2, 4)
        )
        ctk.CTkLabel(card, text=tool.summary, wraplength=440, justify="left").grid(
            row=2, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 6)
        )

        dot = ctk.CTkLabel(card, text="●", text_color=STATUS_COLORS.get(status.state, "gray"))
        dot.grid(row=3, column=0, sticky="w", padx=14, pady=2)
        status_label = ctk.CTkLabel(
            card,
            text=f"{status.state.upper()}: {status.detail}",
            wraplength=430,
            justify="left",
            font=ctk.CTkFont(size=11),
        )
        status_label.grid(row=3, column=1, sticky="w", padx=(2, 8), pady=2)
        if tool.note:
            ctk.CTkLabel(
                card,
                text=tool.note,
                wraplength=440,
                justify="left",
                font=ctk.CTkFont(size=10),
                text_color=("gray45", "gray65"),
            ).grid(row=4, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 6))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 12))
        if tool.installer:
            launch_text = "Run installer"
        elif tool.console:
            launch_text = "Open console"
        else:
            launch_text = "Open in app"
        launch = ctk.CTkButton(
            actions,
            text=launch_text,
            width=130,
            state="disabled" if tool.excluded else "normal",
            command=lambda current=tool: self.launch(current),
        )
        launch.pack(side="left", padx=4)
        ctk.CTkButton(
            actions,
            text="Open folder",
            width=105,
            fg_color="transparent",
            state="disabled" if tool.excluded else "normal",
            command=lambda current=tool: self.open_folder(current),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            actions,
            text="Set path",
            width=90,
            fg_color="transparent",
            state="disabled" if tool.excluded else "normal",
            command=lambda current=tool: self.set_path(current),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            actions,
            text="Clear",
            width=70,
            fg_color="transparent",
            state="disabled" if tool.excluded or not self.app.vendor.user_path(tool.id) else "normal",
            command=lambda current=tool: self.clear_path(current),
        ).pack(side="left", padx=4)

        self._cards[tool.id] = {"dot": dot, "status": status_label, "launch": launch}
        return card

    # ---------- actions ----------

    def _close_tool(self) -> None:
        self.host.close()
        self.host_title.configure(text="Tool window: none")
        self.host_detail.configure(text="Compatible tools open here, inside FlashBridge PC.")
        self.placeholder.configure(
            text="No tool is open.\nClick 'Open in app' on a tool card to show it here."
        )
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
        self.close_tool.configure(state="disabled")

    def _host_state(self, event: str, tool_name: str, detail: str = "") -> None:
        if event == "preparing":
            self.host_title.configure(text=f"Preparing {tool_name}...")
            self.host_detail.configure(text="Unpacking if needed, then opening the tool window.")
            self.placeholder.configure(text=f"Starting {tool_name}...\nThis can take a few seconds.")
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.close_tool.configure(state="disabled")
            self.app.set_status(f"Starting {tool_name}", "run")
            return
        if event == "embedded":
            self.host_title.configure(text=f"Tool window: {tool_name}")
            self.host_detail.configure(text=detail or "Running inside FlashBridge PC.")
            self.placeholder.place_forget()
            self.close_tool.configure(state="normal")
            self.app.set_status(f"{tool_name} is open in the app", "ok")
            self.app.logs.log(f"{tool_name} embedded in the tool window.", "INFO", "vendor")
            self.refresh()
            return
        if event == "external":
            self.host_title.configure(text=f"{tool_name}: opened separately")
            self.host_detail.configure(text=detail)
            self.placeholder.configure(text=detail)
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.close_tool.configure(state="disabled")
            self.app.set_status(f"{tool_name} started", "ok")
            self.app.logs.log(f"{tool_name}: {detail}", "INFO", "vendor")
            return
        if event == "error":
            self.host_title.configure(text="Tool could not open")
            self.host_detail.configure(text=detail)
            self.placeholder.configure(text=detail)
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.close_tool.configure(state="disabled")
            self.app.set_status("Vendor tool failed", "error")
            self.app.logs.log(f"{tool_name}: {detail}", "ERROR", "vendor")
            messagebox.showerror("Vendor tools", detail)
            return
        if event == "closed":
            self._close_tool()

    def _finish(self, tool: VendorTool | None, message: str, error: bool = False) -> None:
        level = "ERROR" if error else "INFO"
        self.app.logs.log(message, level, "vendor")
        if not error:
            messagebox.showinfo("Vendor tools", message)
        else:
            messagebox.showerror("Vendor tools", message)
        self.refresh()

    def launch(self, tool: VendorTool) -> None:
        if not tool.installer and not tool.console:
            self.host.launch(tool)
            return

        self.app.set_status(f"Starting {tool.name}", "run")

        def worker() -> None:
            try:
                self.app.vendor.launch(tool)
                result = f"{tool.name} started."
                error = False
            except Exception as exc:
                result = f"Could not start {tool.name}: {exc}"
                error = True
            self.app.after(0, lambda: self._launch_done(tool, result, error))

        threading.Thread(target=worker, daemon=True).start()

    def _launch_done(self, tool: VendorTool, message: str, error: bool) -> None:
        self.app.set_status("Vendor tool failed" if error else "Vendor tool started", "error" if error else "ok")
        self.app.logs.log(message, "ERROR" if error else "INFO", "vendor")
        if error:
            messagebox.showerror("Vendor tools", message)
        self.refresh()

    def unpack_all(self) -> None:
        self.app.set_status("Unpacking vendor tools", "run")

        def worker() -> None:
            try:
                results = self.app.vendor.ensure_all()
                message = f"Unpacked {len(results)} bundled tool payloads."
                error = False
            except Exception as exc:
                message = str(exc)
                error = True
            self.app.after(0, lambda: self._finish(None, message, error))

        threading.Thread(target=worker, daemon=True).start()

    def open_folder(self, tool: VendorTool) -> None:
        try:
            self.app.vendor.open_folder(tool)
        except Exception as exc:
            messagebox.showerror("Vendor tools", f"Could not open the folder: {exc}")

    def set_path(self, tool: VendorTool) -> None:
        path = filedialog.askopenfilename(
            title=f"Select the {tool.name} launcher",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.app.vendor.set_user_path(tool.id, path)
            self._finish(tool, f"Saved launcher path for {tool.name}.")
        except Exception as exc:
            messagebox.showerror("Vendor tools", str(exc))

    def clear_path(self, tool: VendorTool) -> None:
        self.app.vendor.clear_user_path(tool.id)
        self._finish(tool, f"Cleared launcher path for {tool.name}.")

    def open_notices(self) -> None:
        try:
            os.startfile(str(license_path()))
        except Exception as exc:
            messagebox.showerror("Notices", f"Could not open notices: {exc}")
