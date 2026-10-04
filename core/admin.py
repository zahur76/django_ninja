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
