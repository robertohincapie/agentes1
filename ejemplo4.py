import asyncio

from agents import Agent, ItemHelpers, Runner, trace, WebSearchTool, ModelSettings

from dotenv import load_dotenv
load_dotenv()

maestro = Agent(
    name="Agente maestro",
    instructions=("Tu debes recibir un nombre de un programa académico, el nivel del mismo y una breve descripción de a qué se refiere. " 
                  "Con esta información deberás realizar una búsqueda en la web, encontrando primer a nivel del país Colombia, luego en Latinoamérica programas similares "
                  "con esta información, deberás construir un listado de programas con la siguiente información por cada programa: "
                  "Nombre del programa, nivel del programa, universidad que lo ofrece"
                  ) ,
    tools=[WebSearchTool(search_context_size='low')],
    model="gpt-4.1",
    model_settings=ModelSettings(
       temperature=0.2,  # Lower for more deterministic outputs (0.0-2.0)
       #max_tokens=1024,  # Maximum length of response
    ),
   output_type=str
)

buscador_programa = Agent(
    name="Agente buscador de programas",
    instructions=("Tu recibes la información básica de un programa y debes buscar con más detalle "
                  "datos adicionales del mismo como son: la duración, el número de créditos, "
                  "la dirección web del programa en la página de su universidad, su nivel académico, "
                  "el costo de un semestre, si la universidad es privada o publica. "
                  "Es importante pero no imprescindible si se encuentran los cursos del programa") ,
    tools=[WebSearchTool(search_context_size='low')],
    model="gpt-4.1",
    model_settings=ModelSettings(
       temperature=0.2,  # Lower for more deterministic outputs (0.0-2.0)
       #max_tokens=1024,  # Maximum length of response
    ),
   output_type=str
)

arquitecto_de_busqueda = Agent(
    name="Agente buscador de diferentes programas",
    instructions=("Tu recibes una entrada que menciona varios programas académicos."
                  "Primero identifica cada uno de los programas y llama a la herramienta buscador_programa, "
                  "Haciendo que cada programa sea buscado por dicha herramienta. Al final espera todas las respuestas "
                  "y genera un reporte final con el texto detallado de cada programa") ,
    tools=[buscador_programa.as_tool(
            tool_name="BuscadorPrograma",
            tool_description="Busca un programa en la web para completar su información",
        ),],
    model="gpt-4.1",
    model_settings=ModelSettings(
       temperature=0.2,  # Lower for more deterministic outputs (0.0-2.0)
       #max_tokens=1024,  # Maximum length of response
    ),
   output_type=str
)

async def main():
    input_prompt = input("Escriba el nombre del programa, su nivel académico y una breve descripción del mismo:")

    resultado_maestro = await Runner.run(
            maestro,
            input_prompt,
        )
    resultado_busqueda= await Runner.run(
        arquitecto_de_busqueda, 
        resultado_maestro.final_output
    )
    print("Resultado final:", resultado_busqueda.final_output)


if __name__ == "__main__":
    asyncio.run(main())