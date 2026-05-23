import sys
import os


PASS2_FILES = ["out_pass2.txt", "HTME.txt"]


def _clear_pass2_outputs(out_dir):
    for fname in PASS2_FILES:
        with open(os.path.join(out_dir, fname), "w") as f:
            f.write("")


def _write_pass1_outputs(out_dir, intermediate, symtab, pooltab,
                         blocks, block_order, block_abs_start, total_length):
    """Write whatever pass1 built so far — even if incomplete due to an error."""

    # ── symbTable.txt ─────────────────────────────────────────────
    with open(os.path.join(out_dir, "symbTable.txt"), "w") as f:
        f.write("SYMBOL NAME  ADDRESS\n")
        
        for sym, val in symtab.items():
            if isinstance(val, tuple):
                blk, off = val
                addr = block_abs_start.get(blk, 0) + off if block_abs_start else off
            else:
                addr = val
            f.write(f"{sym:<12} {addr:04X}\n")

    # ── poolTable.txt ─────────────────────────────────────────────
    with open(os.path.join(out_dir, "poolTable.txt"), "w") as f:
        f.write("POOL NAME  ADDRESS  LENGTH  OBJECT CODE\n")
        for lit, data in pooltab.items():
            addr = data.get("addr", data.get("block_offset", 0))
            f.write(f"{lit:<10} {addr:04X}     {data['length']}       {data['obj']}\n")

    # ── blockTable.txt ────────────────────────────────────────────
    with open(os.path.join(out_dir, "blockTable.txt"), "w") as f:
        f.write("BLOCK NAME  BLOCK NUMBER  ADDRESS  SIZE\n")
        for bname in block_order:
            info      = blocks[bname]
            abs_start = block_abs_start.get(bname, 0) if block_abs_start else 0
            f.write(f"{bname:<10} {info['num']:<13} {abs_start:04X}     {info['lc']:04X}\n")
        f.write(f"\nTotal program length: {total_length:04X}\n")

    # ── intermediate.txt ──────────────────────────────────────────
    with open(os.path.join(out_dir, "intermediate.txt"), "w") as f:
        f.write("Location counter  Symbol   Instructions  Reference\n")
        f.write("----------------  -------  ------------  ----------\n")
        for blk, lc_val, label, opcode, operand in intermediate:
            if opcode == "_LIT_":
                continue
            lc_str  = f"{lc_val:04X}" if lc_val is not None else ""
            sym_str = label   if (label   and label   != "-") else ""
            op_str  = opcode  if opcode  else ""
            ref_str = operand if operand else ""
            f.write(f"{lc_str:<18} {sym_str:<9} {op_str:<14} {ref_str}\n")


def error(msg, lc, line_num=0, detail="", out_dir=".",
          intermediate=None, symtab=None, pooltab=None,
          blocks=None, block_order=None, block_abs_start=None, total_length=0):
    """
    On error:
      1. Write pass1 outputs with whatever was built so far
      2. Clear pass2 outputs
      3. Write error.txt
      4. Stop
    """
    
    if intermediate is not None:
        _write_pass1_outputs(
            out_dir,
            intermediate,
            symtab        or {},
            pooltab       or {},
            blocks        or {},
            block_order   or [],
            block_abs_start or {},
            total_length
        )

    
    _clear_pass2_outputs(out_dir)

    
    err_path = os.path.join(out_dir, "error.txt")
    with open(err_path, "w") as f:
        f.write(f"Error : {msg}\n")
        f.write(f"PC    : {lc:04X}\n")
        if line_num:
            f.write(f"Line  : line {line_num}\n")
        if detail:
            f.write(f"Detail: {detail}\n")

    print(f"ERROR: {msg} at {lc:04X}")
    if line_num:
        print(f"       Line {line_num}")
    if detail:
        print(f"       {detail}")
    print(f"       See {err_path}")

    
    sys.exit(1)



