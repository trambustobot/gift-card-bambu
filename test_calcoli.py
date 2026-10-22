import unittest
import calcoli as C

IMP = {"valore_punto_usd": 0.066, "cambio_usd_eur": 0.86}


class TestCalcoli(unittest.TestCase):
    def test_punti_tagli(self):
        self.assertEqual([t["punti"] for t in C.TAGLI], [524, 2620])

    def test_card_necessarie_esatto(self):
        c = C.card_necessarie(120)
        self.assertEqual((c.n_card, c.avanzo, c.punti), (3, 0, 3 * 524))

    def test_card_necessarie_arrotonda_per_eccesso(self):
        c = C.card_necessarie(85)
        self.assertEqual((c.n_card, c.avanzo), (3, 35))

    def test_tabella_vendita(self):
        c = C.card_necessarie(80)
        righe = C.tabella_vendita(c, IMP)
        self.assertEqual([r.prezzo for r in righe], list(range(30, 41)))
        r30 = righe[0]
        self.assertAlmostEqual(r30.sconto_perc, 25)
        self.assertAlmostEqual(r30.incasso, 60)
        self.assertAlmostEqual(r30.soldi_punti, 1048 * 0.066 * 0.86)
        self.assertAlmostEqual(r30.guadagno, 60 - 1048 * 0.066 * 0.86)

    def test_prezzo_minimo(self):
        self.assertAlmostEqual(C.prezzo_minimo_40(IMP), 524 * 0.066 * 0.86)


if __name__ == "__main__":
    unittest.main()
