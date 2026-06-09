"""Typo / misspelling normalizer.

Small models miss few-shot pattern matches when the user's word doesn't appear
verbatim. Hand-maintained map of common domain-specific misspellings; no
generic edit-distance fallback (would rewrite legitimate words too often).

Pure function. No I/O.
"""

from __future__ import annotations

import re

MISSPELLINGS: dict[str, str] = {
    # competitor
    "compitior": "competitor", "compitiors": "competitors",
    "competitior": "competitor", "competitiors": "competitors",
    "competator": "competitor", "competators": "competitors",
    "competetor": "competitor", "competetors": "competitors",
    "compeitor": "competitor", "compeitors": "competitors",
    "competiter": "competitor", "competiters": "competitors",
    # revenue
    "revanue": "revenue", "revunue": "revenue", "revenu": "revenue",
    "revenues": "revenue", "revinue": "revenue",
    # category
    "categary": "category", "categery": "category", "catagory": "category",
    "categeries": "categories", "catagories": "categories", "categorys": "categories",
    # brand
    "brnad": "brand", "brnads": "brands", "bran": "brand", "brands": "brands",
    # product
    "prodcut": "product", "prodcuts": "products",
    "proudct": "product", "proudcts": "products",
    "prodct": "product", "prodcts": "products",
    "porduct": "product", "porducts": "products",
    "produt": "product", "produts": "products",
    # market
    "markett": "market", "marekt": "market", "marekts": "markets", "markets": "markets",
    # cannabis
    "canabis": "cannabis", "cannibis": "cannabis", "canibus": "cannabis",
    "cannabbis": "cannabis",
    # category-product terms
    "flwer": "flower", "flowr": "flower", "flwoer": "flower", "flowwer": "flower",
    "preroll": "pre-roll", "prerolls": "pre-rolls",
    "prerol": "pre-roll", "prerols": "pre-rolls",
    "edibel": "edible", "edibels": "edibles", "edibe": "edible",
    "concntrate": "concentrate", "concentraite": "concentrate",
    "consentrate": "concentrate", "consentrates": "concentrates",
    "vape": "vape", "vapes": "vapes",
    "cartrige": "cartridge", "cartriges": "cartridges", "cart": "cartridge",
    # price / quantity
    "prce": "price", "pric": "price", "prises": "prices",
    "qty": "quantity", "quanity": "quantity", "quantitiy": "quantity",
    # greetings
    "helo": "hello", "helllo": "hello", "helooo": "hello",
    "hii": "hi", "hiii": "hi", "hry": "hey", "heyy": "hey", "heyyy": "hey",
    "yoo": "yo", "sup": "hi",
    "thanx": "thanks", "thnx": "thanks", "thx": "thanks", "ty": "thanks",
    "thnks": "thanks", "thakns": "thanks", "thaks": "thanks",
    # sales / order
    "sels": "sales", "saless": "sales", "sale": "sales",
    "oders": "orders", "oder": "order",
    "invntory": "inventory", "invnetory": "inventory", "invetory": "inventory",
    # partners / stores / dispensary
    "partener": "partner", "parteners": "partners",
    "parnter": "partner", "parnters": "partners",
    "patner": "partner", "patners": "partners",
    "dispencary": "dispensary", "dispensry": "dispensary",
    "dispensaries": "dispensaries", "dispencaries": "dispensaries",
    "stoer": "store", "stoers": "stores",
}

_TOKEN_RX = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def normalize_question(question: str) -> str:
    def repl(m: re.Match[str]) -> str:
        return MISSPELLINGS.get(m.group(0).lower(), m.group(0))
    return _TOKEN_RX.sub(repl, question)
