from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from routers.query_router import router as query_router
from routers.auth_router import router as auth_router
from routers.dashboard_router import router as dashboard_router

from database import engine, Base

app = FastAPI(title="AskDB AI")

# create tables
Base.metadata.create_all(bind=engine)

# include routers
app.include_router(query_router, prefix="/query", tags=["Query"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

# remove prefix here
app.include_router(dashboard_router)

# templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

