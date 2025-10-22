# react_agent_example.py
from agents import Agent, Runner, WebSearchTool, function_tool
import requests
from bs4 import BeautifulSoup

from dotenv import load_dotenv
load_dotenv()

"""
Modelo que implementa la arquitectura react con una cadena de pensamientos. Se define dentro de un 
agente la manera como debe operar durante su evolución hasta que obtiene una respuesta definitiva. 
"""

@function_tool
def fetch_url(url: str, max_chars: int = 3000) -> str:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return text[:max_chars]

# --- Instrucciones estilo ReAct ---
#El modelo react no es una clase especial, simplemente corresponde a unas instrucciones que hacen 
#un ciclo de pensamiento, acción, observación, pensamiento, etc. 
REACT_INSTRUCTIONS = """
Eres un agente ReAct. Debes razonar paso a paso y usar herramientas cuando sea útil.
Formato de interacción:
- Thought: explica tu siguiente paso brevemente.
- Action: <tool_name>[<json_args>]
- Observation: (resultado resumido)
Repite Thought/Action/Observation las veces necesarias. 
Cuando tengas la respuesta final, termina con:
- Final: <respuesta breve y clara + fuentes>

Reglas:
- Prefiere buscar primero con web_search para encontrar la fuente más confiable.
- Si obtienes una URL candidata, usa fetch_url para extraer el contenido y verificar datos.
- Cita 1–3 URLs confiables en el "Final".
- No inventes datos; si hay incertidumbre, decláralo.
"""

# --- Agente con herramientas (ReAct loop gestionado por la SDK) ---
agent = Agent(
    name="ReAct-Agent",
    instructions=REACT_INSTRUCTIONS,
    tools=[
        WebSearchTool(),   # Hosted tool: búsqueda web
        fetch_url          # Function tool: abrir URL y extraer texto
    ],
)

if __name__ == "__main__":
    # Ejemplo sencillo de tarea (cámbialo por lo que necesites):
    prompt = (
        "Encuentra el plan de estudios oficial del programa 'Ingeniería en Ciencia de Datos' de alguna "
        "universidad reconocida en Latinoamérica y dime 3 cursos troncales frecuentes. "
        "Entrega la respuesta final con 2–3 fuentes."
    )

    # Ejecuta el bucle ReAct (la SDK itera Thought→Action→Observation hasta finalizar)
    result = Runner.run_sync(agent, prompt) #este comando evita tener que llamar a una función async
    #internamente crea el loop y llama al agente dentro de ella. 
    # result.final_output contiene el 'Final: ...' del agente
    print('Resultado final del agente:','\n',result.final_output)

    # (Opcional) También puedes inspeccionar los pasos intermedios:
    
    print('Eventos del agente: ')
    for ev in result.raw_responses:
        print('\n------------------\n',ev)  # Verás tool_calls, observations, etc.
