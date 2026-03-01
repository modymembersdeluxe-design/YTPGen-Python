import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


class YTPGenGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YTPGen Mega - Python Backend UI")
        self.root.geometry("920x700")
        self.process = None

        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.audio_lib_var = tk.StringVar()
        self.temp_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="STANDARD")
        self.format_var = tk.StringVar(value="mp4")
        self.resolution_var = tk.StringVar(value="1280x720")
        self.clip_count_var = tk.StringVar(value="20")
        self.min_duration_var = tk.StringVar(value="0.5")
        self.max_duration_var = tk.StringVar(value="2.5")
        self.bitrate_var = tk.StringVar(value="2500k")
        self.bpm_var = tk.StringVar(value="120")
        self.project_name_var = tk.StringVar(value="YTPGen Mega Project")
        self.scale_var = tk.StringVar(value="")

        self.no_video_effects_var = tk.BooleanVar(value=False)
        self.no_audio_effects_var = tk.BooleanVar(value=False)
        self.export_metadata_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        wrapper = tk.Frame(self.root, padx=10, pady=10)
        wrapper.pack(fill="both", expand=True)

        title = tk.Label(
            wrapper,
            text="YTPGen Mega Python Generator (UI)",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        )
        title.pack(fill="x", pady=(0, 8))

        sub = tk.Label(
            wrapper,
            text="Windows 7/8.1 compatible Tkinter front-end for ytpgen_py_generator.py",
            anchor="w",
        )
        sub.pack(fill="x", pady=(0, 10))

        settings = tk.LabelFrame(wrapper, text="Project Settings", padx=8, pady=8)
        settings.pack(fill="x", pady=(0, 8))

        self._path_row(settings, "Source Folder", self.source_var, self._browse_source, 0)
        self._path_row(settings, "Output File", self.output_var, self._browse_output, 1)
        self._path_row(settings, "Audio Library", self.audio_lib_var, self._browse_audio_library, 2)
        self._path_row(settings, "Temp Folder", self.temp_var, self._browse_temp, 3)

        options = tk.LabelFrame(wrapper, text="Generator Options", padx=8, pady=8)
        options.pack(fill="x", pady=(0, 8))

        self._entry_row(options, "Mode", self.mode_var, 0, as_option=True, values=["STANDARD", "YTPMV", "TENNIS", "COLLAB"])
        self._entry_row(options, "Format", self.format_var, 1, as_option=True, values=["mp4", "wmv", "avi", "mkv"])
        self._entry_row(options, "Resolution", self.resolution_var, 2)
        self._entry_row(options, "Clip Count", self.clip_count_var, 3)
        self._entry_row(options, "Min Duration", self.min_duration_var, 4)
        self._entry_row(options, "Max Duration", self.max_duration_var, 5)
        self._entry_row(options, "Bitrate", self.bitrate_var, 6)
        self._entry_row(options, "BPM (YTPMV)", self.bpm_var, 7)
        self._entry_row(options, "Project Name", self.project_name_var, 8)
        self._entry_row(options, "Scale (optional)", self.scale_var, 9)

        toggles = tk.Frame(options)
        toggles.grid(row=10, column=0, columnspan=3, sticky="w", pady=(8, 0))

        tk.Checkbutton(toggles, text="Disable video effects", variable=self.no_video_effects_var).pack(side="left", padx=(0, 12))
        tk.Checkbutton(toggles, text="Disable audio effects", variable=self.no_audio_effects_var).pack(side="left", padx=(0, 12))
        tk.Checkbutton(toggles, text="Export metadata", variable=self.export_metadata_var).pack(side="left")

        actions = tk.LabelFrame(wrapper, text="Actions", padx=8, pady=8)
        actions.pack(fill="x", pady=(0, 8))

        self.run_button = tk.Button(actions, text="Run Generator", width=16, command=self.run_generator)
        self.run_button.pack(side="left", padx=(0, 8))

        self.stop_button = tk.Button(actions, text="Stop", width=10, command=self.stop_generator, state="disabled")
        self.stop_button.pack(side="left", padx=(0, 8))

        self.preview_button = tk.Button(actions, text="Preview Command", width=14, command=self.preview_command)
        self.preview_button.pack(side="left", padx=(0, 8))

        self.clear_button = tk.Button(actions, text="Clear Log", width=10, command=self.clear_log)
        self.clear_button.pack(side="left", padx=(0, 8))

        log_frame = tk.LabelFrame(wrapper, text="Console Output", padx=8, pady=8)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=18, wrap="word", bg="#111", fg="#e7e7e7")
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _path_row(self, parent, label_text, var, callback, row):
        label = tk.Label(parent, text=label_text, width=16, anchor="w")
        label.grid(row=row, column=0, sticky="w", pady=2)

        entry = tk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=(4, 4), pady=2)

        button = tk.Button(parent, text="Browse", width=10, command=callback)
        button.grid(row=row, column=2, sticky="e", pady=2)

        parent.grid_columnconfigure(1, weight=1)

    def _entry_row(self, parent, label_text, var, row, as_option=False, values=None):
        label = tk.Label(parent, text=label_text, width=16, anchor="w")
        label.grid(row=row, column=0, sticky="w", pady=2)

        if as_option:
            menu = tk.OptionMenu(parent, var, *(values or []))
            menu.config(width=24)
            menu.grid(row=row, column=1, sticky="w", padx=(4, 4), pady=2)
        else:
            entry = tk.Entry(parent, textvariable=var, width=30)
            entry.grid(row=row, column=1, sticky="w", padx=(4, 4), pady=2)

    def _browse_source(self):
        path = filedialog.askdirectory(title="Select source media folder")
        if path:
            self.source_var.set(path)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Select output file",
            defaultextension=".mp4",
            filetypes=[
                ("Video Files", "*.mp4 *.wmv *.avi *.mkv"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            self.output_var.set(path)

    def _browse_audio_library(self):
        path = filedialog.askdirectory(title="Select audio library folder")
        if path:
            self.audio_lib_var.set(path)

    def _browse_temp(self):
        path = filedialog.askdirectory(title="Select temp folder")
        if path:
            self.temp_var.set(path)

    def _build_command(self):
        source = self.source_var.get().strip()
        output = self.output_var.get().strip()

        if not source:
            raise ValueError("Source folder is required.")
        if not output:
            raise ValueError("Output file is required.")

        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ytpgen_py_generator.py")
        if not os.path.isfile(script_path):
            raise ValueError("ytpgen_py_generator.py not found in current folder.")

        cmd = [
            sys.executable,
            script_path,
            "--source",
            source,
            "--output",
            output,
            "--mode",
            self.mode_var.get().strip() or "STANDARD",
            "--clip-count",
            self.clip_count_var.get().strip() or "20",
            "--min-duration",
            self.min_duration_var.get().strip() or "0.5",
            "--max-duration",
            self.max_duration_var.get().strip() or "2.5",
            "--resolution",
            self.resolution_var.get().strip() or "1280x720",
            "--format",
            self.format_var.get().strip() or "mp4",
            "--bitrate",
            self.bitrate_var.get().strip() or "2500k",
            "--project-name",
            self.project_name_var.get().strip() or "YTPGen Mega Project",
            "--bpm",
            self.bpm_var.get().strip() or "120",
        ]

        if self.audio_lib_var.get().strip():
            cmd.extend(["--audio-library", self.audio_lib_var.get().strip()])
        if self.temp_var.get().strip():
            cmd.extend(["--temp-folder", self.temp_var.get().strip()])
        if self.scale_var.get().strip():
            cmd.extend(["--scale", self.scale_var.get().strip()])

        if self.no_video_effects_var.get():
            cmd.append("--no-video-effects")
        if self.no_audio_effects_var.get():
            cmd.append("--no-audio-effects")
        if self.export_metadata_var.get():
            cmd.append("--export-metadata")

        return cmd

    def preview_command(self):
        try:
            cmd = self._build_command()
            self._log("[PREVIEW] %s\n" % self._format_cmd(cmd))
        except Exception as exc:
            messagebox.showerror("Command Error", str(exc))

    def run_generator(self):
        if self.process is not None:
            messagebox.showwarning("Already Running", "A generation process is already running.")
            return

        try:
            cmd = self._build_command()
        except Exception as exc:
            messagebox.showerror("Configuration Error", str(exc))
            return

        self._log("[INFO] Starting generator...\n")
        self._log("[CMD] %s\n\n" % self._format_cmd(cmd))

        self.run_button.config(state="disabled")
        self.stop_button.config(state="normal")

        thread = threading.Thread(target=self._run_process_thread, args=(cmd,))
        thread.daemon = True
        thread.start()

    def _run_process_thread(self, cmd):
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                self._threadsafe_log(line)

            exit_code = self.process.wait()
            self._threadsafe_log("\n[INFO] Generator exited with code %d\n" % exit_code)
        except Exception as exc:
            self._threadsafe_log("\n[ERROR] %s\n" % str(exc))
        finally:
            self.process = None
            self.root.after(0, self._unlock_buttons)

    def stop_generator(self):
        if self.process is None:
            return
        try:
            self.process.terminate()
            self._log("[WARN] Stop requested by user.\n")
        except Exception as exc:
            self._log("[ERROR] Failed to stop process: %s\n" % str(exc))

    def _unlock_buttons(self):
        self.run_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    def _log(self, text):
        self.log_text.insert("end", text)
        self.log_text.see("end")

    def _threadsafe_log(self, text):
        self.root.after(0, lambda: self._log(text))

    def _format_cmd(self, cmd):
        formatted = []
        for part in cmd:
            if " " in part:
                formatted.append('"%s"' % part)
            else:
                formatted.append(part)
        return " ".join(formatted)


def main():
    root = tk.Tk()
    app = YTPGenGuiApp(root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()
