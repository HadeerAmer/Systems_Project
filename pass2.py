import sys
import os


OPTAB = {
    "FIX": ("C4", 1), "FLOAT": ("C0", 1), "HIO": ("F4", 1),
    "NORM": ("C8", 1), "SIO": ("F0", 1), "TIO": ("F8", 1),

    "ADDR": ("90", 2), "CLEAR": ("B4", 2), "COMPR": ("A0", 2),
    "DIVR": ("9C", 2), "MULR": ("98", 2), "RMO": ("AC", 2),
    "SHIFTL": ("A4", 2), "SHIFTR": ("A8", 2), "SUBR": ("94", 2),
    "SVC": ("B0", 2), "TIXR": ("B8", 2),

    "ADD": ("18", 3), "ADDF": ("58", 3), "AND": ("40", 3),
    "COMP": ("28", 3), "COMPF": ("88", 3), "DIV": ("24", 3),
    "DIVF": ("64", 3), "J": ("3C", 3), "JEQ": ("30", 3),
    "JGT": ("34", 3), "JLT": ("38", 3), "JSUB": ("48", 3),
    "LDA": ("00", 3), "LDB": ("68", 3), "LDCH": ("50", 3),
    "LDF": ("70", 3), "LDL": ("08", 3), "LDS": ("6C", 3),
    "LDT": ("74", 3), "LDX": ("04", 3), "LPS": ("D0", 3),
    "MUL": ("20", 3), "MULF": ("60", 3), "OR": ("44", 3),
    "RD": ("D8", 3), "RSUB": ("4C", 3), "STA": ("0C", 3),
    "STB": ("78", 3), "STCH": ("54", 3), "STF": ("80", 3),
    "STI": ("D4", 3), "STL": ("14", 3), "STS": ("7C", 3),
    "STSW": ("E0", 3), "STT": ("84", 3), "STX": ("10", 3),
    "SUB": ("1C", 3), "SUBF": ("5C", 3), "TD": ("E4", 3),
    "TIX": ("2C", 3), "WD": ("DC", 3)
}

REGTAB = {"A": 0, "X": 1, "L": 2, "B": 3, "S": 4, "T": 5, "F": 6}

NO_CODE_OPCODES = {"START", "END", "USE", "BASE", "NOBASE",
                   "LTORG", "RESW", "RESB", "EQU"}

PASS2_FILES = ["out_pass2.txt", "HTME.txt"]



def error(msg, addr, out_dir=".", detail="", line_num=0):
    
    for fname in PASS2_FILES:
        with open(os.path.join(out_dir, fname), "w") as f:
            f.write("")

    
    err_path = os.path.join(out_dir, "error.txt")
    with open(err_path, "w") as f:
        f.write(f"Error : {msg}\n")
        f.write(f"PC    : {addr:04X}\n")
        if line_num:
            f.write(f"Line  : line {line_num}\n")
        if detail:
            f.write(f"Detail: {detail}\n")

    print(f"ERROR: {msg} at {addr:04X}")
    if line_num:
        print(f"       Line {line_num}")
    if detail:
        print(f"       {detail}")
    print(f"       See {err_path}")

    sys.exit(1)