def get_literal_size(lit):
    inner = lit[3:-1]
    if lit.startswith("=C'") or lit.startswith("&C'"):
        return len(inner)
    if lit.startswith("=X'") or lit.startswith("&X'"):
        return max(1, (len(inner) + 1) // 2)
    return 3

def get_literal_object(lit):
    inner = lit[3:-1]
    if lit.startswith("=C'") or lit.startswith("&C'"):
        return "".join(f"{ord(c):02X}" for c in inner)
    if lit.startswith("=X'") or lit.startswith("&X'"):
        result = inner.upper()
        if len(result) % 2:
            result = "0" + result
        return result
    return ""



def run_pass1(infile):
    out_dir = os.path.dirname(os.path.abspath(infile))

    symtab       = {}
    pooltab      = {}
    intermediate = []

    blocks = {
        "DEFAULT":  {"num": 0, "lc": 0},
        "DEFAULTB": {"num": 1, "lc": 0},
        "POOL":     {"num": 2, "lc": 0},
        "CDATA":    {"num": 3, "lc": 0},
        "CBLKS":    {"num": 4, "lc": 0},
    }
    VALID_BLOCKS  = {"DEFAULT", "DEFAULTB", "CDATA", "CBLKS"}
    block_order   = ["DEFAULT"]
    pool_inserted = False
    current_block = "DEFAULT"
    lc            = 0
    lit_pool      = []
    pool_lc       = 0
    line_num      = 0

    
    def err(msg, lc_val, ln=0, detail=""):
        
        _babs = {}
        cursor = prog_start_guess()
        for bname in block_order:
            _babs[bname] = cursor
            cursor += blocks[bname]["lc"]
        _total = cursor - _babs.get(block_order[0], 0)
        error(msg, lc_val, ln, detail, out_dir,
              intermediate, symtab, pooltab, blocks, block_order, _babs, _total)

    def prog_start_guess():
        for _, lv, _, op, opnd in intermediate:
            if op == "START":
                return int(opnd, 16) if opnd else 0
        return 0

    with open(infile) as f:
        for raw_line in f:
            line_num += 1

            if ";" in raw_line:
                raw_line = raw_line.split(";")[0]

            parts = raw_line.strip().split(None, 2)
            if not parts:
                continue

            if len(parts) == 3:
                label, opcode, operand = parts
            elif len(parts) == 2:
                label, opcode = parts
                operand = None
            elif len(parts) == 1:
                label   = "-"
                opcode  = parts[0]
                operand = None
            else:
                continue

            current_lc = lc

            # ── Symbol table ──────────────────────────────────────────
            if label and label != "-" and opcode != "START":
                if label in symtab:
                    err("Duplicate Symbol", lc, line_num,
                        f"symbol '{label}' already defined")
                symtab[label] = (current_block, current_lc)

            # ── Collect =literals ─────────────────────────────────────
            if operand and operand.startswith("="):
                if operand not in lit_pool and operand not in pooltab:
                    lit_pool.append(operand)

            # ── Collect &pool-vars ────────────────────────────────────
            if operand and operand.startswith("&"):
                if operand not in pooltab:
                    if not pool_inserted:
                        pool_inserted = True
                        if "POOL" not in block_order:
                            block_order.append("POOL")
                    size = get_literal_size(operand)
                    obj  = get_literal_object(operand)
                    pooltab[operand] = {
                        "pool_offset":  pool_lc,
                        "block":        "POOL",
                        "block_offset": pool_lc,
                        "length":       size,
                        "obj":          obj
                    }
                    pool_lc += size
                    blocks["POOL"]["lc"] = pool_lc

            
            if opcode == "START":
                lc = int(operand, 16) if operand else 0
                blocks[current_block]["lc"] = lc
                intermediate.append((current_block, current_lc, label, opcode, operand))
                continue

            if opcode == "USE":
                block_name = operand if operand else "DEFAULT"
                if block_name not in VALID_BLOCKS:
                    err("Unidentified Block Name", lc, line_num,
                        f"unknown block '{block_name}'; valid: {', '.join(sorted(VALID_BLOCKS))}")
                blocks[current_block]["lc"] = lc
                current_block = block_name
                lc = blocks[current_block]["lc"]
                if block_name not in block_order:
                    block_order.append(block_name)
                intermediate.append((current_block, None, label, opcode, operand))
                continue

            if opcode in ("BASE", "NOBASE"):
                intermediate.append((current_block, None, label, opcode, operand))
                continue

            if opcode == "LTORG":
                intermediate.append((current_block, None, label, opcode, operand))
                for lit in lit_pool:
                    if lit not in pooltab:
                        size = get_literal_size(lit)
                        obj  = get_literal_object(lit)
                        pooltab[lit] = {
                            "pool_offset":  None,
                            "block":        current_block,
                            "block_offset": lc,
                            "length":       size,
                            "obj":          obj
                        }
                        intermediate.append((current_block, lc, lit, "_LIT_", lit))
                        lc += size
                        blocks[current_block]["lc"] = lc
                lit_pool.clear()
                continue

            if opcode == "WORD":
                intermediate.append((current_block, current_lc, label, opcode, operand))
                lc += 3
                blocks[current_block]["lc"] = lc
                continue

            if opcode == "RESW":
                n = int(operand) if operand else 0
                intermediate.append((current_block, current_lc, label, opcode, operand))
                lc += 3 * n
                blocks[current_block]["lc"] = lc
                continue

            if opcode == "RESB":
                n = int(operand) if operand else 0
                intermediate.append((current_block, current_lc, label, opcode, operand))
                lc += n
                blocks[current_block]["lc"] = lc
                continue

            if opcode == "BYTE":
                if operand and operand.startswith("C'"):
                    size = len(operand) - 3
                elif operand and operand.startswith("X'"):
                    size = max(1, (len(operand[2:-1]) + 1) // 2)
                else:
                    size = 1
                intermediate.append((current_block, current_lc, label, opcode, operand))
                lc += size
                blocks[current_block]["lc"] = lc
                continue

            if opcode == "EQU":
                intermediate.append((current_block, current_lc, label, opcode, operand))
                continue

            if opcode == "END":
                for lit in lit_pool:
                    if lit not in pooltab:
                        size = get_literal_size(lit)
                        obj  = get_literal_object(lit)
                        pooltab[lit] = {
                            "pool_offset":  None,
                            "block":        current_block,
                            "block_offset": lc,
                            "length":       size,
                            "obj":          obj
                        }
                        intermediate.append((current_block, lc, lit, "_LIT_", lit))
                        lc += size
                        blocks[current_block]["lc"] = lc
                lit_pool.clear()
                intermediate.append((current_block, lc, label, opcode, operand))
                continue

            
            base_op = opcode.lstrip("+")

            if base_op in ["FIX", "FLOAT", "HIO", "NORM", "SIO", "TIO"]:
                size = 1
            elif base_op in ["ADDR", "CLEAR", "COMPR", "DIVR", "MULR", "RMO",
                              "SHIFTL", "SHIFTR", "SUBR", "SVC", "TIXR"]:
                size = 2
            elif opcode.startswith("+"):
                size = 4
            else:
                size = 3

            intermediate.append((current_block, current_lc, label, opcode, operand))
            lc += size
            blocks[current_block]["lc"] = lc

    
    all_defined    = set(symtab.keys())
    skip_opcodes   = {"START", "END", "USE", "BASE", "NOBASE", "LTORG",
                      "WORD", "RESW", "RESB", "BYTE", "_LIT_", "EQU"}
    register_names = {"A", "X", "L", "B", "S", "T", "F", "PC", "SW"}

    for blk, lc_val, lbl, op, opnd in intermediate:
        if op in skip_opcodes or opnd is None:
            continue
        raw = opnd
        if raw.startswith(("#", "@")):
            raw = raw[1:]
        if raw.endswith(",X"):
            raw = raw[:-2]
        if raw.startswith(("=", "&")):
            continue
        if raw.replace("-", "").replace("+", "").isdigit():
            continue
        try:
            int(raw, 16)
            continue
        except ValueError:
            pass
        if raw in register_names:
            continue
        if raw and raw not in all_defined:
            err("Unidentified Symbol", lc_val if lc_val else 0, 0,
                f"symbol '{raw}' referenced but never defined")

    
    for bname in ["DEFAULT", "DEFAULTB", "CDATA", "CBLKS"]:
        if bname not in block_order and blocks[bname]["lc"] > 0:
            block_order.append(bname)

    prog_start = 0
    for _, lc_val, _, op, opnd in intermediate:
        if op == "START":
            prog_start = int(opnd, 16) if opnd else 0
            break

    block_abs_start = {}
    cursor = prog_start
    for bname in block_order:
        block_abs_start[bname] = cursor
        cursor += blocks[bname]["lc"]
    total_length = cursor - prog_start

    
    final_symtab = {}
    for sym, (blk, off) in symtab.items():
        final_symtab[sym] = block_abs_start.get(blk, 0) + off

    pool_start    = block_abs_start.get("POOL", cursor)
    final_pooltab = {}
    for lit, data in pooltab.items():
        if data["pool_offset"] is None:
            abs_addr = block_abs_start.get(data["block"], 0) + data["block_offset"]
        else:
            abs_addr = pool_start + data["pool_offset"]
        final_pooltab[lit] = {
            "addr":   abs_addr,
            "length": data["length"],
            "obj":    data["obj"]
        }

    
    _write_pass1_outputs(
        out_dir, intermediate, final_symtab, final_pooltab,
        blocks, block_order, block_abs_start, total_length
    )

    print(f"Pass 1 complete. Output written to: {out_dir}")

    
    intermediate_abs = []
    for blk, lc_val, lbl, op, opnd in intermediate:
        abs_lc = (block_abs_start.get(blk, 0) + lc_val) if lc_val is not None else None
        intermediate_abs.append((blk, abs_lc, lbl, op, opnd))

    return (final_symtab, final_pooltab, block_abs_start, blocks,
            block_order, intermediate_abs, prog_start, total_length)