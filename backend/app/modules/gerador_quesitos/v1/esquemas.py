# backend/app/modules/gerador_quesitos/v1/esquemas.py
from pydantic import BaseModel, Field

class RespostaQuesitos(BaseModel):
    """Schema para a resposta contendo os quesitos gerados."""
    quesitos_texto: str = Field(..., description="O texto formatado contendo os quesitos gerados pela IA.")

# Não são necessários outros schemas por enquanto.
