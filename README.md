# SIC/XE Two-Pass Assembler

A complete implementation of a SIC/XE Two-Pass Assembler with support for core assembler features, error handling, literals, program blocks, and object code generation.

This project was developed as part of a Systems Programming course to demonstrate the internal workflow of modern assemblers including symbol resolution, address calculation, and object program generation.

---

## Features

### Pass 1
- Parses SIC/XE assembly programs
- Generates symbol table
- Handles literals and literal pools
- Supports program blocks
- Detects syntax and semantic errors
- Generates intermediate file
- Calculates addresses and location counters

### Pass 2
- Generates object code
- Supports SIC/XE instruction formats
- Handles addressing modes:
  - Immediate addressing
  - Indirect addressing
  - Indexed addressing
  - PC-relative addressing
  - Base-relative addressing
  - Extended format
- Generates:
  - Header record
  - Text records
  - Modification records
  - End record

### Web GUI
- Upload assembly source files
- Run assembler directly from browser
- Display generated outputs
- Show errors clearly
- Download output files

---

## Technologies Used

- Python
- Flask
- HTML/CSS/JavaScript

---

## Project Structure

```bash
project/
│
├── app.py                # Flask web application
├── pass1.py              # Pass 1 implementation
├── pass2.py              # Pass 2 implementation
├── opcode.json           # SIC/XE opcode table
├── templates/            # HTML templates
├── static/               # CSS and JS files
├── input/                # Input assembly programs
├── output/               # Generated assembler outputs
└── README.md
