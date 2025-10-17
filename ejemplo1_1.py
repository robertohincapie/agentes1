# -*- coding: utf-8 -*-
import asyncio, threading
from agents import Agent, Runner, ModelSettings, WebSearchTool, function_tool
from dotenv import load_dotenv
from typing import List, Tuple, Any
from pydantic import BaseModel, Field, ValidationError
load_dotenv() #Carga de la clave de acceso de OpenAI
import json, re

class Respuesta_marcas(BaseModel):
    anio_separacion: str = Field(..., description="Año de la separación")
    motivo: str = Field(..., description="Motivo factual de la separación")
    marca_original: str = Field(..., description="Nombre de la marca original antes de separarse")
    marcas_resultantes: List[str] = Field(default_factory=list, description="Marcas tras la separación")

# Función para validar la respuesta y determinar si está completa o no
#@function_tool
def validar(info: Respuesta_marcas) -> bool:
    try:
        flag_anio=len(info.anio_separacion)>0 
        print('Año: ',flag_anio)
        flag_motivo=len(info.motivo)>0
        print('Motivo: ',flag_motivo)
        flag_marca=len(info.marca_original)>0
        print('Marca Original: ',flag_marca)
        flag_marcas=len(info.marcas_resultantes)>0 
        print('Marcas resultantes:',flag_marcas)
        flag=flag_anio and flag_motivo and flag_marca and flag_marcas
        print('Se procede a validar las marcas nuevas y los dueños')
        #for d2 in info['marcas_resultantes']:
        #   flag=flag and len(d2['marca'])>0 and len(d2['dueños'])>0 
        #if(not(flag)): 
        #    print('En la validación, falta alguno de los datos')
        return flag
    except Exception as e:
        print('Ocurrió una excepción en la validación: ',e)
        return False
# Creamos un agente básico que trata de responder la pregunta. 

agente1 = Agent(
   name="Buscador de noticias",
   instructions="""Eres un agente conocedor de información de mercado, que puede 
   extraer y presentar información acerca de la separación de una marca tradicional en antioquia
   que se separó en dos marcas nuevas. 
   Tu respuesta debe incluir los siguientes campos: 
   anio_separacion, que indica el año en que ocurrió la separación
   motivo, que describe la razón por la cuál la dos marcas se separaron
   marca_original, corresponde a la marca que compartían las empresas inicialmente y
   marcas_resultantes, construida como una lista que indica las marcas nuevas y los dueños dueños que quedaron en cada una de las marcas nuevas. 
   Presenta respuestas factuales, sin inventar información que no se conoce. 
   Si no conoces la información, deja el campo vacío en la respuesta. 
   """,
   tools=[],
   model="gpt-4.1-nano",
   model_settings=ModelSettings(
       temperature=0.0,  # Lower for more deterministic outputs (0.0-2.0)
       #max_tokens=1024,  # Maximum length of response
   ),
   output_type=Respuesta_marcas
)



# Creamos un agente básico que trata de responder la pregunta. 
agente2 = Agent(
   name="Buscador de noticias",
   instructions="""Eres un agente conocedor de información de mercado, que puede 
   extraer y presentar información acerca de la separación de una marca tradicional en antioquia
   que se separó en dos marcas nuevas. 
   Tu respuesta debe incluir los siguientes campos: 
   anio_separacion, que indica el año en que ocurrió la separación
   motivo, que describe la razón por la cuál la dos marcas se separaron
   marca_original, corresponde a la marca que compartían las empresas inicialmente y
   marcas_resultantes, construida como una lista que indica las marcas nuevas y los dueños dueños que quedaron en cada una de las marcas nuevas. 
   Presenta respuestas factuales, sin inventar información que no se conoce. 
   Si no conoces la información, deja el campo vacío en la respuesta. 
   """,
   tools=[WebSearchTool(search_context_size='low')],
   model="gpt-4.1",
   model_settings=ModelSettings(
       temperature=0.0,  # Lower for more deterministic outputs (0.0-2.0)
       #max_tokens=1024,  # Maximum length of response
   ),
   output_type=Respuesta_marcas
)

# Creamos un agente básico que trata de responder la pregunta. 
agente3 = Agent(
   name="Generador de reporte",
   instructions="""Eres un agente conocedor de información de mercado, que puede 
   extraer y presentar información acerca de la separación de una marca tradicional en antioquia
   que se separó en dos marcas nuevas. 
   Vas a recibir una información respecto a la separación de una marca antioqueña. Complementa lo necesario con una busqueda web 
   y genera un reporte tipo noticia, que especifique la información que se te pasa y otra que pueda complementar
   """,
   tools=[WebSearchTool(search_context_size='low')],
   model="gpt-4.1",
   model_settings=ModelSettings(
       temperature=0.8,  # Lower for more deterministic outputs (0.0-2.0)
       #max_tokens=1024,  # Maximum length of response
   ),
   output_type=str
)
async def main():
    try:
        result = await asyncio.wait_for(
            Runner.run(agente1, "Dime por qué se separó el supermercado la vaquita en la vaquita y supermu"),
            timeout=30)
        #print("Resultado de la primera consulta: ",result.final_output)
        assert isinstance(result.final_output, Respuesta_marcas)
        valido=validar(result.final_output)
        
        if(not(valido)):
            print("No fue una respuesta completa, se pasa a un segundo agente")
            result2 = await asyncio.wait_for(
                Runner.run(agente2, "Dime por qué se separó el supermercado la vaquita en la vaquita y supermu"),
                timeout=30)
            #print("Resultado de la segunda consulta: ",result2.final_output)
            assert isinstance(result2.final_output, Respuesta_marcas)
            valido2=validar(result2.final_output)
        
            if(valido2):
                result3 = await asyncio.wait_for(
                    Runner.run(agente3, json.dumps(result2.final_output, ensure_ascii=False, indent=2)),
                    timeout=30)
                print('-------------------------------')
                print(result3.final_output)
                
    except Exception as e:
        print('Ocurrió un error :',e)
    
    # Function calls itself,
    # Looping in smaller pieces,
    # Endless by design.

asyncio.run(main())

