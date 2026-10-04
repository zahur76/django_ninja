# Star Wars API (Django Ninja demo)

A demo REST API built with [Django](https://www.djangoproject.com/) and [Django Ninja](https://django-ninja.dev/).

It has two database models:

1. **Faction**: `name`
2. **Character**: `name`, `faction` (foreign key to Faction), `birth_date`, `gender`

---

## Setup steps

Each step taken to build this project is recorded below, in order.

### Step 1: Create a virtual environment

A virtual environment keeps this project's packages separate from the global Python install.

```powershell
python -m venv .venv
```

Activate it:

```powershell
# PowerShell
.venv\Scripts\Activate.ps1

# Git Bash
source .venv/Scripts/activate
```

Check it's active. The path should point inside `.venv`:

```powershell
python -c "import sys; print(sys.prefix)"
```

> If PowerShell blocks the activation script, run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Step 2: Install Django Ninja

With the venv active:

```powershell
pip install django-ninja
```

You only need to install `django-ninja`. It depends on Django and Pydantic, so pip installs them automatically.

Check what got installed:

```powershell
pip list
```

Main packages installed:

| Package      | Version | Purpose                                  |
|--------------|---------|------------------------------------------|
| django-ninja | 1.7.1   | The API framework                        |
| Django       | 6.1.1   | Web framework (pulled in by Ninja)       |
| pydantic     | 2.13.5  | Request/response schemas (used by Ninja) |

> `python-dotenv` is installed later, in Step 15.

### Step 3: Create the Django project

```powershell
django-admin startproject starwars_api .
```

The trailing `.` creates the project in the current folder, so `manage.py` sits next to `README.md` and `.venv` instead of inside an extra nested folder.

Resulting structure:

```
django_ninja/
├── .venv/
├── manage.py            # command-line tool for this project
├── README.md
└── starwars_api/        # project config package
    ├── __init__.py
    ├── asgi.py          # ASGI entry point
    ├── settings.py      # project settings
    ├── urls.py          # root URL routes (the Ninja API will be hooked in here)
    └── wsgi.py          # WSGI entry point
```

Verify the project is set up correctly:

```powershell
python manage.py check
```

Expected output: `System check identified no issues (0 silenced).`

### Step 4: Create the `core` app

A Django *project* is the overall config; an *app* is a module holding models and logic. The `core` app will hold both the `Character` and `Faction` models.

```powershell
python manage.py startapp core
```

This creates:

```
core/
├── __init__.py
├── admin.py         # register models with the Django admin
├── apps.py          # app config
├── migrations/      # database migration files
│   └── __init__.py
├── models.py        # Character and Faction models go here
├── tests.py
└── views.py         # not used; Ninja endpoints will go in api.py instead
```

Register the app in `starwars_api/settings.py` so Django loads it:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  # added
]
```

Verify:

```powershell
python manage.py check
```

### Step 5: Define the models

In `core/models.py`:

```python
from django.db import models


