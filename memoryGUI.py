import tkinter as tk
from tkinter import ttk, filedialog, messagebox

MEMORY_SIZE = 65536  # 64 KB memory


class MemoryVisualizer:

    def __init__(self, root):
        self.root = root
        self.root.title("SIC/XE Memory Visualizer")
        self.root.geometry("1400x800")
        self.root.configure(bg="#1e1e1e")

        self.memory = ["00"] * MEMORY_SIZE

        self.create_widgets()

    # =========================================================
    # GUI DESIGN
    # =========================================================
    def create_widgets(self):

        # ---------------- TOP FRAME ----------------
        top_frame = tk.Frame(self.root, bg="#1e1e1e")
        top_frame.pack(fill="x", padx=10, pady=10)

        title = tk.Label(
            top_frame,
            text="SIC/XE MEMORY VISUALIZER",
            font=("Consolas", 22, "bold"),
            fg="#00ffcc",
            bg="#1e1e1e"
        )
        title.pack(side="left")

        load_btn = tk.Button(
            top_frame,
            text="Load HTME",
            command=self.load_htme,
            bg="#00aa88",
            fg="white",
            font=("Consolas", 12, "bold"),
            padx=15
        )
        load_btn.pack(side="right", padx=5)

        clear_btn = tk.Button(
            top_frame,
            text="Clear Memory",
            command=self.clear_memory,
            bg="#aa3333",
            fg="white",
            font=("Consolas", 12, "bold"),
            padx=15
        )
        clear_btn.pack(side="right", padx=5)

        # ---------------- MEMORY TABLE ----------------
        table_frame = tk.Frame(self.root, bg="#1e1e1e")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ["Address"] + [f"{i:X}" for i in range(16)]

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=30
        )

        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=28,
            font=("Consolas", 11)
        )

        style.configure(
            "Treeview.Heading",
            background="#444444",
            foreground="#00ffcc",
            font=("Consolas", 11, "bold")
        )

        # Column setup
        for col in columns:
            self.tree.heading(col, text=col)

            if col == "Address":
                self.tree.column(col, width=100, anchor="center")
            else:
                self.tree.column(col, width=55, anchor="center")

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar_x = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        # ---------------- STATUS BAR ----------------
        self.status = tk.Label(
            self.root,
            text="Memory Empty",
            anchor="w",
            bg="#111111",
            fg="#00ffcc",
            font=("Consolas", 11)
        )

        self.status.pack(fill="x")

        self.display_memory()

    # =========================================================
    # CLEAR MEMORY
    # =========================================================
    def clear_memory(self):

        self.memory = ["00"] * MEMORY_SIZE

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.display_memory()

        self.status.config(text="Memory Cleared")

    # =========================================================
    # LOAD HTME FILE
    # =========================================================
    def load_htme(self):

        file_path = filedialog.askopenfilename(
            title="Select HTME File",
            filetypes=[("Text Files", "*.txt")]
        )

        if not file_path:
            return

        try:
            self.memory = ["00"] * MEMORY_SIZE

            with open(file_path, "r") as f:

                lines = f.readlines()

                for line in lines:

                    line = line.strip()

                    # Parse T records only
                    if line.startswith("T."):

                        parts = line.split(".")

                        start_addr = int(parts[1], 16)

                        obj_code = parts[3]

                        # Load bytes into memory
                        for i in range(0, len(obj_code), 2):

                            byte = obj_code[i:i+2]

                            mem_addr = start_addr + (i // 2)

                            if mem_addr < MEMORY_SIZE:
                                self.memory[mem_addr] = byte

            # Refresh table
            for row in self.tree.get_children():
                self.tree.delete(row)

            self.display_memory()

            self.status.config(
                text=f"Loaded {file_path}"
            )

            messagebox.showinfo(
                "Success",
                "HTME file loaded successfully!"
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

    # =========================================================
    # DISPLAY MEMORY
    # =========================================================
    def display_memory(self):

        for addr in range(0, MEMORY_SIZE, 16):

            row = [f"{addr:06X}"]

            for i in range(16):
                row.append(self.memory[addr + i])

            self.tree.insert("", "end", values=row)


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":

    root = tk.Tk()

    app = MemoryVisualizer(root)

    root.mainloop()