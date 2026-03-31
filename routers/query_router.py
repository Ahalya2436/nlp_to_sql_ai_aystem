from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from repositories.query_repository import get_user_history
from schemas.query_schema import PromptRequest
from services.query_services import handle_prompt
from services.schema_vector_services import create_collection, store_schema_embeddings

router = APIRouter()
class AskRequest(BaseModel):
    prompt: str
    user_id: int
@router.post("/ask")
def ask_query(request: PromptRequest, db: Session = Depends(get_db)):
    return handle_prompt(request.prompt, request.user_id, request.schema_name, db)

@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    return get_user_history(db)

@router.get("/load-schema")
def load_schema_embeddings(db: Session = Depends(get_db)):

    databases = ["ask_db","employee_db","ecommerce_db","sales_db", "hr_db", "hospital_db"]

    # ensure collection exists
    create_collection()

    for d in databases:
        store_schema_embeddings(db, d)

    return {"message": "Schema embeddings loaded"}