class Faction(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Character(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    name = models.CharField(max_length=100)
    faction = models.ForeignKey(
        Faction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="characters",
    )
    # Star Wars dates use the BBY/ABY calendar (e.g. "19BBY"), so this is text, not a DateField.
    birth_date = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices)

    def __str__(self):
        return self.name
```

| Model     | Field        | Type                 | Notes                                                       |
|-----------|--------------|----------------------|-------------------------------------------------------------|
| Faction   | `name`       | CharField(100)       | `unique=True`, so no two factions share a name              |
| Character | `name`       | CharField(100)       |                                                             |
| Character | `faction`    | ForeignKey → Faction | Optional. If the faction is deleted, it's set to `NULL`     |
| Character | `birth_date` | CharField(20)        | Text like `"19BBY"`, since Star Wars dates aren't real dates |
| Character | `gender`     | CharField(10)        | Required. One of `male`, `female`, `other`                  |

Design decisions:

- **`Faction` is defined first** because `Character` refers to it.
- **`on_delete=models.SET_NULL`**: deleting a faction keeps its characters and clears their `faction`. Requires `null=True`.
- **`Gender` uses `TextChoices`**: the database stores the value (`"male"`), the admin shows the label (`"Male"`), and code can use `Character.Gender.MALE` instead of a raw string. Any other value fails validation.
- **`related_name="characters"`**: lets you go from a faction to its members with `faction.characters.all()`.
- **`__str__`** shows the name in the Django admin and shell instead of `Faction object (1)`.

Verify:

```powershell
python manage.py check
```

> The database tables don't exist yet. That's the next step (migrations).

### Step 6: Make and apply migrations

Migrations are how Django turns model classes into database tables. It's a two-step process.

**6a. Generate the migration file** from the models:

```powershell
python manage.py makemigrations core
```

Output:

```
Migrations for 'core':
  core\migrations\0001_initial.py
    + Create model Faction
    + Create model Character
```

This writes `core/migrations/0001_initial.py`, a Python description of the tables. It doesn't touch the database yet. Django also adds an `id` primary key (`BigAutoField`) to each model automatically.

**6b. Apply migrations** to the database:

```powershell
python manage.py migrate
```

This creates `db.sqlite3` (SQLite is Django's default database). It also creates the tables for Django's built-in apps (`admin`, `auth`, `contenttypes`, `sessions`) along with `core`.

Tables created for our models:

| Table            | Columns                                                  |
|------------------|----------------------------------------------------------|
| `core_faction`   | `id`, `name`                                             |
| `core_character` | `id`, `name`, `birth_date`, `gender`, `faction_id`       |

Verify:

```powershell
python manage.py showmigrations core
```

Expected output: `[X] 0001_initial` (the `X` means it's applied).

> Whenever you change `models.py` later, run `makemigrations` and then `migrate` again.

### Step 7: Register the models in the Django admin

The Django admin is a built-in web UI for adding and editing data. Models only show up there once they're registered.

In `core/admin.py`:

```python
from django.contrib import admin

from .models import Character, Faction


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "faction", "birth_date", "gender"]
    list_filter = ["faction", "gender"]
    search_fields = ["name"]
```

| Option          | What it does                                          |
|-----------------|-------------------------------------------------------|
| `list_display`  | Columns shown in the list page                        |
| `list_filter`   | Sidebar filters (e.g. show only "female" or one faction) |
| `search_fields` | Adds a search box that searches by name               |

Verify:

```powershell
python manage.py check
```

To log in to the admin you need a superuser account. It prompts for a username, email and password:

```powershell
python manage.py createsuperuser
```

Then start the server and open http://127.0.0.1:8000/admin/:

```powershell
python manage.py runserver
```

### Step 8: Set up the Ninja API and Swagger docs

Django Ninja generates an OpenAPI schema and a Swagger UI page automatically. All it needs is a `NinjaAPI` instance hooked into the URLs.

**8a. Create the API**: new file `starwars_api/api.py`:

```python
from ninja import NinjaAPI

api = NinjaAPI(
    title="Star Wars API",
    version="1.0.0",
    description="Demo API for Star Wars characters and factions, built with Django Ninja.",
)


@api.get("/hello")
def hello(request):
    return {"message": "Hello there!"}
```

- `NinjaAPI(...)` is the main API object. `title`, `version` and `description` appear at the top of the Swagger page.
- `@api.get("/hello")` registers a GET endpoint. Ninja converts the returned dict to JSON. It's just a test endpoint and will be replaced by real ones later.

**8b. Hook it into the URLs**: `starwars_api/urls.py`:

```python
from django.contrib import admin
from django.urls import path