def run_pass2(intermediate, symtab, pooltab, infile=None):

    if not intermediate:
        print("No intermediate file generated.")
        return

    if infile:
        out_dir = os.path.dirname(os.path.abspath(infile))
    else:
        out_dir = os.getcwd()

    print(f"Pass 2: writing output files to: {out_dir}")

    
    prog_name   = "PROG"
    start_addr  = 0
    end_operand = None

    for blk, abs_lc, label, opcode, operand in intermediate:
        if opcode == "START":
            start_addr = abs_lc if abs_lc is not None else 0
            if label and label != "-":
                prog_name = label[:6].upper()
            break

    for blk, abs_lc, label, opcode, operand in intermediate:
        if opcode == "END":
            end_operand = operand
            break

    
    prog_len = 0
    for blk, abs_lc, label, opcode, operand in intermediate:
        if abs_lc is None:
            continue
        base_op = opcode[1:] if opcode.startswith("+") else opcode
        if base_op in OPTAB:
            fmt  = OPTAB[base_op][1]
            size = 4 if opcode.startswith("+") else fmt
        elif opcode == "WORD":
            size = 3
        elif opcode == "BYTE":
            if operand and operand.startswith("C'"):
                size = len(operand[2:-1])
            elif operand and operand.startswith("X'"):
                size = max(1, (len(operand[2:-1]) + 1) // 2)
            else:
                size = 1
        elif opcode == "RESW":
            size = 3 * int(operand) if operand else 0
        elif opcode == "RESB":
            size = int(operand) if operand else 0
        elif opcode == "_LIT_":
            lit   = operand
            inner = lit[3:-1]
            if lit.startswith(("=C'", "&C'")):
                size = len(inner)
            elif lit.startswith(("=X'", "&X'")):
                size = max(1, (len(inner) + 1) // 2)
            else:
                size = 3
        else:
            size = 0
        end_of = abs_lc + size - start_addr
        if end_of > prog_len:
            prog_len = end_of

    
    object_code = []
    mod_records = []
    base_val    = None

    for line_num, (blk, addr, label, opcode, operand) in enumerate(intermediate, 1):

        code = ""

        
        if opcode == "_LIT_":
            lit   = operand
            inner = lit[3:-1]
            if lit.startswith(("=C'", "&C'")):
                code = "".join(f"{ord(c):02X}" for c in inner)
            elif lit.startswith(("=X'", "&X'")):
                code = inner.upper()
                if len(code) % 2:
                    code = "0" + code
            object_code.append((addr, label, "_LIT_", operand, code))
            continue

        
        if opcode == "BASE":
            if operand and operand in symtab:
                base_val = symtab[operand]
            object_code.append((addr, label, opcode, operand, ""))
            continue

        if opcode == "NOBASE":
            base_val = None
            object_code.append((addr, label, opcode, operand, ""))
            continue

        
        if opcode in NO_CODE_OPCODES:
            object_code.append((addr, label, opcode, operand, ""))
            continue

        
        is_extended = opcode.startswith("+")
        base_opcode = opcode[1:] if is_extended else opcode

        if base_opcode in OPTAB:
            op_hex, fmt = OPTAB[base_opcode]

            
            if fmt == 1:
                code = op_hex

           
            elif fmt == 2:
                regs = operand.split(",") if operand else []
                r1 = REGTAB.get(regs[0].strip(), 0) if len(regs) > 0 else 0
                r2 = REGTAB.get(regs[1].strip(), 0) if len(regs) > 1 else 0
                code = f"{op_hex}{r1:01X}{r2:01X}"

            
            elif fmt == 3:

                if base_opcode == "RSUB":
                    code = "4C0000"

                else:
                    n, i, x = 1, 1, 0
                    target = operand if operand else ""

                    if target.startswith("#"):
                        n, i = 0, 1
                        target = target[1:]
                    elif target.startswith("@"):
                        n, i = 1, 0
                        target = target[1:]

                    if target.endswith(",X"):
                        x = 1
                        target = target[:-2]

                    addr_val        = 0
                    is_pool_ref     = False
                    resolved_symbol = None

                    if target:
                        is_plain_num = False
                        try:
                            addr_val     = int(target)
                            is_plain_num = True
                        except ValueError:
                            try:
                                addr_val     = int(target, 16)
                                is_plain_num = True
                            except ValueError:
                                pass

                        if not is_plain_num:
                            if target in symtab:
                                addr_val        = symtab[target]
                                resolved_symbol = target
                            elif target in pooltab:
                                addr_val        = pooltab[target]["addr"]
                                is_pool_ref     = True
                                resolved_symbol = target
                            else:
                                error("Undefined Symbol", addr if addr else 0,
                                      out_dir,
                                      f"symbol '{target}' referenced but never defined",
                                      line_num)

                    op_int = (int(op_hex, 16) & 0xFC) | ((n << 1) | i)

                    if is_extended:
                        byte2 = (x << 7) | (1 << 4) | ((addr_val >> 16) & 0xF)
                        byte3 = (addr_val >> 8) & 0xFF
                        byte4 =  addr_val        & 0xFF
                        code  = f"{op_int:02X}{byte2:02X}{byte3:02X}{byte4:02X}"

                        is_imm_num = (n == 0 and i == 1 and resolved_symbol is None)
                        if resolved_symbol and not is_imm_num:
                            mod_records.append((addr + 1, 5, prog_name))

                    else:
                        pc_next       = addr + 3
                        is_imm_number = (n == 0 and i == 1 and resolved_symbol is None)

                        if is_imm_number:
                            disp = addr_val & 0xFFF
                            b, p = 0, 0
                        else:
                            pc_disp = addr_val - pc_next
                            if -2048 <= pc_disp <= 2047:
                                disp = pc_disp & 0xFFF
                                b, p = 0, 1
                            elif base_val is not None:
                                base_disp = addr_val - base_val
                                if 0 <= base_disp <= 4095:
                                    disp = base_disp & 0xFFF
                                    b, p = 1, 0
                                else:
                                    tag = "POOLVAR error" if is_pool_ref else "Addressing error"
                                    error(tag, addr if addr else 0, out_dir,
                                          f"'{target}' out of PC and Base range", line_num)
                            else:
                                tag = "POOLVAR error" if is_pool_ref else "Addressing error"
                                error(tag, addr if addr else 0, out_dir,
                                      f"'{target}' out of PC range and no BASE set", line_num)

                        byte2 = (x << 7) | (b << 6) | (p << 5) | ((disp >> 8) & 0xF)
                        byte3 =  disp & 0xFF
                        code  = f"{op_int:02X}{byte2:02X}{byte3:02X}"

        
        elif opcode == "WORD":
            code = f"{int(operand):06X}"

        
        elif opcode == "BYTE":
            if operand and operand.startswith("C'"):
                code = "".join(f"{ord(c):02X}" for c in operand[2:-1])
            elif operand and operand.startswith("X'"):
                raw  = operand[2:-1]
                code = ("0" + raw if len(raw) % 2 else raw).upper()

        object_code.append((addr, label, opcode, operand, code))

    
    p2_path = os.path.join(out_dir, "out_pass2.txt")
    with open(p2_path, "w") as f:
        f.write("Location counter  Symbol   Instructions  Reference   Obj. code\n")
        f.write("----------------  -------  ------------  ----------  --------------\n")
        for addr, label, opcode, operand, code in object_code:
            lc_str  = f"{addr:04X}" if addr is not None else ""
            sym_str = label if (label and label != "-") else ""
            op_str  = "LITERAL" if opcode == "_LIT_" else (opcode or "")
            ref_str = operand or ""
            obj_str = code if code else "No object code"
            f.write(f"{lc_str:<18} {sym_str:<9} {op_str:<13} {ref_str:<12} {obj_str}\n")
    print(f"  Written: {p2_path}")

    
    e_addr = start_addr
    if end_operand and end_operand in symtab:
        e_addr = symtab[end_operand]

    MAX_T_BYTES = 30

    def flush_t(f, t_start, t_hex):
        if t_hex and t_start is not None:
            f.write(f"T^{t_start:06X}^{len(t_hex)//2:02X}^{t_hex}\n")

    htme_path = os.path.join(out_dir, "HTME.txt")
    with open(htme_path, "w") as f:

        f.write(f"H^{prog_name:<6}^{start_addr:06X}^{prog_len:06X}\n")

        t_start       = None
        t_hex         = ""
        expected_next = None

        for addr, label, opcode, operand, code in object_code:
            if not code or addr is None or opcode in ("RESW", "RESB"):
                flush_t(f, t_start, t_hex)
                t_start, t_hex, expected_next = None, "", None
                continue

            code_bytes = len(code) // 2
            gap        = (expected_next is not None and addr != expected_next)
            overflow   = (len(t_hex) // 2 + code_bytes > MAX_T_BYTES)

            if gap or overflow:
                flush_t(f, t_start, t_hex)
                t_start, t_hex = None, ""

            if t_start is None:
                t_start = addr

            t_hex        += code
            expected_next = addr + code_bytes

        flush_t(f, t_start, t_hex)

        for mod_addr, mod_len, pname in mod_records:
            f.write(f"M^{mod_addr:06X}^{mod_len:02X}^+{pname}\n")

        f.write(f"E^{e_addr:06X}\n")

    print(f"  Written: {htme_path}")