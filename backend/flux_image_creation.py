"""

Purpose : Used to create Flux Image

"""
import time
from wan22_handler_async import Wan22_Handler
import os
import gc
import asyncio

####################
# Directories
####################
COMFYUI_URL = "http://localhost:8188"
COMFYUI_DIRECTORY_OUTPUT = "C:\\Programming 1\\2025 New PC\\Python\\ComfyUI\\ComfyUI\\output"
DIRECTORY_OUTPUT_STORY = "fastapi_flux_images"
#input path
COMFYUI_INPUT_PATH = "C:/Programming 1/2025 New PC/Python/ComfyUI/ComfyUI/input"
FILES_DIRECTORY = "files"

####################
# File Names
####################

WORKFLOW_FLUX_NO_IMAGE_FILE1 = "Flux_No_Image_APP_1_API_1.json"
WORKFLOW_FREEMEM = "free_mem_API_1.json"
MAIN_FILE_NAME = "Video_Normal"
MAIN_FILE_NAME_ENHANCED = "Video_Enhanced"
MAIN_FLUX_FILENAME = "Flux_img"
IMAGE_FILE = ""

####################
# Variables
####################

UPSCALE_IMAGES = False  #if we will upscale images
IMAGE_COUNTER = 1
IMAGE_COUNTER_HIGH = 100000


FLUX_WIDTH = 1280
FLUX_HEIGHT = 720

WIDTH = 896
HEIGHT = 512

#WIDTH = 1024
#HEIGHT = 1024

#WIDTH = 512
#HEIGHT = 896

BATCH_SIZE = 1
FLUX_BATCH_SIZE = 1

VIDEO_FPS = 24

class Flux_Image:
    def __init__(self):
        pass

    #you need to send in at least 1 kontext image to use this
    async def create_fluxschnell_kontext_images_with_directory(self, prompt : str, filename, in_directory : str, workflow : str, kontext_workflow : bool, kontext_image_1 : str = "", kontext_image_2 = "", batchsize : int = FLUX_BATCH_SIZE, image_to_use = ""):
        all_images = []
        #directory_num = 0

        #create our directory if we have a prompt and the workflow exists
        if prompt != "" and os.path.isfile(workflow):# and kontext_image_1 != "":
            #directory, directory_num = create_directory(in_directory)
            directory = in_directory
        else:
            print("Error! No flux positive prompt, workflow or kontext_image_1 sent in!")
            return all_images

        if directory == "":
            print('Error! No new directory created!')
            return all_images
        
        #set first image to use
        image_used = image_to_use

        #init wan var
        wan_handler = Wan22_Handler(IMAGE_COUNTER, 
                                    filename,
                                    f"{filename}_enchanced_",
                                    FLUX_WIDTH, 
                                    FLUX_HEIGHT, 
                                    batchsize, 
                                    image_used, 
                                    in_directory,
                                    IMAGE_FILE)
        
        #get workflow and update it
        await wan_handler.open_workflow(workflow)

        #make our directory for this
        #wan_handler.create_directories_with_direct(str(directory_num))

        #check to see if kontext workflow or not
        if kontext_workflow:
            await wan_handler.update_workflow_fluxs_kontext(positive_prompt=prompt, kontext_image1= kontext_image_1, kontext_image2=kontext_image_2)
        #no kontext image, just normal flux image prompt
        else:
            await wan_handler.update_workflow_fluxschnell(positive_prompt=prompt)
        
        #wan_handler.update_workflow_fluxschnell_by_step(step=step, positive_prompt=prompt)        

        #now wrap and send
        await wan_handler.send_wrapped_workflow()

        #now wait for response
        all_images = await wan_handler.track_image_response()

        #free from memory
        # This removes the reference, but memory isn't "free" yet
        del wan_handler

        # 3. Force Python to find and clear the deleted object
        gc.collect()

        return all_images
    
    async def comfyui_freemem(self, workflow : str):
        print('\n\nFreeing up VRAM with ComfyUI!')
        #init wan var
        wan_handler = Wan22_Handler(IMAGE_COUNTER, 
                                    '',
                                    f"{''}_enchanced_",
                                    FLUX_WIDTH, 
                                    FLUX_HEIGHT, 
                                    0, 
                                    '', 
                                    '',
                                    IMAGE_FILE)
        
        #get workflow and update it
        await wan_handler.open_workflow(workflow)

        #now wrap and send
        await wan_handler.send_wrapped_workflow()

        #wait for response
        #wan_handler.track_freemem_response()

        #time.sleep(10)
        await asyncio.sleep(10)

        #free from memory
        # This removes the reference, but memory isn't "free" yet
        del wan_handler

        # 3. Force Python to find and clear the deleted object
        gc.collect()

        #sleep for catchup
        #time.sleep(2)
        await asyncio.sleep(2)

        print('\n\nCOMFYUI Free Mem Completed!\n\n')

    #this will keep going until it finds the best image possible for our workflow, prompt and kontext images.
    #send in the prompt, workflow to use, if it uses kontext images, kontext image1, kontext image2
    async def create_flux_kontext_image(self, prompt_for_flux : str, workflow : str = os.path.join(FILES_DIRECTORY,WORKFLOW_FLUX_NO_IMAGE_FILE1), Kontext_Workflow : bool = False, kontext_image1 : str = "", kontext_image2 : str = "")->str:
        #final image to be returned
        image_used = ""

        #keep looping and creating flux images, until we get a good image to use for the video
        get_flux_image = True

        #create directory to use for story
        #print('\n\nCreating directory and saving data.\n\n')
        #main_direct, main_direct_num = create_directory(DIRECTORY_OUTPUT_STORY)
        main_direct = DIRECTORY_OUTPUT_STORY
        
        ##
        # only try so many times to get image
        ##
        image_loop_count = 0
        MAX_LOOP_COUNT = 3

        while get_flux_image:
            #create our images var
            images = []

            #create directory to use for story
            #print('\n\nCreating directory and saving data.\n\n')
            #main_direct, main_direct_num = create_directory(DIRECTORY_OUTPUT_STORY)

            #Create Flux Image
            images = await self.create_fluxschnell_kontext_images_with_directory(prompt=prompt_for_flux, 
                                                                    filename=MAIN_FLUX_FILENAME, 
                                                                    in_directory=main_direct,
                                                                    workflow=workflow,
                                                                    kontext_workflow=Kontext_Workflow,
                                                                    kontext_image_1=kontext_image1,
                                                                    kontext_image_2=kontext_image2,
                                                                    batchsize=FLUX_BATCH_SIZE
            )


            print(f"\n\nIMAGE CREATED : {images}\n\n")


            #CALL FUNCTION TO GET BEST IMAGE
            if len(images) > 0:
                image_used = images[0]
                get_flux_image = False         
            else:
                print('❌❌❌ ERROR! NO IMAGES FOUND! RETRYING!')
                if image_loop_count > MAX_LOOP_COUNT:
                    print('COULD NOT CREATE IMAGE!!!')
                    get_flux_image = False   

            #free mem
            await self.comfyui_freemem(os.path.join(FILES_DIRECTORY,WORKFLOW_FREEMEM))   

            image_loop_count = image_loop_count + 1

        #return our image
        return image_used
                