from .api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),  # added
]
```

Every Ninja endpoint is now served under `/api/`.

**8c. Try it**:

```powershell
python manage.py runserver
```

| URL                                         | What it is                                 |
|---------------------------------------------|--------------------------------------------|
| http://127.0.0.1:8000/api/docs              | Swagger UI: browse and test endpoints      |
| http://127.0.0.1:8000/api/openapi.json      | The raw OpenAPI schema                     |
| http://127.0.0.1:8000/api/hello             | Test endpoint → `{"message": "Hello there!"}` |

In Swagger, click **GET /api/hello**, then **Try it out**, then **Execute** to call it from the browser.

### Step 9: Create the Pydantic schemas

Schemas define the JSON shape the API **accepts** (input) and **returns** (output). Ninja uses them to:

- validate incoming request bodies (wrong type or missing field → automatic `422` error)
- convert Django model objects into JSON responses
- document the request/response formats in Swagger

`ninja.Schema` is a Pydantic `BaseModel` that can also read attributes from Django model objects.

New file `core/schemas.py`:

```python
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


class CharacterOut(Schema):
    id: int
    name: str
    faction: FactionOut | None
    birth_date: str
    gender: Character.Gender
```

Why separate **In** and **Out** schemas?

| | `...In` (request body) | `...Out` (response) |
|---|---|---|
| `id` | Not included. The database generates it | Included |
| Faction on a character | `faction_id`: just the number | `faction`: a nested object `{id, name}` |

Field notes:

- **`= None` / `= ""`** make a field optional. `name` and `gender` have no default, so they're required.
- **`faction_id`**: Django automatically gives every `ForeignKey` a `<name>_id` attribute, so `Character(faction_id=1)` works directly.
- **`gender: Character.Gender`** reuses the model's `TextChoices`, so the allowed values are defined in one place. Swagger shows them as a dropdown.
- **`faction: FactionOut | None`** nests one schema inside another. A character with no faction returns `null`.

Example output for a character:

```json
{
  "id": 1,
  "name": "Leia Organa",
  "faction": {"id": 1, "name": "Rebel Alliance"},
  "birth_date": "19BBY",
  "gender": "female"
}
```

Validation examples:

| Input                                   | Result                                              |
|-----------------------------------------|-----------------------------------------------------|
| `{"name": "R2-D2", "gender": "droid"}`  | Error: `Input should be 'male', 'female' or 'other'` |
| `{"gender": "male"}`                    | Error: `name: Field required`                       |

> The schemas aren't used by any endpoint yet. That's the next step.

### Step 10: Faction CRUD endpoints

CRUD means **C**reate, **R**ead, **U**pdate, **D**elete.

**10a. Create a router**: new file `core/api.py`.

A `Router` is a group of endpoints that belongs to one app. It gets attached to the main `NinjaAPI` afterwards. This keeps each app's endpoints in its own folder instead of piling them all into `starwars_api/api.py`.

```python
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from .models import Faction
from .schemas import FactionIn, FactionOut

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
```

How Ninja reads these functions:

| Piece                               | Meaning                                                                      |
|-------------------------------------|------------------------------------------------------------------------------|
| `@router.get / post / put / delete` | HTTP method + URL path                                                       |
| `{faction_id}` in path + `faction_id: int` | Path parameter. Ninja converts it to `int` (`/factions/abc` → `422`)  |
| `payload: FactionIn`                | Request body, validated against the schema (missing `name` → `422`)          |
| `response=FactionOut`               | Output is converted to this schema (model object → JSON)                     |
| `response=list[FactionOut]`         | Output is a list, so a QuerySet can be returned directly                     |
| `response={201: FactionOut}`        | Return `(status_code, data)` to send a status other than 200                 |
| `tags=["Factions"]`                 | Groups the endpoints under a "Factions" heading in Swagger                   |
| `request`                           | Required first argument (the Django `HttpRequest`) even if unused            |

Error handling:

- **`get_object_or_404`**: an unknown id returns `404` instead of crashing.
- **`HttpError(409, ...)`**: `name` is `unique=True`, so a duplicate name returns `409 Conflict` with a clear message instead of a database `IntegrityError` (`500`).

**10b. Attach the router to the main API**: `starwars_api/api.py`:

```python
from ninja import NinjaAPI

from core.api import router as core_router

api = NinjaAPI(
    title="Star Wars API",
    version="1.0.0",
    description="Demo API for Star Wars characters and factions, built with Django Ninja.",
)


