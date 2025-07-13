from logger import logger
import streamlit as st
from PIL import Image
from main import*
from etabs_interface import*

# Simulaciones de funciones externas (reemplaza con tus funciones reales)
def execution_vision_model(image):
    #!pip install langchain langchain-groq
    #!pip install openai langchain
    #!pip install langchain_community
    import os
    #from dotenv import load_dotenv
    from pydantic import BaseModel, Field
    from langchain_core.output_parsers import JsonOutputParser
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain

    from langchain.llms import OpenAI
    import os

    # Set your OpenAI API key (make sure to keep it safe!)
    os.environ["OPENAI_API_KEY"] = "sk-pr7_mXrFr3U2kRbi5Oo1SNgg9agEzfEouWfWqiEFxH5h86T3BlbkFJPCC8mUIQ-KlxhfphY1sDMfB76MQHBJUJUeA6SuGiCcVN0rTAazOxbFCvnBTdx5neFRx18GbUUA"

    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage

    llm = ChatOpenAI(model_name="gpt-4", temperature=0)

    #%pip install Pillow
    import base64
    from io import BytesIO
    from PIL import Image
    import os

    import os
    #from dotenv import load_dotenv
    from langchain_groq import ChatGroq
    from groq import Groq

    def encode_image(image):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def describe_image(image):
        VISION_MODEL_NAME="meta-llama/llama-4-maverick-17b-128e-instruct"  #"meta-llama/llama-4-scout-17b-16e-instruct"
        client = Groq(api_key='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')
        vision_model = VISION_MODEL_NAME

        # Removed: image = Image.open(image)  # Ya es un objeto Image
        base64_image = encode_image(image)

        completion = client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Strictly extract the coordinates from all entries labeled C(index) as they appear in the image. Only take the numeric values inside parentheses (C(x, y)) and list them in order: C0, C1, C2, etc "
                        "Strictly and accurately extract all core_h and core_v elements"
                            "Return one tuple per value for each horizontal (core_h) and vertical (core_v) core"
                            "Do not add any value that is not clearly visible in the image."
                            "Do not simplify or modify any tuples — extract them exactly as shown."
            
                        
                        "Strictly and accurately extract all bal and op elements. "
                        "For bal and op, do not extract coordinates — only extract the indices inside parenthese "},  
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
        )

        return completion.choices[0].message.content

    description = describe_image(image)
    print("Image description:", description)
    print(description)
    return description

