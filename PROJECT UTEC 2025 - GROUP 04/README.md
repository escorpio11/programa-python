# 📌 AI-Powered Structural Design Automation Tool

## Overview

This project is a robust AI-powered automation tool designed to streamline and optimize the structural design process for buildings in **Peru** using **ETABS**, **Python**, and the **COM API**. It integrates **Large Language Models (LLMs)** to handle both geometric data extraction and vision-based tasks, and provides a user-friendly interface via **Streamlit**. The tool enables structural engineers to generate, modify, and verify ETABS models programmatically, ensuring higher accuracy, efficiency, and repeatability in dynamic structural analysis.

# 📂 Folder Structure

```plaitext
project-root/
│
├── backend/
│   ├── Dockerfile               # Docker configuration for the backend
│   ├── models/                  # Pydantic models for ETABS objects
│   ├── prompts/                 # LLM prompt templates
│   ├── src/                     # Backend source code
│   │   ├── etabs_automation.py  # Core ETABS API automation logic
│   │   ├── vision_module.py     # Vision module for reading drawings/images
│   │   ├── llm_module.py        # LLM interaction for data extraction
│   │   ├── geometry_parser.py   # Geometric data processing logic
│   │   └── server.py            # FastAPI server
│   └── requirements.txt         # Python dependencies for backend
│
├── frontend/
│   ├── Dockerfile               # Docker configuration for frontend
│   ├── src/                     # Streamlit source code
│   │   ├── etabs_ui.py          # Streamlit UI for user interaction
│   │   ├── run_model.py         # Connects UI inputs to ETABS automation
│   └── requirements.txt         # Python dependencies for frontend
│
├── README.md                    # Project documentation
└── docker-compose.yml           # Docker Compose configuration
markdown
```
# ✅ Features

- **Full ETABS Automation:** Programmatically creates grids, slabs, walls, columns, beams, and openings using the ETABS COM API.

- **LLM Integration:** Uses Large Language Models for vision tasks (e.g., interpreting scanned structural drawings) and for language-based extraction of design data from technical documents.

- **Geometric Parsing:** Converts extracted data into precise ETABS geometry.

- **Streamlit UI:** Provides a simple and intuitive interface to define model parameters, upload input data, and launch automation.

- **Containerized:** Uses Docker and Docker Compose for easy deployment and portability.

⚙️ Backend Structure
- **Dockerfile:** Defines the backend runtime.

- **models/:** Pydantic models for grids, frames, walls, loads.

- **prompts/:** Templates for LLM queries (e.g., interpret drawings, extract dimensions).

- **src/:**

    - `etabs_automation.py:`Orchestrates the ETABS model creation.
        
    - `vision_module.py:`Processes images/drawings.
        
    - `llm_module.py:`Manages LLM requests (Groq, OpenAI, etc.).
        
    - `geometry_parser.py:`**Transforms extracted text/vision data into ETABS-compatible coordinates.
        
    - `server.py:`Exposes FastAPI endpoints.

# 🎛️ Frontend Structure

- **Dockerfile:** Defines the frontend runtime.

- **src/:**

    - `etabs_ui.py:`Implements the Streamlit UI (input fields, file upload, run button).
    
    - `run_model.py:`Sends user inputs to backend and displays ETABS output/logs.

# 🔍 Documentation of Main Files
## Backend

- `etabs_automation.py:` Core logic to create ETABS grids, slabs, walls, columns, and openings.

- `vision_module.py:` Extracts dimensions and geometry from images using LLM vision.

- `llm_module.py:` Handles communication with LLMs for language tasks.

- `geometry_parser.py:` Validates and converts raw geometry into ETABS model elements.

- `server.py:` Defines API routes for automation tasks.

## Frontend

- `etabs_ui.py:` UI for engineers to select options, upload architectural drawings, and launch scripts.

- `run_model.py:` Calls backend API and shows results in real time.

#🚀 Getting Started
## Prerequisites
- Docker and Docker Compose installed.

- `.env` file with API keys (e.g., `GROQ_API_KEY`, `ETABS_PATH`).

## Installations :
    !pip install langchain langchain-groq
    !pip install openai langchain
    !pip install langchain_community
    %pip install Pillow

- **Frontend:** http://localhost:8501

- **Backend (API docs):**https://docs.csiamerica.com/help-files/etabs-api-2016/html/6a9c8a48-232d-761c-5421-1ff5ae019a4c.htm
# 🔗 Usage
1️⃣ Upload architectural drawings or input structural data.<br>
2️⃣ Select building parameters (grids, levels, loads).<br>
3️⃣ Click "Run Automation" to create ETABS models programmatically.<br>
4️⃣ Review logs and download ETABS .EDB files.

# 📡 API Endpoints
- `GET /health:` Health check.

- `POST /run_etabs:` Automates model generation.

- `POST /parse_geometry:` Parses raw geometry data.

- `POST /vision_extract:` Extracts geometry from images.*

# ⚙️ Future Work
- Add automatic structural analysis reports.

- Integrate reinforcement detailing modules.

- Extend LLM vision to interpret scanned PDFs.

- Deploy as a web service for multi-user teams.

**This project demonstrates how powerful results can be achieved by integrating LLMs, Python, ETABS API, vision modules, and a modern UI into one automated workflow for dynamic structural design.

If you want, I can package this into a README.md or a project proposal PDF — just say yes. 🚀📐**

