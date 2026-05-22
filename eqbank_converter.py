"""
EQ Bank CSV to OFX Converter
Supports EQ Bank Card and EQ Bank Savings Account CSV exports.
Auto-detects format based on column headers.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
from datetime import datetime


# ── Supported currencies ──────────────────────────────────────────────────────
CURRENCIES = [
    "CAD", "USD", "EUR", "GBP", "JPY", "AUD", "CHF", "CNY",
    "HKD", "NZD", "SEK", "NOK", "DKK", "MXN", "SGD", "INR",
]

# ── Account type dropdown options: (display label, OFX value) ─────────────────
ACCOUNT_TYPES = [
    ("Pre-paid Bank Card", "CHECKING"),
    ("Chequing",           "CHECKING"),
    ("Savings",            "SAVINGS"),
]
ACCT_LABELS = [a[0] for a in ACCOUNT_TYPES]

def acct_label_to_ofx(label: str) -> str:
    for lbl, ofx in ACCOUNT_TYPES:
        if lbl == label:
            return ofx
    return "CHECKING"

# ── Format identifiers ────────────────────────────────────────────────────────
FMT_CARD    = "EQ Bank Card"
FMT_SAVINGS = "EQ Bank Savings"


# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_amount(raw: str) -> float:
    """Strip quotes, dollar sign, commas; return float."""
    cleaned = raw.strip().strip('"').replace("$", "").replace(",", "").strip()
    return float(cleaned)

def format_amount(value: float) -> str:
    return f"{value:.2f}"

def ofx_trntype(value: float) -> str:
    return "CREDIT" if value >= 0 else "DEBIT"

def parse_date_card(raw: str) -> str:
    """'17 May 2026' → '20260517120000'"""
    dt = datetime.strptime(raw.strip(), "%d %b %Y")
    return dt.strftime("%Y%m%d120000")

def parse_date_savings(raw: str) -> str:
    """'2026-05-07' → '20260507120000'"""
    dt = datetime.strptime(raw.strip(), "%Y-%m-%d")
    return dt.strftime("%Y%m%d120000")

def make_fitid(row_index: int, date_str: str) -> str:
    return f"{date_str[:8]}-{row_index:05d}"

def detect_format(fieldnames: list) -> str:
    """Return FMT_SAVINGS or FMT_CARD based on CSV column headers."""
    fields = [f.strip().lower() for f in (fieldnames or [])]
    if "transfer date" in fields:
        return FMT_SAVINGS
    return FMT_CARD


# ── OFX builder ───────────────────────────────────────────────────────────────
def build_ofx(transactions: list, account_number: str, currency: str,
              acct_type_ofx: str) -> str:
    """
    Build a complete OFX 1.02 SGML file string.
    acct_type_ofx: 'CHECKING' or 'SAVINGS'
    """
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    if transactions:
        dates    = [t["date_ofx"] for t in transactions]
        dt_start = min(dates)
        dt_end   = max(dates)
    else:
        dt_start = dt_end = now

    trn_lines = []
    for t in transactions:
        trn_lines.append("<STMTTRN>")
        trn_lines.append(f"<TRNTYPE>{ofx_trntype(t['amount'])}")
        trn_lines.append(f"<DTPOSTED>{t['date_ofx']}")
        trn_lines.append(f"<TRNAMT>{format_amount(t['amount'])}")
        trn_lines.append(f"<FITID>{t['fitid']}")
        trn_lines.append(f"<NAME>{t['description']}")
        trn_lines.append("</STMTTRN>")
    trn_block = "\n".join(trn_lines)

    ofx = (
        "OFXHEADER:100\n"
        "DATA:OFXSGML\n"
        "VERSION:102\n"
        "SECURITY:NONE\n"
        "ENCODING:USASCII\n"
        "CHARSET:1252\n"
        "COMPRESSION:NONE\n"
        "OLDFILEUID:NONE\n"
        "NEWFILEUID:NONE\n"
        "\n"
        "<OFX>\n"
        "<SIGNONMSGSRSV1>\n"
        "<SONRS>\n"
        "<STATUS>\n"
        "<CODE>0\n"
        "<SEVERITY>INFO\n"
        "</STATUS>\n"
        f"<DTSERVER>{now}\n"
        "<LANGUAGE>ENG\n"
        "</SONRS>\n"
        "</SIGNONMSGSRSV1>\n"
        "<BANKMSGSRSV1>\n"
        "<STMTTRNRS>\n"
        "<TRNUID>1001\n"
        "<STATUS>\n"
        "<CODE>0\n"
        "<SEVERITY>INFO\n"
        "</STATUS>\n"
        "<STMTRS>\n"
        f"<CURDEF>{currency}\n"
        "<BANKACCTFROM>\n"
        "<BANKID>EQBANK\n"
        f"<ACCTID>{account_number}\n"
        f"<ACCTTYPE>{acct_type_ofx}\n"
        "</BANKACCTFROM>\n"
        "<BANKTRANLIST>\n"
        f"<DTSTART>{dt_start}\n"
        f"<DTEND>{dt_end}\n"
        f"{trn_block}\n"
        "</BANKTRANLIST>\n"
        "<LEDGERBAL>\n"
        "<BALAMT>0.00\n"
        f"<DTASOF>{dt_end}\n"
        "</LEDGERBAL>\n"
        "</STMTRS>\n"
        "</STMTTRNRS>\n"
        "</BANKMSGSRSV1>\n"
        "</OFX>\n"
    )
    return ofx


# ── Main GUI ──────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EQ Bank CSV → OFX Converter")
        self.resizable(True, True)
        self.minsize(880, 580)

        self.csv_path       = tk.StringVar()
        self.ofx_path       = tk.StringVar()
        self.account_number = tk.StringVar()
        self.currency       = tk.StringVar(value="CAD")
        self.acct_type_var  = tk.StringVar(value=ACCT_LABELS[0])
        self.format_var     = tk.StringVar(value="—")

        self.rows           = []
        self.amount_floats  = []

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        ctrl = ttk.LabelFrame(self, text="Settings", padding=8)
        ctrl.pack(fill="x", padx=10, pady=(10, 4))

        # Row 0 – CSV input
        ttk.Label(ctrl, text="CSV File:").grid(row=0, column=0, sticky="e", **pad)
        ttk.Entry(ctrl, textvariable=self.csv_path, width=52).grid(
            row=0, column=1, columnspan=3, sticky="ew", **pad)
        ttk.Button(ctrl, text="Browse…", command=self._browse_csv).grid(row=0, column=4, **pad)

        # Row 1 – OFX output
        ttk.Label(ctrl, text="Output OFX File:").grid(row=1, column=0, sticky="e", **pad)
        ttk.Entry(ctrl, textvariable=self.ofx_path, width=52).grid(
            row=1, column=1, columnspan=3, sticky="ew", **pad)
        ttk.Button(ctrl, text="Browse…", command=self._browse_ofx).grid(row=1, column=4, **pad)

        # Row 2 – Account number + Currency
        ttk.Label(ctrl, text="Account Number:").grid(row=2, column=0, sticky="e", **pad)
        ttk.Entry(ctrl, textvariable=self.account_number, width=22).grid(
            row=2, column=1, sticky="ew", **pad)
        ttk.Label(ctrl, text="Currency:").grid(row=2, column=2, sticky="e", **pad)
        ttk.Combobox(ctrl, textvariable=self.currency, values=CURRENCIES,
                     width=8, state="readonly").grid(row=2, column=3, sticky="w", **pad)

        # Row 3 – Account type + Detected format
        ttk.Label(ctrl, text="Account Type:").grid(row=3, column=0, sticky="e", **pad)
        ttk.Combobox(ctrl, textvariable=self.acct_type_var, values=ACCT_LABELS,
                     width=20, state="readonly").grid(row=3, column=1, sticky="w", **pad)
        ttk.Label(ctrl, text="Detected Format:").grid(row=3, column=2, sticky="e", **pad)
        ttk.Label(ctrl, textvariable=self.format_var,
                  foreground="navy", font=("Segoe UI", 9, "italic")).grid(
                      row=3, column=3, sticky="w", **pad)

        ctrl.columnconfigure(1, weight=1)

        # Transaction list
        list_frame = ttk.LabelFrame(
            self, text="Transactions  (Ctrl+click or Shift+click to multi-select)", padding=8)
        list_frame.pack(fill="both", expand=True, padx=10, pady=4)

        cols = ("date", "description", "amount")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="extended")
        self.tree.heading("date",        text="Date")
        self.tree.heading("description", text="Description")
        self.tree.heading("amount",      text="Amount")
        self.tree.column("date",        width=105, anchor="center")
        self.tree.column("description", width=460, anchor="w")
        self.tree.column("amount",      width=115, anchor="e")

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Button bar
        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill="x", padx=10, pady=(4, 10))

        ttk.Button(btn_bar, text="Select All",  command=self._select_all).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Select None", command=self._select_none).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Change +/- for All",
                   command=self._toggle_amounts).pack(side="left", padx=16)

        self.status_label = ttk.Label(btn_bar, text="Load a CSV file to begin.", foreground="gray")
        self.status_label.pack(side="left", padx=10)

        ttk.Button(btn_bar, text="Convert Now ▶", command=self._convert,
                   style="Accent.TButton").pack(side="right", padx=4)

        style = ttk.Style(self)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    # ── File dialogs ──────────────────────────────────────────────────────────
    def _browse_csv(self):
        path = filedialog.askopenfilename(
            title="Select EQ Bank CSV export",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.csv_path.set(path)
            base = os.path.splitext(path)[0]
            self.ofx_path.set(base + ".ofx")
            self._load_csv(path)

    def _browse_ofx(self):
        path = filedialog.asksaveasfilename(
            title="Save OFX file as",
            defaultextension=".ofx",
            filetypes=[("OFX files", "*.ofx"), ("All files", "*.*")]
        )
        if path:
            self.ofx_path.set(path)

    # ── CSV loading ───────────────────────────────────────────────────────────
    def _load_csv(self, path: str):
        self.rows.clear()
        self.amount_floats.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.format_var.set("—")

        errors = []
        fmt = FMT_CARD

        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or []
                fmt = detect_format(fieldnames)
                raw_rows = list(reversed(list(reader)))

            # Auto-set account type dropdown based on detected format
            if fmt == FMT_SAVINGS:
                self.acct_type_var.set("Savings")
            else:
                self.acct_type_var.set("Pre-paid Bank Card")

            self.format_var.set(fmt)

            for i, row in enumerate(raw_rows):
                if fmt == FMT_SAVINGS:
                    date_raw = row.get("Transfer date", "").strip()
                    # Balance column is discarded
                else:
                    date_raw = row.get("Date", "").strip()

                desc_raw = row.get("Description", "").strip().strip('"')
                amt_raw  = row.get("Amount", "").strip()

                try:
                    amt_float = parse_amount(amt_raw)
                    if fmt == FMT_SAVINGS:
                        date_ofx = parse_date_savings(date_raw)
                    else:
                        date_ofx = parse_date_card(date_raw)
                except Exception as e:
                    errors.append(f"Row {i+2}: {e}")
                    continue

                self.rows.append({
                    "date_raw":     date_raw,
                    "date_ofx":     date_ofx,
                    "description":  desc_raw,
                    "amount_float": amt_float,
                    "fitid":        make_fitid(i, date_ofx),
                })
                self.amount_floats.append(amt_float)
                self.tree.insert("", "end", values=(date_raw, desc_raw, f"{amt_float:,.2f}"))

        except Exception as e:
            messagebox.showerror("Error loading CSV", str(e))
            return

        self._select_all()

        msg = f"{len(self.rows)} transactions loaded  ({fmt})."
        if errors:
            msg += f"  ({len(errors)} rows skipped)"
        self.status_label.config(text=msg, foreground="black")

        if errors:
            messagebox.showwarning("Some rows skipped", "\n".join(errors[:10]))

    # ── Selection helpers ─────────────────────────────────────────────────────
    def _select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def _select_none(self):
        self.tree.selection_remove(self.tree.get_children())

    # ── Toggle +/- for all rows ───────────────────────────────────────────────
    def _toggle_amounts(self):
        if not self.rows:
            return
        children = self.tree.get_children()
        for i, item in enumerate(children):
            self.amount_floats[i]        = -self.amount_floats[i]
            self.rows[i]["amount_float"] = self.amount_floats[i]
            vals = self.tree.item(item, "values")
            self.tree.item(item, values=(vals[0], vals[1], f"{self.amount_floats[i]:,.2f}"))
        self.status_label.config(text="Amounts toggled (+/−).", foreground="blue")

    # ── Convert ───────────────────────────────────────────────────────────────
    def _convert(self):
        selected_ids = self.tree.selection()
        if not selected_ids:
            messagebox.showwarning("Nothing selected", "Please select at least one transaction.")
            return

        account = self.account_number.get().strip()
        if not account:
            messagebox.showwarning("Account number missing", "Please enter your EQ Bank account number.")
            return

        ofx_file = self.ofx_path.get().strip()
        if not ofx_file:
            messagebox.showwarning("Output file missing", "Please specify an output OFX file path.")
            return

        currency     = self.currency.get()
        acct_type_ofx = acct_label_to_ofx(self.acct_type_var.get())
        all_children = list(self.tree.get_children())

        transactions = []
        for item in selected_ids:
            idx = all_children.index(item)
            r   = self.rows[idx]
            transactions.append({
                "date_ofx":    r["date_ofx"],
                "description": r["description"],
                "amount":      r["amount_float"],
                "fitid":       r["fitid"],
            })

        # Sort oldest-first
        transactions.sort(key=lambda t: t["date_ofx"])

        try:
            ofx_content = build_ofx(transactions, account, currency, acct_type_ofx)
            with open(ofx_file, "w", encoding="ascii", errors="replace") as f:
                f.write(ofx_content)
        except Exception as e:
            messagebox.showerror("Error writing OFX", str(e))
            return

        messagebox.showinfo(
            "Done!",
            f"Successfully exported {len(transactions)} transaction(s) to:\n\n{ofx_file}"
        )
        self.status_label.config(
            text=f"✔ Exported {len(transactions)} transaction(s) → {os.path.basename(ofx_file)}",
            foreground="green"
        )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
