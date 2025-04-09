from fastapi import FastAPI

from routes.currency_routes import router as currency_router

app = FastAPI()


app.include_router(currency_router, prefix="/currency")