def execute_model_language(description):
    from langchain_core.output_parsers import JsonOutputParser
    from pydantic import BaseModel, Field
    from typing import List
    from langchain_groq import ChatGroq
    from groq import Groq
    import base64
    from io import BytesIO
    from PIL import Image
    import os
    import os
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage
    import os
    #from dotenv import load_dotenv
    from pydantic import BaseModel, Field
    from langchain_core.output_parsers import JsonOutputParser
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    from langchain.llms import OpenAI
    import os
    llm = ChatOpenAI(model_name="gpt-4", temperature=0)

    recibo= description
    TEMPLATE="""Your task is estract from this information for the coordinates C(x,y) 
    where the first elements "x" must be saved in the list x_coordinates nad the second element "y" must be saved in the list y_coordinates
    Only show each different value for x. Only show each different value for y. 
    The information is: {recibo}

    Any list could contain any duplicated value. 
    Allways return a valid JSON that follows this format : {format_instructions}
    """

    TEMPLATE_bal = """ Your task is estract from this information for **bal_h()** and **bal_v()**, **op_h()** and **op_v()**, **core_h()** and **core_v()**
    The information is the follow : {recibo}

    Extract the values inside parentheses from the core_*_h and core_*_v elements into two separate lists:
    A list core_h containing the values from all core_*_h elements, in numerical index order.
    A list core_v containing the values from all core_*_v elements, in numerical index order.
    Consider all values exactly as they appear — do not modify or remove anything.
    Consider that the asterix could take different integer values as 0, 1, 2, etc. It depends on the information.

    Your response must be allways a JSON valid object with the follow structure:  
    {format_instructions}
    """

    class ContentGenerationScript(BaseModel):
        x_coordinates: List[float] = Field(
            description="Coordenadas X"
        )
        y_coordinates: List[float] = Field(
            description="Coordenadas Y"
        )

    parser = JsonOutputParser(pydantic_object=ContentGenerationScript)

    class cores(BaseModel):  #actualizar nombre de parser
        cores : List[int] = Field(
            description="cores (n_core_h)"
        )
        
    parser_cores = JsonOutputParser(pydantic_object=cores)  #actualizar nombre de parser

    prompt = PromptTemplate(
        input_variables=["recibo"],
        template=TEMPLATE,
        #parcial : poner nuevo nombre
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = LLMChain(llm=llm, prompt=prompt, output_parser=parser) #promt actualizar

    recibo= description

    result_1 = chain.invoke({"recibo": recibo})  #actualizado de recibo a text

    result_1
    
    class balcones(BaseModel):  #actualizar nombre de parser
        bal_h : List[float] = Field(
            description="bal_h"
        )
        bal_v : List[float] = Field(
            description="bal_v"
        )
        op_h : List[float] = Field(
            description="op_h"
        )
        op_v : List[float] = Field(
            description="op_v"
        )
        
        core_h : List[float] = Field(
            description="Horizontales (core_*_h)"
        )
        core_v : List[float] = Field(
            description="Verticales (core_*_v)"
        )

    parser_bal = JsonOutputParser(pydantic_object=balcones)  #actualizar nombre de parser

    prompt_bal = PromptTemplate(
        input_variables=["recibo"],
        template=TEMPLATE_bal,  #actualizar con el template especifico
        partial_variables={"format_instructions": parser_bal.get_format_instructions()},
    )

    chain = LLMChain(llm=llm, prompt=prompt_bal, output_parser=parser_bal)
    
    result_3 = chain.invoke({"recibo": recibo})  #actualizado de recibo a text

    result_3

    return result_1, result_3

def format_output(result_1, result_3):
    print(result_1['text'])
    print(type(result_1['text']))

    x_coordinates = sorted(list(result_1['text'].values())[0])
    y_coordinates = sorted(list(result_1['text'].values())[1])

    logger.info(f"Las coordenadas X extraidas son {x_coordinates}") #TEMP Logger
    logger.info(f"Las coordenadas X extraidas son {y_coordinates}") #TEMP Logger

    balcony_axis = [sorted(result_3['text']['bal_h']), sorted(result_3['text']['bal_v'])]
    logger.info(f"Las coordenadas de balcones extraidas son {balcony_axis}")

    openings = [tuple(sorted(result_3['text']['op_v']) + sorted(result_3['text']['op_h']))]
    logger.info(f"Las coordenadas de tragaluces extraidas son {openings}")

    core_h_list = result_3['text']['core_h']
    logger.info(f"Los ejes horizontales de muros extraidos son {core_h_list}")

    core_v_list = result_3['text']['core_v']
    logger.info(f"Los ejes verticales de muros extraidos son {core_v_list}")

    core_h_tpl=[]
    for i in range(0, len(core_h_list), 2):
        if i+1 < len(core_h_list):
            core_h_tpl.append((core_h_list[i], core_h_list[i+1]))

    core_v_tpl=[]
    for i in range(0, len(core_v_list), 2):
        if i+1 < len(core_v_list):
            core_v_tpl.append((core_v_list[i], core_v_list[i+1]))

    cores = []
    for core_i, core_j in zip(core_h_tpl, core_v_tpl):
        a = {'horizontal': core_i, 'vertical': core_j}
        cores.append(a)
    
    logger.info(f"Los ejes horizontales y verticales de muros extraidos son {cores}")

    return x_coordinates, y_coordinates, balcony_axis, openings, cores

from etabs_interface import *
from functions_parameter_etabs import *
import pandas as pd

# ---------------- INTERFAZ ----------------
st.set_page_config(page_title="Plano Editor", layout="centered")
st.title("🛠 Editor de Plano Estructural")

# --- 1. CARGAR IMAGEN ---
st.header("🖼 Cargar imagen de plano")
uploaded_file = st.file_uploader("Sube la imagen del plano", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagen del plano cargada", use_column_width=True)

    # --- 2. EJECUTAR MODELOS ---
    with st.spinner("Ejecutando modelo de visión..."):
        vision_json = execution_vision_model(image)

    with st.spinner("Ejecutando modelo de lenguaje..."):
        result_1, result_3 = execute_model_language(vision_json)

    x_coordinates, y_coordinates, balcony_axis, openings, cores = format_output(result_1, result_3)

    # Crear el diccionario final_input correctamente
    final_input = {
        "coordinates": {
            "x_coordinates": x_coordinates,
            "y_coordinates": y_coordinates
        },
        "balcones": balcony_axis,
        "openings": openings,
        "muros": cores
    }

    # Extraer datos
    default_coordinates = final_input["coordinates"]
    default_balcones = final_input["balcones"]
    default_openings = final_input["openings"]
    default_muros = final_input["muros"]

    # --- 3. MODIFICAR DATOS ---
    st.header("📐 Coordenadas")
    x_coords = st.text_input("Coordenadas X (separadas por coma)", value=", ".join(map(str, default_coordinates["x_coordinates"])))
    y_coords = st.text_input("Coordenadas Y (separadas por coma)", value=", ".join(map(str, default_coordinates["y_coordinates"])))
    x_coords_list = [float(x.strip()) for x in x_coords.split(",") if x.strip()]
    y_coords_list = [float(y.strip()) for y in y_coords.split(",") if y.strip()]

    st.header("🏢 Balcones")
    st.markdown("*Horizontales (índices de Y):*")
    bal_h = st.text_input("balcones horizontales", value=", ".join(map(str, default_balcones[0])))
    st.markdown("*Verticales (índices de X):*")
    bal_v = st.text_input("balcones verticales", value=", ".join(map(str, default_balcones[1])))
    bal_h_list = [float(i.strip()) for i in bal_h.split(",") if i.strip()]
    bal_v_list = [float(i.strip()) for i in bal_v.split(",") if i.strip()]

    st.header("🚪 Openings")
    openings_list = []
    with st.expander("Modificar openings", expanded=True):
        num_openings = st.number_input("Cantidad de openings", min_value=0, max_value=10, value=len(default_openings), step=1)
        for i in range(num_openings):
            st.markdown(f"*Opening #{i+1}*")
            col1, col2, col3, col4 = st.columns(4)
            x1 = col1.number_input(f"x1_idx_{i}", value=default_openings[i][0] if i < len(default_openings) else 0, key=f"x1_{i}")
            x2 = col2.number_input(f"x2_idx_{i}", value=default_openings[i][1] if i < len(default_openings) else 0, key=f"x2_{i}")
            y1 = col3.number_input(f"y1_idx_{i}", value=default_openings[i][2] if i < len(default_openings) else 0, key=f"y1_{i}")
            y2 = col4.number_input(f"y2_idx_{i}", value=default_openings[i][3] if i < len(default_openings) else 0, key=f"y2_{i}")
            openings_list.append((float(x1), float(x2), float(y1), float(y2)))

    st.header("🧱 Muros")
    muros_list = []
    with st.expander("Modificar muros", expanded=True):
        num_muros = st.number_input("Cantidad de muros", min_value=0, max_value=10, value=len(default_muros), step=1)
        for i in range(num_muros):
            st.markdown(f"*Muro #{i+1}*")
            col1, col2 = st.columns(2)
            
            # Get default values if they exist
            default_h = default_muros[i]["horizontal"] if i < len(default_muros) else (0, 0)
            default_v = default_muros[i]["vertical"] if i < len(default_muros) else (0, 0)
            
            h_horizontal = col1.text_input(f"horizontal (y_idx, x_idx) #{i}", 
                                         value=f"{default_h[0]}, {default_h[1]}", 
                                         key=f"hor_{i}")
            v_vertical = col2.text_input(f"vertical (x_idx, y_idx) #{i}", 
                                       value=f"{default_v[0]}, {default_v[1]}", 
                                       key=f"ver_{i}")
            
            try:
                h_tuple = tuple(map(float, [x.strip() for x in h_horizontal.split(",") if x.strip()]))
                v_tuple = tuple(map(float, [x.strip() for x in v_vertical.split(",") if x.strip()]))
                
                if len(h_tuple) == 2 and len(v_tuple) == 2:
                    muros_list.append({
                        "horizontal": h_tuple,
                        "vertical": v_tuple
                    })
                else:
                    st.warning(f"Por favor ingrese exactamente 2 valores para cada eje del muro #{i+1}")
            except Exception as e:
                st.warning(f"Error al interpretar las coordenadas del muro #{i+1}: {str(e)}")

    # --- 4. RESULTADO FINAL ---
    final_data = {
        "coordinates": {
            "x_coordinates": x_coords_list,
            "y_coordinates": y_coords_list
        },
        "balcones": [bal_h_list, bal_v_list],
        "openings": openings_list,
        "muros": muros_list
    }

    st.header("📦 Resultado final")
    st.code(final_data, language="python")

    # --- 5. BOTÓN PARA EJECUTAR BUILD_ETABS ---
# Add these imports at the top of your file
import pythoncom
import threading
story_heights = [5, 3.5, 3.5, 3.5]
#----------------------------------------------------
def run_in_thread():
    pythoncom.CoInitialize()
    try:
        success, message = build_etabs_model_with_beams(
            story_heights,
            x_coordinates,
            y_coordinates,
            slab_prop_name="Slab1",
            slab_offset=0.3,
            balcony_axis=balcony_axis,
            balcony_width=4,
            balcony_depth=2,
            balcony_offset=4.0,
            wall_section="Wall1",
            column_section="ConcCol",
            beam_section="ConcBm",
            cores=cores,
            openings=openings,
        )
        st.session_state.etabs_result = (success, message)
    except Exception as e:
        st.session_state.etabs_result = (False, str(e))
    finally:
        pythoncom.CoUninitialize()
#----------------------------------------------------
# Modify your ETABS building section like this:
 # streamlit run app_plano.py
# --- BUTTON ---
if st.button("🏗 Construir modelo ETABS", type="primary"):
    if 'etabs_result' in st.session_state:
        del st.session_state.etabs_result
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    with st.spinner("Running ETABS function..."):
        thread.join()
    if 'etabs_result' in st.session_state:
        success, message = st.session_state.etabs_result
        if success:
            st.success(message)

            # Recupera los datos desde session_state
            if 'loads' in st.session_state:
                all_loads = st.session_state.loads

                st.subheader("🔍 Cargas extraídas")

                for case_name, load_case in all_loads.items():
                    st.markdown(f"### Caso de carga: **{case_name}**")
                    for key, values in load_case.items():
                        st.write(f"**{key}** = {values}")
                    st.markdown("---")
            else:
                st.warning("No se encontraron cargas. Corre primero el cálculo en main.py.")

        else:
            st.error(message)