from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

from app.routers import health, profiles, parsed_ads, exports

app = FastAPI(title="Technoreboot Avito Module API")

app.include_router(health.router)
app.include_router(profiles.router)
app.include_router(parsed_ads.router)
app.include_router(exports.router)

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