@api.get("/hello")
def hello(request):
    return {"message": "Hello there!"}


api.add_router("/", core_router)  # added
```

`add_router("/", ...)` mounts the router's endpoints under `/api/`, so `/factions` becomes `/api/factions`. Without this line the endpoints are never registered and won't appear (see the note on `api.urls` in Step 8).

**10c. Endpoints**:

| Method | URL                       | Body        | Success                    | Errors                         |
|--------|---------------------------|-------------|----------------------------|--------------------------------|
| GET    | `/api/factions`           |             | `200` list of factions     |                                |
| GET    | `/api/factions/{id}`      |             | `200` one faction          | `404`                          |
| POST   | `/api/factions`           | `{"name"}`  | `201` created faction      | `409` duplicate, `422` invalid |
| PUT    | `/api/factions/{id}`      | `{"name"}`  | `200` updated faction      | `404`, `409`, `422`            |
| DELETE | `/api/factions/{id}`      |             | `204` no content           | `404`                          |

> Deleting a faction doesn't delete its characters. Their `faction` becomes `null` (`on_delete=SET_NULL`, Step 5).

**10d. Try it**: run `python manage.py runserver`, open http://127.0.0.1:8000/api/docs, and use **Try it out** under the **Factions** section. For example, POST `{"name": "Rebel Alliance"}`.

Tested responses:

```
POST   create Rebel Alliance       201  {"id": 1, "name": "Rebel Alliance"}
POST   duplicate name              409  {"detail": "Faction 'Rebel Alliance' already exists"}
POST   missing name                422  {"detail": [{"type": "missing", "loc": ["body", "payload", "name"], "msg": "Field required"}]}
GET    list                        200  [{"id": 1, "name": "Rebel Alliance"}, ...]
GET    not found                   404  {"detail": "Not Found: No Faction matches the given query."}
PUT    rename                      200  {"id": 1, "name": "Rebellion"}
DELETE                             204
```

### Step 11: Character CRUD endpoints

Added to the same router in `core/api.py`, below the faction endpoints. First update the imports at the top:

```python
from .models import Character, Faction
from .schemas import CharacterIn, CharacterOut, FactionIn, FactionOut
```

Then the endpoints:

```python
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


@router.delete("/characters/{character_id}", response={204: None}, tags=["Characters"])
def delete_character(request, character_id: int):
    character = get_object_or_404(Character, id=character_id)
    character.delete()
    return 204, None
