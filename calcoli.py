"""Logica di calcolo per le gift card Bambu Lab (nessuna dipendenza da interfaccia)."""
from __future__ import annotations

import math
from dataclasses import dataclass

TAGLI = [
    {"nome": "Gift card 40 €", "valore_eur": 40.0, "punti": 524},
    {"nome": "Gift card 200 €", "valore_eur": 200.0, "punti": 2620},
]

# Valori predefiniti, modificabili dall'app.
IMPOSTAZIONI_PREDEFINITE = {
    "valore_punto_usd": 0.066,  # quanto vale 1 punto se convertito direttamente in soldi (USD)
    "cambio_usd_eur": 0.86,     # 1 USD = x EUR
}

PREZZI_VENDITA_40 = list(range(30, 41))


def punti_a_eur(punti: float, valore_punto_usd: float, cambio_usd_eur: float) -> float:
    return punti * valore_punto_usd * cambio_usd_eur


@dataclass
class Combinazione:
    n_card: int     # card da 40 € necessarie
    valore: float   # € totali di gift card
    punti: int      # punti necessari per riscattarle
    avanzo: float   # € di gift card che restano dopo l'acquisto


def card_necessarie(prezzo: float) -> Combinazione:
    """Quante card da 40 € servono per coprire il prezzo."""
    t = TAGLI[0]
    n = max(0, math.ceil(round(max(0.0, prezzo) / t["valore_eur"], 9)))
    valore = n * t["valore_eur"]
    return Combinazione(n, valore, n * t["punti"], valore - max(0.0, prezzo))


@dataclass
class RigaVendita:
    prezzo: float         # prezzo di vendita di una card da 40 €
    sconto_perc: float
    incasso: float        # totale incassato vendendo tutte le card
    soldi_punti: float    # quanto avresti convertendo gli stessi punti in soldi
    guadagno: float       # incasso - soldi_punti
    conviene: bool


def tabella_vendita(comb: Combinazione, imp: dict, prezzi=PREZZI_VENDITA_40) -> list[RigaVendita]:
    soldi = punti_a_eur(comb.punti, imp["valore_punto_usd"], imp["cambio_usd_eur"])
    righe = []
    for p in prezzi:
        incasso = comb.n_card * p
        righe.append(RigaVendita(p, (1 - p / TAGLI[0]["valore_eur"]) * 100, incasso, soldi,
                                 incasso - soldi, incasso > soldi))
    return righe


def prezzo_minimo_40(imp: dict) -> float:
    """Prezzo di una card da 40 € sotto cui conviene convertire i punti in soldi."""
    return punti_a_eur(TAGLI[0]["punti"], imp["valore_punto_usd"], imp["cambio_usd_eur"])
