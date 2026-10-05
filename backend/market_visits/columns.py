"""Fixed Market Visit product columns (Availability Y/N + Facing qty)."""

from typing import TypedDict


class ColumnDef(TypedDict):
    code: str
    group: str
    label: str


MARKET_VISIT_COLUMNS: list[ColumnDef] = [
    {"code": "washout_lemon_1000", "group": "WASH OUT", "label": "LEMON 1000 ML"},
    {"code": "washout_ocean_1000", "group": "WASH OUT", "label": "OCEAN 1000 ML"},
    {"code": "washout_floral_1000", "group": "WASH OUT", "label": "FLORAL 1000 ML"},
    {"code": "rhino_bottle_750", "group": "RHINO", "label": "BOTTLE 750 ML"},
    {"code": "rhino_bottle_500", "group": "RHINO", "label": "BOTTLE 500 ML"},
    {"code": "rhino_bottle_250", "group": "RHINO", "label": "BOTTLE 250 ML"},
    {"code": "fabrito_bottle_1000", "group": "FABRITO", "label": "BOTTLE 1000 ML"},
    {"code": "fabrito_pouch_1000", "group": "FABRITO", "label": "POUCH 1000 ML"},
    {"code": "brighten_bottle_1000", "group": "BRIGHTEN", "label": "BOTTLE 1000 ML"},
    {"code": "brighten_pouch_1000", "group": "BRIGHTEN", "label": "POUCH 1000 ML"},
    {"code": "powerwash_bottle_500", "group": "POWER WASH", "label": "BOTTLE 500 ML"},
    {"code": "powerwash_pouch_1000", "group": "POWER WASH", "label": "POUCH 1000 ML"},
    {"code": "degreaser_bottle_750", "group": "DEGREASER", "label": "BOTTLE 750 ML"},
    {"code": "titan_jar_500", "group": "TITAN", "label": "JAR 500 G"},
    {"code": "titan_jar_1250", "group": "TITAN", "label": "JAR 1.25 KG"},
]

COLUMN_CODES = [c["code"] for c in MARKET_VISIT_COLUMNS]


def empty_availability() -> dict:
    return {code: "" for code in COLUMN_CODES}


def empty_facing() -> dict:
    return {code: None for code in COLUMN_CODES}


def grouped_columns() -> list[dict]:
    groups: list[dict] = []
    current = None
    for col in MARKET_VISIT_COLUMNS:
        if current is None or current["group"] != col["group"]:
            current = {"group": col["group"], "columns": []}
            groups.append(current)
        current["columns"].append({"code": col["code"], "label": col["label"]})
    return groups