```

These follow the same pattern as the faction endpoints (Step 10). What's new:

- **`check_faction_exists()`**: a `faction_id` that doesn't exist returns a clear `400` error before saving. Without it, the database would reject the foreign key and the API would return a `500`. `None` is allowed, meaning no faction.
- **`Character.objects.create(**payload.dict())`**: the payload dict is `{"name": ..., "faction_id": ..., "birth_date": ..., "gender": ...}`. These keys match the model's attributes, including the automatic `faction_id` from Step 9, so they can be passed directly.
- **`select_related("faction")`**: `CharacterOut` includes the nested faction. Without this, listing N characters runs 1 query for the characters plus 1 extra query per character to fetch its faction (the "N+1 problem"). `select_related` fetches everything in a single SQL `JOIN`. Tested: listing 7 characters takes **1 query**.
- **PUT needs every required field** (`name`, `gender`), even when changing only one. To update just some fields, a PATCH endpoint is needed (not added yet).

Endpoints:

| Method | URL                         | Body                                         | Success                    | Errors                                   |
|--------|-----------------------------|----------------------------------------------|----------------------------|------------------------------------------|
| GET    | `/api/characters`           |                                              | `200` list of characters   |                                          |
| GET    | `/api/characters/{id}`      |                                              | `200` one character        | `404`                                    |
| POST   | `/api/characters`           | `{"name", "faction_id"?, "birth_date"?, "gender"}` | `201` created character | `400` bad faction, `422` invalid         |
| PUT    | `/api/characters/{id}`      | same as POST                                 | `200` updated character    | `404`, `400`, `422`                      |
| DELETE | `/api/characters/{id}`      |                                              | `204` no content           | `404`                                    |

(`?` = optional)

Tested responses:

```
POST  Luke (with faction)            201  {"id": 1, "name": "Luke Skywalker", "faction": {"id": 1, "name": "Rebel Alliance"}, "birth_date": "19BBY", "gender": "male"}
POST  Han (no faction/birth_date)    201  {"id": 2, "name": "Han Solo", "faction": null, "birth_date": "", "gender": "male"}
POST  bad faction_id                 400  {"detail": "Faction with id 99999 does not exist"}
POST  bad gender                     422  {"detail": [{"type": "enum", "loc": ["body", "payload", "gender"], "msg": "Input should be 'male', 'female' or 'other'", ...}]}
GET   not found                      404  {"detail": "Not Found: No Character matches the given query."}
PUT   Luke -> Empire                 200  {"id": 1, ..., "faction": {"id": 2, "name": "Galactic Empire"}, ...}
PUT   missing gender                 422  {"detail": [{"type": "missing", "loc": ["body", "payload", "gender"], "msg": "Field required"}]}
DELETE faction Empire                204
GET   Luke after faction delete      200  {"id": 1, ..., "faction": null, ...}
```

The last two lines confirm `on_delete=SET_NULL`. Deleting a faction keeps its characters and sets their `faction` to `null`.

Try it in Swagger at http://127.0.0.1:8000/api/docs under the **Characters** section. Create a faction first, then use its `id` as `faction_id`.

### Step 12: PATCH endpoint for partial character updates

**PUT vs PATCH**:

| | PUT | PATCH |
|---|---|---|
| Meaning | Replace the whole object | Change only the fields you send |
| Body to change only the faction | `{"name": "Luke Skywalker", "faction_id": 2, "birth_date": "19BBY", "gender": "male"}` | `{"faction_id": 2}` |

**12a. Add a PATCH schema**: in `core/schemas.py`, between `CharacterIn` and `CharacterOut`:

```python
class CharacterPatch(Schema):
    name: str | None = None
    faction_id: int | None = None
    birth_date: str | None = None
    gender: Character.Gender | None = None
```

Every field has `= None`, so every field is optional and the client can send any combination, including just one.

**12b. Add the endpoint**: in `core/api.py`, add `CharacterPatch` to the schema import:

```python
from .schemas import CharacterIn, CharacterOut, CharacterPatch, FactionIn, FactionOut
```

Then add the endpoint below `update_character`:

```python
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
```

How it works:

- **`payload.dict(exclude_unset=True)`**: the key line. It returns only the fields the client actually sent. Without it, every missing field would be `None` and would overwrite existing data.

  | Body sent                 | `payload.dict()`                                                    | `payload.dict(exclude_unset=True)` |
  |---------------------------|---------------------------------------------------------------------|------------------------------------|
  | `{"name": "Darth Vader"}` | `{"name": "Darth Vader", "faction_id": None, "birth_date": None, "gender": None}` | `{"name": "Darth Vader"}` |

- **The null check**: since the schema fields are `X | None`, a client could explicitly send `{"name": null}`. But `name`, `birth_date` and `gender` can't be `NULL` in the database (Step 5), so this returns a clear `400` instead of a database error.
- **`faction_id` is different**: it *can* be null. Sending `{"faction_id": null}` removes the character from their faction.
- **`check_faction_exists`** runs only if `faction_id` was sent.

Endpoint:

| Method | URL                    | Body                       | Success                 | Errors                                    |
|--------|------------------------|----------------------------|-------------------------|-------------------------------------------|
| PATCH  | `/api/characters/{id}` | any subset of the fields   | `200` updated character | `404`, `400` null field / bad faction, `422` invalid |

Tested responses (starting from Anakin Skywalker, Rebel Alliance, 41BBY, male):

```
PATCH only faction_id     {"faction_id": 2}       200  {"id": 1, "name": "Anakin Skywalker", "faction": {"id": 2, "name": "Galactic Empire"}, "birth_date": "41BBY", "gender": "male"}
PATCH only name           {"name": "Darth Vader"} 200  {"id": 1, "name": "Darth Vader", "faction": {"id": 2, "name": "Galactic Empire"}, ...}
PATCH faction_id null     {"faction_id": null}    200  {"id": 1, "name": "Darth Vader", "faction": null, ...}
PATCH empty body          {}                      200  (nothing changed)
PATCH name null           {"name": null}          400  {"detail": "'name' cannot be null"}
PATCH bad faction_id      {"faction_id": 99999}   400  {"detail": "Faction with id 99999 does not exist"}
PATCH bad gender          {"gender": "droid"}     422  {"detail": [... "Input should be 'male', 'female' or 'other'" ...]}
PATCH not found                                   404  {"detail": "Not Found: No Character matches the given query."}
```

### Step 13: Seed the database with sample data

Sample data is loaded with a custom **management command**, a script you run with `python manage.py <name>` just like the built-in `migrate` or `runserver`. It can be run again at any time, for example after deleting `db.sqlite3` and re-running `migrate`.

**13a. Create the folder structure**: Django finds commands in `<app>/management/commands/`. Both folders need an empty `__init__.py`:

```
core/
└── management/
    ├── __init__.py
    └── commands/
        ├── __init__.py
        └── seed.py      # the file name becomes the command name: "seed"
