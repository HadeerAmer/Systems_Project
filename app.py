"""
SIC/XE Assembler — Web GUI
Run with:  python app.py
Then open: http://localhost:5000
"""

import os
import sys
import json
import tempfile
import shutil
from flask import Flask, request, jsonify, send_from_directory

# ── Make sure pass1/pass2 are importable from the same directory ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pass1 import run_pass1
from pass2 import run_pass2

app = Flask(__name__, static_folder="static")

OUTPUT_FILES = [
    ("intermediate.txt",  "Intermediate"),
    ("symbTable.txt",     "Symbol Table"),
    ("poolTable.txt",     "Pool Table"),
    ("blockTable.txt",    "Block Table"),
    ("out_pass2.txt",     "Pass 2 Output"),
    ("HTME.txt",          "HTME Records"),
    ("error.txt",         "Errors"),
]


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/assemble", methods=["POST"])
def assemble():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"ok": False, "error": "Empty filename"}), 400

    # Write uploaded file to a temp directory
    tmp_dir  = tempfile.mkdtemp()
    in_path  = os.path.join(tmp_dir, "in.txt")
    uploaded.save(in_path)

    result = {"ok": True, "files": {}}

    try:
        symtab, pooltab, block_abs, blocks, block_order, intermediate, prog_start, total_len = run_pass1(in_path)
        run_pass2(intermediate, symtab, pooltab, in_path)

        # On success: clear error.txt
        err_path = os.path.join(tmp_dir, "error.txt")
        with open(err_path, "w") as f:
            f.write("")

    except SystemExit:
        # An error() call happened — read whatever files exist
        result["ok"] = False

    # Collect all output files (empty or not)
    for fname, label in OUTPUT_FILES:
        fpath = os.path.join(tmp_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", errors="replace") as f:
                content = f.read()
        else:
            content = ""
        result["files"][label] = content

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return jsonify(result)


if __name__ == "__main__":
    # Create static folder if needed
    os.makedirs(os.path.join(os.path.dirname(__file__), "static"), exist_ok=True)
    print("SIC/XE Assembler GUI running at http://localhost:5000")
    app.run(debug=False, port=5000)