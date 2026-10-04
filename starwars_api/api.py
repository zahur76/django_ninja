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


api.add_router("/", core_router)
