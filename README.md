# Flux .1 Image Generation Workbench

A lightweight, high-performance web interface designed to connect a custom frontend to a **FastAPI** backend, which serves as a bridge to **ComfyUI** for generating **Flux .1** images.

## 🚀 Project Overview

The goal of this application is to provide a professional-grade "control center" for Flux generation. It handles the complex communication with ComfyUI while offering a user-friendly interface for prompting, inspecting, and managing image history.

### Core Workflow
1. Frontend: User enters a prompt and hits "Generate".
2. Backend: FastAPI receives the request, translates it for ComfyUI, and monitors the generation progress.
3. Frontend: Once the image is ready, the UI displays the result, enables a high-res download, and adds it to the persistent history gallery.

## 🛠 Tech Stack

### Frontend
* **Web Standard:** HTML5, CSS3, Vanilla JavaScript (ES6+).
* **Key Features:** * **Advanced Modal:** Smooth mouse-wheel zoom and click-and-drag panning for detail inspection.
* **History Gallery:** A dedicated scrollbox to preview and swap between previous generations.
* **Live Status:** Real-time server health monitoring (Online/Busy/Offline).

### Backend
* **FastAPI:** Python-based API layer for ultra-fast request handling.
* **Uvicorn:** ASGI server for production-ready performance (Running internally via main.py).
* **ComfyUI Bridge:** Connects to ComfyUI's API/WebSocket to execute Flux workflows.

## 📋 Prerequisites

* **Python:** 3.12.8
* **ComfyUI:** Must be running locally (usually http://127.0.0.1:8188) or on a reachable server.
* **Model:** Flux .1 model weights properly configured in your ComfyUI environment.

## ⚙️ Setup & Installation

### 1. Backend Environment
Navigate to your project directory and set up a virtual environment to keep your dependencies isolated:

# Create the environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

### 2. Run the Server
The FastAPI backend is configured to run Uvicorn internally. Simply execute the main script to start the server:

# Command to run the server
python backend/main.py

### 3. Launch the Frontend
The frontend is built with vanilla web technologies. You can:
* Open index.html directly in your browser.
* Use a local development server like the "Live Server" extension in VS Code.

## 🖼 Project Architecture

1. **Browser (main.js):** Sends JSON payload (prompt) to the /generate endpoint.
2. **FastAPI (main.py):** Receives the request and forwards the instructions to the ComfyUI prompt queue.
3. **ComfyUI:** Processes the Flux .1 workflow and saves the resulting image to the output folder.
4. **FastAPI:** Sends the image URL/path back to the browser as a success response.
5. **Browser:** Updates the main display, reveals the Download High-Res button, and updates the history gallery.

## 📖 File Structure

* **frontend\index.html** - Main UI layout and structure  
* **frontend\styles.css** - Visual styling for the workbench, gallery, and modal  
* **frontend\main.js** - API calls, zoom/pan logic, and UI state management  
* **backend\main.py** - FastAPI server and ComfyUI integration bridge  
* **backend\flux_image_creation.py** - Handle the creation of flux images  
* **backend\wan22_handlers_async.py** - Handles calls to ComfyUI for flux image creation  
* **files\free_mem_API_1.json** - Json file used to communicate to ComfyUI to clear vram  
* **files\Flux_No_Image_APP_1_API_1.json** - Json file used to communicate to ComfyUI to create our Flux .1 image  
* **requirements.txt** - List of Python dependencies (fastapi, uvicorn, etc.)  
* **README.md** - Project documentation