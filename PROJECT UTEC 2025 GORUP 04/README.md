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
# ✅ Features

Full ETABS Automation: Programmatically creates grids, slabs, walls, columns, beams, and openings using the ETABS COM API.

LLM Integration: Uses Large Language Models for vision tasks (e.g., interpreting scanned structural drawings) and for language-based extraction of design data from technical documents.

Geometric Parsing: Converts extracted data into precise ETABS geometry.

Streamlit UI: Provides a simple and intuitive interface to define model parameters, upload input data, and launch automation.

Containerized: Uses Docker and Docker Compose for easy deployment and portability.

