'''
Created By : Christian Merriman
Date : 3/2/26

Purpose : To create a asic backend for creating flux .1 images. This will communicate with the frontend via fastapi.


'''
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from flux_image_creation import *
from fastapi.staticfiles import StaticFiles
import os
import uvicorn

#global variables
COMFYUI_DIRECTORY_OUTPUT = "C:\\Programming 1\\2025 New PC\\Python\\ComfyUI\\ComfyUI\\output"
DIRECTORY_OUTPUT_FLUX = "fastapi_flux_images"

app = FastAPI()

# Mount it so http://localhost:8000/images/ refers to that folder
app.mount("/images", StaticFiles(directory=os.path.join(COMFYUI_DIRECTORY_OUTPUT, DIRECTORY_OUTPUT_FLUX)), name="flux_images")

# Enable CORS so your frontend can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data model for the incoming prompt
class PromptRequest(BaseModel):
    prompt: str

# Data model for the response
class ImageResponse(BaseModel):
    status: str
    image_url: Optional[str] = None
    detail: Optional[str] = None

#handles creating the flux .1 image. will either return the image created or an error
async def process_flux_image(prompt: str):
    #check for prompt
    if not prompt or prompt.isspace():
        return {"success": False, "error": "No text prompt sent in."}

    #create our flux image object
    fluximage = Flux_Image()

    try:
        #create our flux image
        image_path = await fluximage.create_flux_kontext_image(prompt_for_flux=prompt)
        
        #make sure we have an image
        if image_path == "":
            return {"success": False, "error": "Flux model timed out or failed."}

        #setup filename for frontend
        filename = os.path.basename(image_path)

        # Return the web friendly URL
        return {
            "success": True, 
            "url": f"/images/{filename}" 
        }
    
    except Exception as e:
        # This catches any unexpected errors and reports them to the frontend
        return {"success": False, "error": f"Internal Server Error: {str(e)}"}

#receives the post to create a flux .1 image
@app.post("/generate", response_model=ImageResponse)
async def generate_image(request: PromptRequest):
    try:
        # 1. Notify start (Logged in terminal)
        print(f"Received prompt: {request.prompt}")
        
        # 2. Call your Flux function
        result = await process_flux_image(request.prompt)
        
        # 3. Handle the result
        if result["success"]:
            return ImageResponse(status="success", image_url=result["url"])
        else:
            return ImageResponse(status="failed", detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add this above your /generate route
@app.get("/health")
async def health_check():
    return {"status": "online"} 

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)