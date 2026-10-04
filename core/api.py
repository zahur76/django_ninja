from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from .models import Character, Faction
from .schemas import CharacterIn, CharacterOut, CharacterPatch, FactionIn, FactionOut

router = Router()


# ---------- Factions ----------

@router.get("/factions", response=list[FactionOut], tags=["Factions"])
def list_factions(request):
    return Faction.objects.all()


@router.get("/factions/{faction_id}", response=FactionOut, tags=["Factions"])
def get_faction(request, faction_id: int):
    return get_object_or_404(Faction, id=faction_id)


@router.post("/factions", response={201: FactionOut}, tags=["Factions"])
def create_faction(request, payload: FactionIn):
    if Faction.objects.filter(name=payload.name).exists():
        raise HttpError(409, f"Faction '{payload.name}' already exists")
    faction = Faction.objects.create(**payload.dict())
    return 201, faction


@router.put("/factions/{faction_id}", response=FactionOut, tags=["Factions"])
def update_faction(request, faction_id: int, payload: FactionIn):
    faction = get_object_or_404(Faction, id=faction_id)
    if Faction.objects.filter(name=payload.name).exclude(id=faction_id).exists():
        raise HttpError(409, f"Faction '{payload.name}' already exists")
    for attr, value in payload.dict().items():
        setattr(faction, attr, value)
    faction.save()
    return faction


@router.delete("/factions/{faction_id}", response={204: None}, tags=["Factions"])
def delete_faction(request, faction_id: int):
    faction = get_object_or_404(Faction, id=faction_id)
    faction.delete()
    return 204, None


# ---------- Characters ----------

def check_faction_exists(faction_id):
    if faction_id is not None and not Faction.objects.filter(id=faction_id).exists():
        raise HttpError(400, f"Faction with id {faction_id} does not exist")


@router.get("/characters", response=list[CharacterOut], tags=["Characters"])
def list_characters(request):
    return Character.objects.select_related("faction")


@router.get("/characters/{character_id}", response=CharacterOut, tags=["Characters"])
def get_character(request, character_id: int):
    return get_object_or_404(Character.objects.select_related("faction"), id=character_id)


@router.post("/characters", response={201: CharacterOut}, tags=["Characters"])
def create_character(request, payload: CharacterIn):
    check_faction_exists(payload.faction_id)
    character = Character.objects.create(**payload.dict())
    return 201, character


@router.put("/characters/{character_id}", response=CharacterOut, tags=["Characters"])
def update_character(request, character_id: int, payload: CharacterIn):
    character = get_object_or_404(Character, id=character_id)
    check_faction_exists(payload.faction_id)
    for attr, value in payload.dict().items():
        setattr(character, attr, value)
    character.save()
    return character


@router.patch("/characters/{character_id}", response=CharacterOut, tags=["Characters"])
def patch_character(request, character_id: int, payload: CharacterPatch):
    character = get_object_or_404(Character, id=character_id)
    data = payload.dict(exclude_unset=True)
    for field in ("name", "birth_date", "gender"):
        if field in data and data[field] is None:
            raise HttpError(400, f"'{field}' cannot be null")
    if "faction_id" in data:
        check_faction_exists(data["faction_id"])
    for attr, value in data.items():
        setattr(character, attr, value)
    character.save()
    return character


@router.delete("/characters/{character_id}", response={204: None}, tags=["Characters"])
def delete_character(request, character_id: int):
    character = get_object_or_404(Character, id=character_id)
    character.delete()
    return 204, None