```

**13b. Write the command**: `core/management/commands/seed.py`:

```python
from django.core.management.base import BaseCommand

from core.models import Character, Faction

FACTIONS = [
    "Rebel Alliance",
    "Galactic Empire",
    "Jedi Order",
    "Sith",
    "Galactic Republic",
]

# (name, faction name or None, birth_date, gender)
CHARACTERS = [
    # Rebel Alliance
    ("Luke Skywalker", "Rebel Alliance", "19BBY", "male"),
    ("Leia Organa", "Rebel Alliance", "19BBY", "female"),
    ("Han Solo", "Rebel Alliance", "32BBY", "male"),
    ("Chewbacca", "Rebel Alliance", "200BBY", "male"),
    ("Lando Calrissian", "Rebel Alliance", "31BBY", "male"),
    ("Mon Mothma", "Rebel Alliance", "48BBY", "female"),
    ("Wedge Antilles", "Rebel Alliance", "21BBY", "male"),
    ("R2-D2", "Rebel Alliance", "33BBY", "other"),
    ("C-3PO", "Rebel Alliance", "112BBY", "other"),
    # Galactic Empire
    ("Darth Vader", "Galactic Empire", "41BBY", "male"),
    ("Grand Moff Tarkin", "Galactic Empire", "64BBY", "male"),
    # Jedi Order
    ("Obi-Wan Kenobi", "Jedi Order", "57BBY", "male"),
    ("Yoda", "Jedi Order", "896BBY", "male"),
    ("Mace Windu", "Jedi Order", "72BBY", "male"),
    ("Qui-Gon Jinn", "Jedi Order", "92BBY", "male"),
    ("Ahsoka Tano", "Jedi Order", "36BBY", "female"),
    # Sith
    ("Darth Sidious", "Sith", "84BBY", "male"),
    ("Darth Maul", "Sith", "54BBY", "male"),
    ("Count Dooku", "Sith", "102BBY", "male"),
    # Galactic Republic
    ("Padmé Amidala", "Galactic Republic", "46BBY", "female"),
    # No faction
    ("Boba Fett", None, "32BBY", "male"),
    ("Jabba the Hutt", None, "600BBY", "male"),
]


