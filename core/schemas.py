from ninja import Schema

from .models import Character


# ---------- Faction ----------

class FactionIn(Schema):
    name: str


class FactionOut(Schema):
    id: int
    name: str


# ---------- Character ----------

class CharacterIn(Schema):
    name: str
    faction_id: int | None = None
    birth_date: str = ""
    gender: Character.Gender


class CharacterPatch(Schema):
    name: str | None = None
    faction_id: int | None = None
    birth_date: str | None = None
    gender: Character.Gender | None = None


class CharacterOut(Schema):
    id: int
    name: str
    faction: FactionOut | None
    birth_date: str
    gender: Character.Gender
