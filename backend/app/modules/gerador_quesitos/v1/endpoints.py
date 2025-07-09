# backend/app/modules/gerador_quesitos/v1/endpoints.py
import logging
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
)
from .esquemas import RespostaQuesitos

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

MOCK_RESPONSE = """
1.  Com base nos documentos médicos apresentados, qual o diagnóstico da parte autora?
2.  A doença é crônica ou aguda?
3.  Existem evidências de incapacidade para o trabalho habitual de {profissao}?
4.  A incapacidade é total ou parcial?
5.  A incapacidade é temporária ou permanente?
6.  Quais tratamentos foram realizados?
7.  O tratamento atual é eficaz?
8.  Quais as limitações funcionais impostas pela doença?
9.  A doença impede o autor de realizar atividades da vida diária?
10. O ambiente de trabalho agrava a condição do autor?
11. O autor está apto para reabilitação profissional?
12. Qual o prognóstico da doença?
13. A doença tem nexo causal com o trabalho exercido?
14. O autor necessita de auxílio de terceiros para suas atividades?
15. É possível estimar a data de início da incapacidade?
"""

@router.post(
    "/gerar",
    response_model=RespostaQuesitos,
    summary="Gera quesitos a partir de dados fornecidos (atualmente mockado).",
    tags=["Gerador Quesitos"],
)
async def gerar_quesitos(
    beneficio: str = Form(...),
    profissao: str = Form(...),
    modelo_nome: str = Form(...),
    file: UploadFile = File(..., description="Arquivo PDF para análise (atualmente não processado)."),
):
    """
    Recebe os dados do formulário e um arquivo PDF para gerar quesitos.

    **Fluxo Atual (Simulado):**
    - Recebe os parâmetros: `beneficio`, `profissao`, `modelo_nome` e um `file`.
    - Ignora o arquivo e os parâmetros da LLM.
    - Retorna uma lista de 15 quesitos genéricos (mockados) formatados com a profissão.
    """
    logger.info(
        f"Recebida requisição para gerar quesitos (mockado) com os seguintes dados: "
        f"Benefício='{beneficio}', Profissão='{profissao}', Modelo='{modelo_nome}', "
        f"Arquivo='{file.filename}'"
    )

    # Simplesmente formata a resposta mockada com a profissão
    response_text = MOCK_RESPONSE.format(profissao=profissao)

    return RespostaQuesitos(quesitos_texto=response_text)