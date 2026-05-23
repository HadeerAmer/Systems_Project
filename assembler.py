import sys
import os
from pass1 import run_pass1
from pass2 import run_pass2

def main():
    print("Running assembler...")
    if len(sys.argv) != 2:
        print("Usage: python assembler.py in.txt")
        sys.exit(1)

    infile  = sys.argv[1]
    out_dir = os.path.dirname(os.path.abspath(infile))

    print("Running Pass 1...")
    final_symtab, final_pooltab, block_abs_start, blocks, block_order, intermediate, prog_start, total_length = run_pass1(infile)

    print("Running Pass 2...")
    run_pass2(intermediate, final_symtab, final_pooltab, infile)

    
    err_path = os.path.join(out_dir, "error.txt")
    with open(err_path, "w") as f:
        f.write("")

    print("Assembler run complete. Check output files.")

if __name__ == "__main__":
    main()