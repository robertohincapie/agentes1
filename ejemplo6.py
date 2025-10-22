# planner_executor_agent.py
from agents import Agent, Runner, WebSearchTool, function_tool
from pydantic import BaseModel, Field
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio

load_dotenv()
# ----------------------------
# Tools del EXECUTOR
# ----------------------------
@function_tool
def fetch_url(url: str, max_chars: int = 4000) -> str:
    """
    Descarga una página y retorna texto visible (recortado).
    """
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return text[:max_chars]

# ----------------------------
# EXECUTOR AGENT
# ----------------------------
EXECUTOR_INSTRUCTIONS = """
Eres un EXECUTOR. Tu trabajo es resolver subtareas CONCRETAS que te delega un Planner.
Sigue este patrón simple de verificación:
- Si necesitas fuentes, usa primero la herramienta de búsqueda web para localizar URLs confiables.
- Luego, usa fetch_url para extraer el contenido clave y verificar.
- Devuelve SIEMPRE una respuesta breve, precisa y con 1–3 URLs como evidencia.
No inventes datos. Si hay incertidumbre, dilo explícitamente.
Formato de salida recomendado (texto):
- Hallazgos clave en 3–6 viñetas.
- Fuentes: lista de URLs.
"""

executor = Agent(
    name="Executor",
    instructions=EXECUTOR_INSTRUCTIONS,
    tools=[WebSearchTool(), fetch_url],
)

# ----------------------------
# PLANNER → delega subtareas al EXECUTOR mediante una function tool
# ----------------------------
@function_tool
async def delegate_to_executor(subtask: str) -> str:
    """
    Ejecuta la subtarea con el EXECUTOR y devuelve su salida final.
    """
    res = await Runner.run(starting_agent=executor, input=subtask)
    return res.final_output

# ----------------------------
# MODELO PARA PARSEAR EL INFORME FINAL (opcional)
# ----------------------------
class ProgramItem(BaseModel):
    program_name: Optional[str] = Field(None, description="Nombre del programa")
    university: Optional[str] = Field(None, description="Universidad")
    country: Optional[str] = Field(None, description="País")
    url: Optional[str] = Field(None, description="URL oficial o principal")
    courses_examples: List[str] = Field(default_factory=list, description="Curso(s) representativos si están disponibles")
    tuition: Optional[str] = Field(None, description="Costo (monto+moneda+periodicidad) si está disponible")
    intake_per_year: Optional[str] = Field(None, description="Ingreso/aforo anual si está disponible")
    sources: List[str] = Field(default_factory=list)

class FinalReport(BaseModel):
    input_program: str
    input_description: str
    coverage: dict
    items: List[ProgramItem]
    insights: List[str]

# ----------------------------
# PLANNER AGENT
# ----------------------------
PLANNER_INSTRUCTIONS = """
Eres un PLANNER. Tu objetivo es:
1) Descomponer la solicitud del usuario en subtareas claras.
2) Delegar cada subtarea al EXECUTOR usando la herramienta delegate_to_executor.
3) Integrar la información en un informe final estructurado, con cobertura local, nacional e internacional.

Reglas:
- Empieza definiendo 4–8 subtareas que cubran: búsqueda local, nacional e internacional; syllabus/plan de estudios; costo (tuition/fees); ingreso/cupos (intake/enrollment); y tendencias del nombre del programa.
- Para cada subtarea, haz:
  Thought: explica por qué esa subtarea es necesaria.
  Action: delegate_to_executor{"subtask": "..."}
  Observation: captura el resumen devuelto por el EXECUTOR.
- Tras cubrir suficientes resultados (≥6 programas únicos o ≥2 por nivel geográfico), sintetiza.

Salida final:
Devuelve un JSON que cumpla EXACTAMENTE este esquema (usa lenguaje claro):
{
  "input_program": "...",
  "input_description": "...",
  "coverage": {"local": int, "national": int, "international": int},
  "items": [
    {
      "program_name": "...",
      "university": "...",
      "country": "...",
      "url": "...",
      "courses_examples": ["...", "..."],
      "tuition": "...",
      "intake_per_year": "...",
      "sources": ["...", "..."]
    }
  ],
  "insights": ["...", "...", "..."]
}

Notas:
- Incluye SIEMPRE "sources" por ítem (aunque sea 1 URL).
- Si un campo no aparece en la web, déjalo vacío o pon "No disponible".
- No incluyas el texto de Thought/Action/Observation en el JSON final.
- Mantén el informe conciso y verificable.
"""

planner = Agent(
    name="Planner",
    instructions=PLANNER_INSTRUCTIONS,
    tools=[delegate_to_executor],  # El Planner solo puede delegar (no busca directo)
)


async def main():
    user_program = "Ingeniería en ciencia de Datos"
    user_desc = "Programa orientado a analítica, ingeniería de datos e inteligencia artificial."

    prompt = f"""
Quiero mapear programas similares a: "{user_program}".
Descripción corta: "{user_desc}".

Tareas:
- Encontrar programas locales (Colombia), nacionales (LATAM) e internacionales (EE.UU./Europa).
- Para cada programa: nombre, universidad, sitio web, cursos representativos, costo (si existe) y estudiantes que ingresan (si existe).
- Si no encuentras suficiente información para un país o región, amplía el rango de búsqueda.
- Al final, analiza si el nombre del programa aparece en búsquedas/tendencias (usa términos ES/EN si ayuda).

Devuélveme el JSON final con el esquema indicado.
"""

    # Ejecuta Planner/Executor (el Planner delega internamente al Executor)
    result = await Runner.run(starting_agent=planner, input=prompt)

    # Texto final (debería ser JSON)
    print("\n=== FINAL (JSON) ===")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
