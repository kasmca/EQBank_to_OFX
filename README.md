# EQ Bank CSV to OFX Converter

A Windows desktop tool that converts EQ Bank transaction CSV exports into OFX files compatible with Microsoft Money Sunset Edition. Supports both EQ Bank Card and EQ Bank Savings Account CSV exports. The format is auto-detected on file load.

## Features

- Auto-detects EQ Bank Card vs Savings Account CSV format
- Select individual transactions using click, Ctrl+click, and Shift+click
- Select All and Select None buttons for quick selection
- Change +/- for All button to flip transaction amounts between positive and negative
- Account Type dropdown (Pre-paid Bank Card, Chequing, Savings) auto-set based on detected format but can be overridden
- Currency dropdown defaulting to CAD with 16 currencies supported
- Output OFX filename defaults to the same name and folder as the input CSV

## How to Use

1. Launch EQBank_OFX_Converter.exe
2. Click Browse next to CSV File and select your EQ Bank export
3. Transactions load automatically with all rows selected by default
4. Enter your Account Number
5. Confirm the Account Type and Currency
6. Adjust the output file path if needed
7. Select the transactions you want to export
8. Click Convert Now
9. Import the resulting .ofx file into Microsoft Money via File > Import > OFX / QFX

## How to Build the .exe on Windows

You only need to do this once.

**Step 1 - Install Python**

Go to python.org/downloads and download the latest Python 3 installer. Run it and make sure to check "Add Python to PATH" on the first screen before clicking Install Now.

**Step 2 - Install PyInstaller**

Open a Command Prompt and run:

`pip install pyinstaller`

**Step 3 - Build the .exe**

Place eqbank_converter.py in a folder such as C:\EQConverter, then in Command Prompt run:

`cd C:\EQConverter`

`pyinstaller --onefile --windowed --name "EQBank_OFX_Converter" eqbank_converter.py`

**Step 4 - Find your .exe**

The finished executable will be at C:\EQConverter\dist\EQBank_OFX_Converter.exe. You can copy this file anywhere and it will run on any Windows PC without Python installed.

Note: Windows Defender or antivirus software may warn about a self-built .exe. Click More info then Run anyway, or add an exception. This is normal for unsigned executables.

## License

MIT License - free to use, modify, and distribute.