class Command(BaseCommand):
    help = "Load sample Star Wars factions and characters into the database."

    def handle(self, *args, **options):
        factions = {}
        for name in FACTIONS:
            factions[name], created = Faction.objects.get_or_create(name=name)
            self.stdout.write(f"{'Created' if created else 'Exists '}  faction    {name}")

        for name, faction_name, birth_date, gender in CHARACTERS:
            _, created = Character.objects.update_or_create(
                name=name,
                defaults={
                    "faction": factions[faction_name] if faction_name else None,
                    "birth_date": birth_date,
                    "gender": gender,
                },
            )
            self.stdout.write(f"{'Created' if created else 'Updated'}  character  {name}")

        self.stdout.write(self.style.SUCCESS(
            f"Done: {Faction.objects.count()} factions, {Character.objects.count()} characters in database."
        ))
```

How it works:

- **`class Command(BaseCommand)`** with a **`handle()`** method is the standard shape of every Django management command. `handle()` runs when you call the command.
- **`get_or_create(name=...)`** fetches the faction if it exists, otherwise creates it. It returns `(object, created)`.
- **`update_or_create(name=..., defaults={...})`** finds a character by name and updates its other fields, or creates it if it doesn't exist.
- Because of these two, the command is **safe to run repeatedly**. Running it twice doesn't create duplicates.
- Characters with `None` as faction (Boba Fett, Jabba) are stored with no faction.

**13c. Run it**:

```powershell
python manage.py seed
```

Output (shortened):

```
Created  faction    Rebel Alliance
...
Created  character  Luke Skywalker
...
Done: 5 factions, 22 characters in database.
```

Running it a second time prints `Exists` / `Updated` instead of `Created` and the totals stay the same.

Data loaded:

| Faction           | Characters                                                                                     |
|-------------------|------------------------------------------------------------------------------------------------|
| Rebel Alliance    | Luke Skywalker, Leia Organa, Han Solo, Chewbacca, Lando Calrissian, Mon Mothma, Wedge Antilles, R2-D2, C-3PO |
| Galactic Empire   | Darth Vader, Grand Moff Tarkin                                                                 |
| Jedi Order        | Obi-Wan Kenobi, Yoda, Mace Windu, Qui-Gon Jinn, Ahsoka Tano                                     |
| Sith              | Darth Sidious, Darth Maul, Count Dooku                                                         |
| Galactic Republic | Padmé Amidala                                                                                  |
| *(no faction)*    | Boba Fett, Jabba the Hutt                                                                      |

> Birth dates are approximate. Sources disagree on several (e.g. Han Solo is 29BBY in some, 32BBY in others). The droids R2-D2 and C-3PO use gender `other`.

Check the data at http://127.0.0.1:8000/api/characters, in Swagger, or in the admin at http://127.0.0.1:8000/admin/.

### Step 14: Add a `.gitignore`

A `.gitignore` tells Git which files **not** to track, such as generated files, local-only files and secrets.

New file `.gitignore` in the project root:

```gitignore
# Virtual environment
.venv/
venv/
env/

# Python bytecode / cache
__pycache__/
*.py[cod]

# Django
db.sqlite3
db.sqlite3-journal
*.log
media/
staticfiles/

# Environment variables / secrets
.env
.env.*

# Testing / coverage
.pytest_cache/
.coverage
htmlcov/

# Editors / IDEs
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
```

| Ignored                   | Why                                                                                   |
|---------------------------|---------------------------------------------------------------------------------------|
| `.venv/`                  | Large and machine-specific. Anyone can recreate it (Step 1 + Step 2)                  |
| `__pycache__/`, `*.pyc`   | Compiled Python files that are regenerated automatically                              |
| `db.sqlite3`              | Local database. Each developer builds their own with `migrate` + `seed` (Steps 6, 13) |
| `.env`                    | Where secrets such as passwords and API keys usually live. Never commit these         |
| `.vscode/`, `.idea/`      | Personal editor settings                                                              |

What **is** committed: source code, `migrations/` (other developers need these to build the same database), `README.md`, and `.gitignore` itself.

> Because `db.sqlite3` is ignored, someone cloning the project sets it up with:
> ```powershell
> python manage.py migrate
> python manage.py seed
> python manage.py createsuperuser
> ```

### Step 15: Move settings into a `.env` file (python-dotenv)

`settings.py` had the `SECRET_KEY` and `DEBUG` written directly in the code. Anyone who can see the code would then see the secret key, and switching between development and production would mean editing code. A `.env` file keeps these values **outside the code**, and it's ignored by Git (Step 14).

**15a. Install python-dotenv**: it reads a `.env` file and loads its values as environment variables:

```powershell
pip install python-dotenv
```

**15b. Create `.env`** in the project root (next to `manage.py`):

```dotenv
SECRET_KEY='django-insecure-...your key...'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

