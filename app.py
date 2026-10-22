"""Gestore Gift Card Bambu Lab - app desktop (Tkinter)."""
from __future__ import annotations

import csv
import json
import os
import sys
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import calcoli as C

NOME_APP = "Gestore Gift Card Bambu Lab"
STATI = ["Disponibile", "Venduta", "Usata"]
NOMI_TAGLI = [t["nome"] for t in C.TAGLI]


def cartella_dati() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    p = Path(base) / "BambuGiftCard"
    p.mkdir(parents=True, exist_ok=True)
    return p


FILE_DATI = cartella_dati() / "dati.json"


def num(testo: str, predefinito: float = 0.0) -> float:
    try:
        return float(str(testo).strip().replace("€", "").replace("$", "").replace(",", "."))
    except ValueError:
        return predefinito


def eur(v: float) -> str:
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def intero(v: int) -> str:
    return f"{v:,}".replace(",", ".")


class Archivio:
    def __init__(self, percorso: Path):
        self.percorso = percorso
        self.impostazioni = dict(C.IMPOSTAZIONI_PREDEFINITE)
        self.card: list[dict] = []
        self.carica()

    def carica(self):
        if not self.percorso.exists():
            return
        try:
            dati = json.loads(self.percorso.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            messagebox.showwarning(NOME_APP, "File dati illeggibile: verranno usati i valori predefiniti.")
            return
        for k in self.impostazioni:
            if k in dati.get("impostazioni", {}):
                self.impostazioni[k] = dati["impostazioni"][k]
        self.card = dati.get("card", [])

    def salva(self):
        dati = {"impostazioni": self.impostazioni, "card": self.card}
        tmp = self.percorso.with_suffix(".tmp")
        tmp.write_text(json.dumps(dati, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.percorso)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(NOME_APP)
        self.geometry("980x740")
        self.minsize(860, 640)
        self.db = Archivio(FILE_DATI)

        stile = ttk.Style(self)
        if "vista" in stile.theme_names():
            stile.theme_use("vista")
        stile.configure("Titolo.TLabel", font=("Segoe UI", 11, "bold"))
        stile.configure("Grande.TLabel", font=("Segoe UI", 13, "bold"))
        stile.configure("Treeview", rowheight=26)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)
        self._scheda_calcolatore()
        self._scheda_inventario()
        self.protocol("WM_DELETE_WINDOW", self.chiudi)

    # ------------------------------------------------------------------ Calcolatore
    def _scheda_calcolatore(self):
        f = ttk.Frame(self.nb, padding=12)
        self.nb.add(f, text="Calcolatore gift card")

        alto = ttk.Frame(f)
        alto.pack(fill="x")

        inp = ttk.LabelFrame(alto, text="Oggetto da comprare su Bambu Lab", padding=10)
        inp.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.v_prezzo = tk.StringVar()
        ttk.Label(inp, text="Prezzo dell'oggetto (€)").grid(row=0, column=0, sticky="w")
        e = ttk.Entry(inp, textvariable=self.v_prezzo, font=("Segoe UI", 12), width=14)
        e.grid(row=0, column=1, sticky="w", padx=8)
        e.focus_set()
        self.lbl_card = ttk.Label(inp, text="", style="Grande.TLabel")
        self.lbl_card.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.lbl_dettagli = ttk.Label(inp, text="", justify="left")
        self.lbl_dettagli.grid(row=2, column=0, columnspan=2, sticky="w")

        par = ttk.LabelFrame(alto, text="Conversione punti in soldi", padding=10)
        par.pack(side="left", fill="both")
        self.v_imp = {}
        for i, (k, et) in enumerate([("valore_punto_usd", "Valore di 1 punto (USD)"),
                                     ("cambio_usd_eur", "Cambio: 1 USD = ? EUR")]):
            self.v_imp[k] = tk.StringVar(value=str(self.db.impostazioni[k]))
            ttk.Label(par, text=et).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(par, textvariable=self.v_imp[k], width=10).grid(row=i, column=1, sticky="w", padx=8, pady=2)
            self.v_imp[k].trace_add("write", lambda *_: self._imp_cambiate())
        self.lbl_minimo = ttk.Label(par, text="", justify="left", wraplength=300)
        self.lbl_minimo.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        ttk.Label(f, text="A che prezzo vendere le gift card da 40 €", style="Titolo.TLabel")\
            .pack(anchor="w", pady=(14, 4))
        colonne = [("prezzo", "Vendo ogni card a", 140), ("sconto", "Sconto", 80),
                   ("incasso", "Incassi in totale", 140), ("soldi", "Convertendo i punti", 150),
                   ("guadagno", "Guadagno in più", 140), ("conviene", "Conviene?", 90)]
        self.tab = ttk.Treeview(f, columns=[c[0] for c in colonne], show="headings",
                                height=len(C.PREZZI_VENDITA_40))
        for k, et, w in colonne:
            self.tab.heading(k, text=et)
            self.tab.column(k, width=w, anchor="center")
        self.tab.tag_configure("si", background="#e3f4e8")
        self.tab.tag_configure("no", background="#fbe4e2")
        self.tab.pack(fill="x")
        ttk.Label(f, foreground="#666", wraplength=880, justify="left", text=(
            "«Convertendo i punti» è quanto otterresti cambiando direttamente in soldi gli stessi punti "
            "usati per riscattare le card. «Guadagno in più» è quanto ci guadagni vendendo le card invece.")
                  ).pack(anchor="w", pady=(6, 0))

        self.v_prezzo.trace_add("write", lambda *_: self.aggiorna_calcolo())
        self.aggiorna_calcolo()

    def _imp_cambiate(self):
        for k, v in self.v_imp.items():
            x = num(v.get(), -1)
            if x > 0:
                self.db.impostazioni[k] = x
        self.aggiorna_calcolo()

    def _combinazione(self) -> C.Combinazione:
        testo = self.v_prezzo.get().strip()
        if not testo or num(testo) <= 0:
            return C.card_necessarie(C.TAGLI[0]["valore_eur"])
        return C.card_necessarie(num(testo))

    def aggiorna_calcolo(self):
        imp = self.db.impostazioni
        c = self._combinazione()
        vuoto = not self.v_prezzo.get().strip()
        self.lbl_card.configure(text=("Esempio con 1 card da 40 €" if vuoto else
                                      f"Ti servono {c.n_card} gift card da 40 €"))
        righe = [f"Valore gift card: {eur(c.valore)}", f"Punti necessari: {intero(c.punti)}"]
        if not vuoto:
            righe.append(f"Avanzo sulla gift card: {eur(c.avanzo)}" if c.avanzo else "Copertura esatta, nessun avanzo")
        self.lbl_dettagli.configure(text="\n".join(righe))
        pmin = C.prezzo_minimo_40(imp)
        self.lbl_minimo.configure(text=(
            f"524 punti convertiti in soldi = {eur(pmin)}.\n"
            f"Vendere una card da 40 € conviene sopra {eur(pmin)}."))

        self.tab.delete(*self.tab.get_children())
        for r in C.tabella_vendita(c, imp):
            self.tab.insert("", "end", tags=("si" if r.conviene else "no",), values=(
                eur(r.prezzo), f"{r.sconto_perc:.1f}%", eur(r.incasso), eur(r.soldi_punti),
                ("+" if r.guadagno >= 0 else "") + eur(r.guadagno), "Sì" if r.conviene else "No"))

    # ------------------------------------------------------------------ Inventario
    COLONNE_INV = [("taglio", "Taglio", 150), ("codice", "Codice", 280), ("stato", "Stato", 120),
                   ("acquirente", "Acquirente", 240)]

    def _scheda_inventario(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text="Inventario gift card")

        barra = ttk.Frame(f)
        barra.pack(fill="x")
        ttk.Button(barra, text="+ Aggiungi gift card", command=self._aggiungi_riga).pack(side="left")
        ttk.Button(barra, text="Incolla codici", command=self._incolla_codici).pack(side="left", padx=6)
        ttk.Button(barra, text="Elimina selezionata", command=self._elimina_card).pack(side="left", padx=6)
        ttk.Button(barra, text="Esporta CSV", command=self._esporta_csv).pack(side="left", padx=6)
        ttk.Button(barra, text="Importa CSV", command=self._importa_csv).pack(side="left", padx=6)
        self.v_filtro = tk.StringVar(value="Tutte")
        cb = ttk.Combobox(barra, textvariable=self.v_filtro, values=["Tutte"] + STATI, state="readonly", width=12)
        cb.pack(side="right")
        cb.bind("<<ComboboxSelected>>", lambda e: self.aggiorna_inventario())
        ttk.Label(barra, text="Mostra:").pack(side="right", padx=6)

        ttk.Label(f, foreground="#666", wraplength=900, justify="left", text=(
            "Clicca su una cella per modificarla: le modifiche si salvano da sole. "
            "Invio conferma e passa alla riga sotto, Esc annulla. "
            "«Incolla codici» crea una riga per ogni codice copiato.")).pack(anchor="w", pady=(8, 4))

        cont = ttk.Frame(f)
        cont.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(cont, columns=[c[0] for c in self.COLONNE_INV], show="headings",
                                 selectmode="browse")
        for k, et, w in self.COLONNE_INV:
            self.tree.heading(k, text=et)
            self.tree.column(k, width=w, anchor="center" if k in ("taglio", "stato") else "w")
        self.tree.tag_configure("Venduta", foreground="#1b7f3b")
        self.tree.tag_configure("Usata", foreground="#888")
        sb = ttk.Scrollbar(cont, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<ButtonRelease-1>", self._click_cella)
        self.tree.bind("<Return>", lambda e: self._modifica_cella(self.tree.focus(), "codice"))
        self.tree.bind("<Delete>", lambda e: self._elimina_card())

        self.lbl_totali = ttk.Label(f, text="", style="Titolo.TLabel")
        self.lbl_totali.pack(anchor="w", pady=(6, 0))
        self._editor: tk.Widget | None = None
        self.aggiorna_inventario()

    def _nuova_card(self, codice: str = "") -> dict:
        return {"id": uuid.uuid4().hex, "taglio": NOMI_TAGLI[0], "codice": codice,
                "stato": "Disponibile", "acquirente": ""}

    def _card(self, iid: str) -> dict | None:
        return next((c for c in self.db.card if c["id"] == iid), None)

    def _valori_riga(self, c: dict) -> tuple:
        return tuple(c.get(k, "") for k, _, _ in self.COLONNE_INV)

    def aggiorna_inventario(self):
        self._chiudi_editor(salva=True)
        self.tree.delete(*self.tree.get_children())
        filtro = self.v_filtro.get()
        for c in self.db.card:
            if filtro == "Tutte" or c.get("stato") == filtro:
                self.tree.insert("", "end", iid=c["id"], values=self._valori_riga(c), tags=(c.get("stato", ""),))
        self._aggiorna_totali()

    def _aggiorna_totali(self):
        conteggi = {s: 0 for s in STATI}
        valori = {t["nome"]: t["valore_eur"] for t in C.TAGLI}
        valore_disp = 0.0
        for c in self.db.card:
            conteggi[c.get("stato", "Disponibile")] = conteggi.get(c.get("stato"), 0) + 1
            if c.get("stato") == "Disponibile":
                valore_disp += valori.get(c.get("taglio"), 0)
        self.lbl_totali.configure(text=(
            f"Disponibili: {conteggi['Disponibile']} ({eur(valore_disp)})   ·   "
            f"Vendute: {conteggi['Venduta']}   ·   Usate: {conteggi['Usata']}   ·   Totale: {len(self.db.card)}"))

    def _click_cella(self, evento):
        if self.tree.identify_region(evento.x, evento.y) != "cell":
            return
        iid = self.tree.identify_row(evento.y)
        col = self.tree.identify_column(evento.x)
        if iid and col:
            self._modifica_cella(iid, self.COLONNE_INV[int(col[1:]) - 1][0])

    def _modifica_cella(self, iid: str, campo: str):
        self._chiudi_editor(salva=True)
        c = self._card(iid)
        if not c or not self.tree.exists(iid):
            return
        self.tree.see(iid)
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.update_idletasks()
        box = self.tree.bbox(iid, campo)
        if not box:
            return
        x, y, w, h = box
        var = tk.StringVar(value=c.get(campo, ""))
        if campo in ("taglio", "stato"):
            ed = ttk.Combobox(self.tree, textvariable=var, state="readonly",
                              values=NOMI_TAGLI if campo == "taglio" else STATI)
            ed.bind("<<ComboboxSelected>>", lambda e: self._chiudi_editor(salva=True))
        else:
            ed = ttk.Entry(self.tree, textvariable=var)
            ed.select_range(0, "end")
        ed.place(x=x, y=y, width=w, height=h)
        ed.focus_set()
        ed.bind("<Return>", lambda e: self._conferma_e_scendi())
        ed.bind("<KP_Enter>", lambda e: self._conferma_e_scendi())
        ed.bind("<Escape>", lambda e: self._chiudi_editor(salva=False))
        ed.bind("<FocusOut>", lambda e: self.after_idle(lambda: self._chiudi_editor(salva=True, solo=ed)))
        self._editor = ed
        self._editor_info = (iid, campo, var)

    def _chiudi_editor(self, salva: bool, solo: tk.Widget | None = None):
        ed = self._editor
        if ed is None or (solo is not None and solo is not ed):
            return
        if solo is not None and self.focus_get() is not None and str(self.focus_get()).startswith(str(ed)):
            return  # il focus è nella tendina della combobox
        self._editor = None
        iid, campo, var = self._editor_info
        if salva:
            c = self._card(iid)
            nuovo = var.get().strip()
            if c is not None and c.get(campo, "") != nuovo:
                c[campo] = nuovo
                self.db.salva()
                if self.tree.exists(iid):
                    self.tree.item(iid, values=self._valori_riga(c), tags=(c.get("stato", ""),))
                self._aggiorna_totali()
        else:
            # Esc su una riga appena creata e ancora vuota: la toglie
            c = self._card(iid)
            if c is not None and campo == "codice" and not c.get("codice") and not c.get("acquirente"):
                self.db.card.remove(c)
                self.db.salva()
                if self.tree.exists(iid):
                    self.tree.delete(iid)
                self._aggiorna_totali()
        ed.destroy()
        self.tree.focus_set()

    def _conferma_e_scendi(self):
        iid, campo, _ = self._editor_info
        self._chiudi_editor(salva=True)
        succ = self.tree.next(iid)
        if not succ and campo == "codice":
            succ = self._aggiungi_riga(modifica=False)
        if succ:
            self._modifica_cella(succ, campo)

    def _aggiungi_riga(self, modifica: bool = True) -> str:
        self._chiudi_editor(salva=True)
        c = self._nuova_card()
        self.db.card.append(c)
        self.db.salva()
        if self.v_filtro.get() not in ("Tutte", "Disponibile"):
            self.v_filtro.set("Tutte")
            self.aggiorna_inventario()
        else:
            self.tree.insert("", "end", iid=c["id"], values=self._valori_riga(c), tags=(c["stato"],))
            self._aggiorna_totali()
        if modifica:
            self._modifica_cella(c["id"], "codice")
        return c["id"]

    def _incolla_codici(self):
        try:
            testo = self.clipboard_get()
        except tk.TclError:
            testo = ""
        codici = [r.strip() for r in testo.splitlines() if r.strip()]
        if not codici:
            messagebox.showinfo(NOME_APP, "Copia prima i codici (uno per riga), poi premi «Incolla codici».")
            return
        esistenti = {c.get("codice") for c in self.db.card}
        nuovi = [k for k in codici if k not in esistenti]
        for k in nuovi:
            self.db.card.append(self._nuova_card(k))
        self.db.salva()
        self.aggiorna_inventario()
        doppi = len(codici) - len(nuovi)
        messagebox.showinfo(NOME_APP, f"Aggiunte {len(nuovi)} gift card da 40 €."
                            + (f" {doppi} codici erano già presenti." if doppi else ""))

    def _elimina_card(self):
        self._chiudi_editor(salva=True)
        sel = self.tree.selection()
        if not sel or not messagebox.askyesno(NOME_APP, "Eliminare la gift card selezionata?"):
            return
        self.db.card = [c for c in self.db.card if c["id"] != sel[0]]
        self.db.salva()
        self.aggiorna_inventario()

    def _esporta_csv(self):
        self._chiudi_editor(salva=True)
        percorso = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                                initialfile="gift_card_bambu.csv")
        if not percorso:
            return
        with open(percorso, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=["taglio", "codice", "stato", "acquirente"],
                               delimiter=";", extrasaction="ignore")
            w.writeheader()
            w.writerows(self.db.card)
        messagebox.showinfo(NOME_APP, f"Esportate {len(self.db.card)} gift card.")

    def _importa_csv(self):
        """Importa il file esportato dall'iPhone (o da un altro PC): aggiorna le card con lo
        stesso codice e aggiunge quelle nuove."""
        self._chiudi_editor(salva=True)
        percorso = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("Tutti i file", "*.*")])
        if not percorso:
            return
        try:
            with open(percorso, newline="", encoding="utf-8-sig") as fh:
                testo = fh.read()
            sep = ";" if testo.splitlines()[0].count(";") >= testo.splitlines()[0].count(",") else ","
            righe = list(csv.DictReader(testo.splitlines(), delimiter=sep))
        except (OSError, UnicodeDecodeError, IndexError, csv.Error):
            messagebox.showwarning(NOME_APP, "File non valido: usa il file esportato dall'app.")
            return
        righe = [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in righe]
        if righe and "codice" not in righe[0]:
            messagebox.showwarning(NOME_APP, "Nel file manca la colonna «codice».")
            return
        per_codice = {c.get("codice"): c for c in self.db.card if c.get("codice")}
        nuove = aggiornate = 0
        for r in righe:
            codice = r.get("codice", "")
            if not codice:
                continue
            stato = next((s for s in STATI if s.lower() == r.get("stato", "").lower()), "Disponibile")
            dati = {"taglio": NOMI_TAGLI[1] if "200" in r.get("taglio", "") else NOMI_TAGLI[0],
                    "stato": stato, "acquirente": r.get("acquirente", "")}
            c = per_codice.get(codice)
            if c is None:
                c = self._nuova_card(codice) | dati
                self.db.card.append(c)
                per_codice[codice] = c
                nuove += 1
            elif any(c.get(k, "") != v for k, v in dati.items()):
                c.update(dati)
                aggiornate += 1
        self.db.salva()
        self.aggiorna_inventario()
        messagebox.showinfo(NOME_APP, f"Importazione fatta: {nuove} nuove, {aggiornate} aggiornate.")

    def chiudi(self):
        try:
            self._chiudi_editor(salva=True)
            self.db.salva()
        finally:
            self.destroy()


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    App().mainloop()
