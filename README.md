EQ Bank CSV → OFX Converter
A Windows desktop tool that converts EQ Bank transaction CSV exports into OFX files compatible with Microsoft Money Sunset Edition.

Features

Supports both EQ Bank Card and EQ Bank Savings Account CSV exports
Auto-detects the CSV format on file load
Select individual transactions to export using click, Ctrl+click, and Shift+click
Select All and Select None buttons for quick selection
Change +/- for All button to flip transaction amounts between positive and negative
Account Type dropdown (Pre-paid Bank Card / Chequing / Savings) — auto-set based on detected format, manually overridable
Currency dropdown defaulting to CAD (16 currencies supported)
Output OFX filename defaults to the same name and folder as the input CSV
Generates OFX 1.02 SGML format validated against Microsoft Money's strict parser


Supported CSV Formats
EQ Bank Card
ColumnExampleDate17 May 2026DescriptionUNIQLO CO.,LTD, Tokyo, JPNAmount"-$263.38"
EQ Bank Savings Account
ColumnExampleTransfer date2026-05-07DescriptionCard LoadAmount-$4000.00Balance$7004.77 (imported but discarded)

How to Use

Launch EQBank_OFX_Converter.exe
Click Browse… next to CSV File and select your EQ Bank export
Transactions load automatically, all selected by default
Enter your Account Number
Confirm the Account Type and Currency (auto-set but can be changed)
Adjust the output file path if needed
Select the transactions you want to export
Click Convert Now ▶
Import the resulting .ofx file into Microsoft Money via File → Import → OFX / QFX…


Building the .exe on Windows
You only need to do this once. It takes about 5–10 minutes.
Step 1 — Install Python

Go to python.org/downloads and download the latest Python 3 installer
Run the installer — check "Add Python to PATH" on the first screen before clicking Install Now

Step 2 — Install PyInstaller
Open a Command Prompt and run:
pip install pyinstaller
Step 3 — Build the .exe
Place eqbank_converter.py in a folder (e.g. C:\EQConverter), then in Command Prompt:
cd C:\EQConverter
pyinstaller --onefile --windowed --name "EQBank_OFX_Converter" eqbank_converter.py
Step 4 — Find your .exe
The finished executable will be at:
C:\EQConverter\dist\EQBank_OFX_Converter.exe
You can copy this file anywhere — it runs on any Windows PC without Python installed.

Note: Windows Defender or antivirus software may warn about a self-built .exe. Click More info → Run anyway or add an exception. This is normal for unsigned executables.


Requirements

Windows 10 or 11
Python 3.8+ (only needed to build the .exe, not to run it)
No third-party Python libraries — uses only the Python standard library (tkinter, csv, os, datetime)


OFX Output Details

Format: OFX 1.02 SGML (compatible with Microsoft Money Sunset Edition)
Transaction types auto-detected: DEBIT for negative amounts, CREDIT for positive
Account types written to OFX: CHECKING (Pre-paid Bank Card or Chequing), SAVINGS (Savings)
Transactions exported in chronological order (oldest first)


Notes

EQ Bank CSV exports are in reverse chronological order; the converter automatically reverses them so the oldest transaction appears first in the list and in the output file
The Balance column in the Savings Account CSV is discarded; <LEDGERBAL> is set to 0.00 in the OFX output, consistent with how other banks (e.g. TD) export OFX files
The <DTSERVER> timestamp in the OFX header reflects the time of conversion and will differ between exports — this is expected and harmless


License
MIT License — free to use, modify, and distribute.