- The `SECRET_KEY` is wrapped in **single quotes** because it contains `#` (which `.env` files can treat as a comment) and other special characters. Single quotes keep the value exactly as written.
- All values in `.env` are **text**. `DEBUG=True` arrives in Python as the string `"True"`, not the boolean `True` (handled in 15d).

**15c. Create `.env.example`**: a copy with placeholder values that **is** committed, so others know which variables to set:

```dotenv
SECRET_KEY='change-me'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Because `.gitignore` ignores `.env.*`, it needs an exception so `.env.example` is still tracked:

```gitignore
.env
.env.*
!.env.example
```

(`!` means "don't ignore this one".)

**15d. Update `starwars_api/settings.py`**:

```python
import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from the .env file in the project root into os.environ
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
```

| Line | What it does |
|---|---|
| `load_dotenv(BASE_DIR / '.env')` | Reads `.env` and puts each value into `os.environ`. The full path means it works from any working directory. Variables already set in the real environment are **not** overwritten, so a server can override `.env` |
| `os.environ['SECRET_KEY']` | **Required.** If it's missing, Django fails at startup with a `KeyError` instead of running with no key |
| `os.getenv('DEBUG', 'False') == 'True'` | Converts the text to a real boolean. Defaults to `False` (the safe choice) if not set |
| `os.getenv('ALLOWED_HOSTS', '').split(',')` | Turns `"localhost,127.0.0.1"` into `['localhost', '127.0.0.1']` |

> **ALLOWED_HOSTS changed** from `[]` to `localhost,127.0.0.1`. With `DEBUG=True` Django allowed these automatically. Listing them explicitly means the project keeps working locally even with `DEBUG=False`. Any other hostname gets a `400 Bad Request`.

Verify:

```powershell
python manage.py check
```

Tested: the secret key loads identically from `.env`, `DEBUG` is the boolean `True`, and the API responds on `127.0.0.1` and `localhost` (`200`) but rejects an unknown host (`400`).

> Someone cloning the project now runs `copy .env.example .env` first (and puts in their own `SECRET_KEY`) before the commands from Step 14. A new key can be generated with:
> ```powershell
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### Step 16: Create `requirements.txt`

`requirements.txt` lists every package the project needs, with exact versions, so anyone can install the same set with one command.

Generate it from the active venv:

```powershell
pip freeze > requirements.txt
```

Result:

```
annotated-types==0.8.0
asgiref==3.12.1
Django==6.1.1
django-ninja==1.7.1
pydantic==2.13.5
pydantic_core==2.46.5
python-dotenv==1.2.4
sqlparse==0.6.0
typing-inspection==0.4.4
typing_extensions==4.16.0
tzdata==2026.5
```

- `pip freeze` lists **everything** installed in the venv: the 3 packages we installed directly (`django-ninja`, `python-dotenv`, and `Django` through Ninja) plus their dependencies.
- `==` pins exact versions, so everyone gets the same versions and the project doesn't break when a new release comes out.
- Run the command **with the venv active**. Otherwise it lists your global Python packages instead.

Install from it (on a fresh clone, inside a new venv):

```powershell
pip install -r requirements.txt
```

> When you install a new package later, run `pip freeze > requirements.txt` again to update the file.

Tested: installed `requirements.txt` into a brand-new empty venv. `pip check` found no conflicts and `python manage.py check` passed.

---

## Quick start (fresh clone)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # then set your own SECRET_KEY in .env
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000/api/docs
