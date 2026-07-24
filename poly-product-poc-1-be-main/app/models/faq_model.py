from pydantic import BaseModel

class FAQCreate(BaseModel):
    section: str
    question: str
    answer: str

class FAQOut(BaseModel):
    id: str
    section: str
    question: str
    answer: str
