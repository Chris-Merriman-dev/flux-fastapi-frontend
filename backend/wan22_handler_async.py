'''
Purpose to handle calls to comfyui for wan and flux.

Updated this for some methods being async.
'''

import requests
import json
import os
import time
from moviepy import *
import random
import psutil
import signal
import subprocess
import asyncio

COMFYUI_DIRECTORY_MAIN = "C:\\Programming 1\\2025 New PC\\Python\\ComfyUI\\ComfyUI"
COMFYUI_DIRECTORY_OUTPUT = "C:\\Programming 1\\2025 New PC\\Python\\ComfyUI\\ComfyUI\\output"
COMFYUI_DIRECTORY_INPUT = "C:\\Programming 1\\2025 New PC\\Python\\ComfyUI\\ComfyUI\\input"
COMFYUI_URL = "http://localhost:8188"

class Wan22_Handler():

    def __init__(self, image_count, file_name, file_name_enchanced, width, height, batchsize, image_filename, savedirectory, image_reference):
        self.image_counter = image_count
        self.main_file_name = file_name
        self.main_file_name_enchanced = file_name_enchanced
        self.video_width = width
        self.video_height = height
        self.batch_size = batchsize
        self.image_file_name = image_filename
        self.save_directory = savedirectory
        self.image_reference_filename = image_reference

    def restart_comfyui_server(start_command=["python", "main.py"], working_dir=COMFYUI_DIRECTORY_MAIN, check_url="http://localhost:8188/ping", timeout=120):
        try:
            print("Searching for ComfyUI process...")
            comfyui_pid = None
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info.get('cmdline')
                if cmdline and "main.py" in cmdline:
                    comfyui_pid = proc.info['pid']
                    break

            if comfyui_pid:
                print(f"Stopping ComfyUI (PID {comfyui_pid})...")
                proc = psutil.Process(comfyui_pid)
                proc.terminate()
                proc.wait(timeout=10)
            else:
                print("ComfyUI process not found. Proceeding to start fresh.")

            print("Restarting ComfyUI...")
            # Make sure this is a list of strings
            start_command = ["python", "main.py"]
            subprocess.Popen(start_command, cwd=working_dir)
            print("Waiting for server to come back online...")

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    ping = requests.get(check_url)
                    if ping.status_code == 200:
                        print("Server is back online.")
                        return True
                except requests.exceptions.ConnectionError:
                    pass
                time.sleep(2)

            print("Timeout: Server did not come back online within expected time.")
            return False

        except Exception as e:
            print("Error during restart:", e)
            return False

    async def open_workflow(self, workflow_path):
        # Load the exported API-ready workflow
        with open(workflow_path, "r", encoding="utf-8") as f:
            self.raw_workflow = json.load(f)

    #creates directory for main video and enhanced video
    def create_directories_with_direct(self, direct = ""):
        #our main output directory, our new directory and the new created number directory
        main_direct = f"{self.save_directory}\\{direct}"

        # Ensure the main directory exists
        os.makedirs(main_direct, exist_ok=True)

        # Start checking from 0 upwards
        i = 0
        while True:
            new_dir_path = os.path.join(main_direct, str(i))
            if not os.path.exists(new_dir_path):
                os.makedirs(new_dir_path)
                print(f"Created directory: {new_dir_path}")
                self.new_dir_path = new_dir_path
                #update save directory
                self.save_directory = os.path.join(self.save_directory, direct, str(i))
                break
            i += 1


    #creates directory for main video and enhanced video
    def create_directories(self, direct = ""):
        #our main output directory, our new directory and the new created number directory
        main_direct = f"{COMFYUI_DIRECTORY_OUTPUT}\\{self.save_directory}\\{direct}"

        # Ensure the main directory exists
        os.makedirs(main_direct, exist_ok=True)

        # Start checking from 0 upwards
        i = 0
        while True:
            new_dir_path = os.path.join(main_direct, str(i))
            if not os.path.exists(new_dir_path):
                os.makedirs(new_dir_path)
                print(f"Created directory: {new_dir_path}")
                self.new_dir_path = new_dir_path
                #update save directory
                self.save_directory = os.path.join(self.save_directory, direct, str(i))
                break
            i += 1

    #this will use values sent in and also values already set
    #THIS IS USED FOR A VERY SPECIFIC WORKFLOW RIGHT NOW
    def update_workflow_fluxschnell_by_step(self, 
                        step : int,
                        positive_prompt = "", 
                        negative_prompt = "",
                        seed = None,
                        image_file = "",
                        filename_prefix = "",
                        filename_prefix_enchanced = ""):
        
        #print("🧾 Original workflow:")
        #print(json.dumps(self.raw_workflow, indent=2))

        # Generate the random seed INSIDE the function
        if seed is None:
            seed = random.randint(0, 18446744073709551615)
            print(f"🎲 Fresh Seed Generated: {seed}")
                
        #set our variables if new ones not sent in
        if image_file == "":
            image_file = self.image_file_name
        
        if filename_prefix == "":
            filename_prefix = f"{self.save_directory}\\{self.main_file_name}{self.image_counter}"

        if filename_prefix_enchanced == "":
            filename_prefix_enchanced = f"{self.save_directory}\\{self.main_file_name_enchanced}{self.image_counter}"

        # Inject new prompts, image paths, and settings safely
        for node_id, node in self.raw_workflow.items():
            if isinstance(node, dict) and "class_type" in node and "inputs" in node:
                class_type = node["class_type"]
                title = node.get("_meta", {}).get("title", "")

                if step == 1 :
                    # Prompts
                    if class_type == "CLIPTextEncode":
                        if "Positive Prompt" in title:
                            node["inputs"]["text"] = positive_prompt

                    # Inject random seed
                    elif class_type == "KSampler":
                        seed = seed
                        node["inputs"]["seed"] = seed
                        print(f"🎲 Injected seed: {seed}")

                    # Load Image
                    #elif class_type == "LoadImage":
                    #    if "First Frame" in title or "Main Image" in title:
                    #        node["inputs"]["image"] = image_file

                    # SaveVideo filename
                    elif "Save Image" in title:
                        node["inputs"]["filename_prefix"] = filename_prefix
                        print(f"📝 Updated filename prefix: {filename_prefix}")

                    # Dimensions and batch size for WAN
                    #elif class_type == "EmptySD3LatentImage":
                    #    if "width" in node["inputs"]:
                    #        node["inputs"]["width"] = self.video_width
                    #    if "height" in node["inputs"]:
                    #        node["inputs"]["height"] = self.video_height
                    #    if "batch_size" in node["inputs"]:
                    #        node["inputs"]["batch_size"] = self.batch_size
                elif step == 2:
                    # Prompts
                    if class_type == "CLIPTextEncode":
                        if "Positive Prompt" in title:
                            node["inputs"]["text"] = positive_prompt

                    # Inject random seed
                    elif class_type == "KSampler":
                        seed = seed
                        node["inputs"]["seed"] = seed
                        print(f"🎲 Injected seed: {seed}")

                    # Load Image
                    elif class_type == "LoadImageOutput":
                        if "Load Image 1" in title:
                            node["inputs"]["image"] = image_file

                    # SaveVideo filename
                    elif "Save Image" in title:
                        node["inputs"]["filename_prefix"] = filename_prefix
                        print(f"📝 Updated filename prefix: {filename_prefix}")

                # Dimensions and batch size for WAN
                #    elif class_type == "EmptySD3LatentImage":
                #        if "width" in node["inputs"]:
                #            node["inputs"]["width"] = self.video_width
                #        if "height" in node["inputs"]:
                #            node["inputs"]["height"] = self.video_height
                #        if "batch_size" in node["inputs"]:
                #            node["inputs"]["batch_size"] = self.batch_size
                elif step == 3:
                   

                    # Load Image
                    if class_type == "LoadImage":
                        if "Set Reference Image" in title:
                            node["inputs"]["image"] = image_file

                    # SaveVideo filename
                    elif "Save Image" in title:
                        node["inputs"]["filename_prefix"] = filename_prefix
                        print(f"📝 Updated filename prefix: {filename_prefix}")

                elif step == 999999:
                    # Prompts
                    if class_type == "CLIPTextEncode":
                        if "Positive Prompt" in title:
                            node["inputs"]["text"] = positive_prompt

                    # Inject random seed
                    elif class_type == "KSampler":
                        seed = seed
                        node["inputs"]["seed"] = seed
                        print(f"🎲 Injected seed: {seed}")

                    # Load Image
                    #elif class_type == "LoadImage":
                    #    if "First Frame" in title or "Main Image" in title:
                    #        node["inputs"]["image"] = image_file

                    # SaveVideo filename
                    elif "Save Image" in title:
                        node["inputs"]["filename_prefix"] = filename_prefix
                        print(f"📝 Updated filename prefix: {filename_prefix}")

                # Dimensions and batch size for WAN
                    elif class_type == "EmptySD3LatentImage":
                        if "width" in node["inputs"]:
                            node["inputs"]["width"] = self.video_width
                        if "height" in node["inputs"]:
                            node["inputs"]["height"] = self.video_height
                        if "batch_size" in node["inputs"]:
                            node["inputs"]["batch_size"] = self.batch_size

 
        #print("🛠️ Updated workflow:")
        #print(json.dumps(self.raw_workflow, indent=2))

    #this will use values sent in and also values already set
    #THIS IS USED FOR A VERY SPECIFIC WORKFLOW RIGHT NOW
    async def update_workflow_fluxs_kontext(self, 
                        positive_prompt = "", 
                        negative_prompt = "",
                        seed = None,
                        image_file = "",
                        filename_prefix = "",
                        filename_prefix_enchanced = "",
                        kontext_image1 = "",
                        kontext_image2 = ""):
        
        # Generate the random seed INSIDE the function
        if seed is None:
            seed = random.randint(0, 18446744073709551615)
            print(f"🎲 Fresh Seed Generated: {seed}")
            
        #print("🧾 Original workflow:")
        #print(json.dumps(self.raw_workflow, indent=2))
                
        #set our variables if new ones not sent in
        if image_file == "":
            image_file = self.image_file_name
        
        if filename_prefix == "":
            filename_prefix = f"{self.save_directory}\\{self.main_file_name}{self.image_counter}"

        if filename_prefix_enchanced == "":
            filename_prefix_enchanced = f"{self.save_directory}\\{self.main_file_name_enchanced}{self.image_counter}"

        # Inject new prompts, image paths, and settings safely
        for node_id, node in self.raw_workflow.items():
            if isinstance(node, dict) and "class_type" in node and "inputs" in node:
                class_type = node["class_type"]
                title = node.get("_meta", {}).get("title", "")

                # Prompts
                if class_type == "CLIPTextEncode":
                    if "Positive Prompt" in title:
                        node["inputs"]["text"] = positive_prompt

                # Inject random seed
                elif class_type == "KSampler":
                    seed = seed
                    node["inputs"]["seed"] = seed
                    print(f"🎲 Injected seed: {seed}")

                # Load Image
                elif class_type == "LoadImage":
                    if "Image1" in title:
                        node["inputs"]["image"] = kontext_image1
                    elif "Image2" in title:
                        node["inputs"]["image"] = kontext_image2
                        #check to see if we have an image
                        #if kontext_image2:
                        #    node["inputs"]["image"] = kontext_image2
                        #    node["mode"] = 0  # 0 = Always (Active)
                        #else:
                        #    # If no image is provided, bypass the node
                        #    node["mode"] = 4  # 4 = Bypass

                # SaveVideo filename
                elif "Save Image" in title:
                    node["inputs"]["filename_prefix"] = filename_prefix
                    print(f"📝 Updated filename prefix: {filename_prefix}")

               # Dimensions and batch size for WAN
                elif class_type == "EmptySD3LatentImage":
                    if "width" in node["inputs"]:
                        node["inputs"]["width"] = self.video_width
                    if "height" in node["inputs"]:
                        node["inputs"]["height"] = self.video_height
                    if "batch_size" in node["inputs"]:
                        node["inputs"]["batch_size"] = self.batch_size

 
        #print("🛠️ Updated workflow:")
        #print(json.dumps(self.raw_workflow, indent=2))



    #this will use values sent in and also values already set
    #THIS IS USED FOR A VERY SPECIFIC WORKFLOW RIGHT NOW
    async def update_workflow_fluxschnell(self, 
                        positive_prompt = "", 
                        negative_prompt = "",
                        seed = None,
                        image_file = "",
                        filename_prefix = "",
                        filename_prefix_enchanced = ""):
        
        #print("🧾 Original workflow:")
        #print(json.dumps(self.raw_workflow, indent=2))

        # Generate the random seed INSIDE the function
        if seed is None:
            seed = random.randint(0, 18446744073709551615)
            print(f"🎲 Fresh Seed Generated: {seed}")
                
        #set our variables if new ones not sent in
        if image_file == "":
            image_file = self.image_file_name
        
        if filename_prefix == "":
            filename_prefix = f"{self.save_directory}\\{self.main_file_name}{self.image_counter}"

        if filename_prefix_enchanced == "":
            filename_prefix_enchanced = f"{self.save_directory}\\{self.main_file_name_enchanced}{self.image_counter}"

        # Inject new prompts, image paths, and settings safely
        for node_id, node in self.raw_workflow.items():
            if isinstance(node, dict) and "class_type" in node and "inputs" in node:
                class_type = node["class_type"]
                title = node.get("_meta", {}).get("title", "")

                # Prompts
                if class_type == "CLIPTextEncode":
                    if "Positive Prompt" in title:
                        node["inputs"]["text"] = positive_prompt

                # Inject random seed
                elif class_type == "KSampler":
                    seed = seed
                    node["inputs"]["seed"] = seed
                    print(f"🎲 Injected seed: {seed}")

                # Load Image
                #elif class_type == "LoadImage":
                #    if "First Frame" in title or "Main Image" in title:
                #        node["inputs"]["image"] = image_file

                # SaveVideo filename
                elif "Save Image" in title:
                    node["inputs"]["filename_prefix"] = filename_prefix
                    print(f"📝 Updated filename prefix: {filename_prefix}")

               # Dimensions and batch size for WAN
                elif class_type == "EmptySD3LatentImage":
                    if "width" in node["inputs"]:
                        node["inputs"]["width"] = self.video_width
                    if "height" in node["inputs"]:
                        node["inputs"]["height"] = self.video_height
                    if "batch_size" in node["inputs"]:
                        node["inputs"]["batch_size"] = self.batch_size

 
        #print("🛠️ Updated workflow:")
        #print(json.dumps(self.raw_workflow, indent=2))

    #this will use values sent in and also values already set
    #THIS IS USED FOR A VERY SPECIFIC WORKFLOW RIGHT NOW
    def update_workflow_for_voice(self, 
                        positive_prompt = "", 
                        negative_prompt = "",
                        noise_seed = None,
                        image_file = "",
                        filename_prefix = "",
                        filename_prefix_enchanced = "",
                        image_ref = "",
                        audio_file = ""):
        
        # Generate the random seed INSIDE the function
        if seed is None:
            seed = random.randint(0, 18446744073709551615)
            print(f"🎲 Fresh Seed Generated: {seed}")
                
        #set our variables if new ones not sent in
        if image_file == "":
            image_file = self.image_file_name
        
        if filename_prefix == "":
            filename_prefix = f"{self.save_directory}\\{self.main_file_name}{self.image_counter}"

        if filename_prefix_enchanced == "":
            filename_prefix_enchanced = f"{self.save_directory}\\{self.main_file_name_enchanced}{self.image_counter}"

        if image_ref == "":
            image_ref = self.image_reference_filename

        # Inject new prompts, image paths, and settings safely
        for node_id, node in self.raw_workflow.items():
            if isinstance(node, dict) and "class_type" in node and "inputs" in node:
                class_type = node["class_type"]
                title = node.get("_meta", {}).get("title", "")

                # Prompts
                if class_type == "CLIPTextEncode":
                    if "Positive Prompt" in title:
                        node["inputs"]["text"] = positive_prompt

                # Inject random seed
                elif class_type == "KSampler" and "KSampler (First)" in title:
                    seed = noise_seed
                    node["inputs"]["noise_seed"] = seed
                    print(f"🎲 Injected noise_seed: {seed}")

                # Load Audio
                elif class_type == "LoadAudio":
                    if "First" in title or "Main" in title:
                        node["inputs"]["audio"] = audio_file

                # Load Image
                elif class_type == "LoadImage":
                    if "First Frame" in title or "Main Image" in title:
                        node["inputs"]["image"] = image_file

                # Load Image Reference
                elif class_type == "LoadImageFromPath":
                    if "Load_Image_From_Path1" in title:
                        node["inputs"]["image"] = image_ref

                # SaveVideo filename
                elif class_type == "SaveVideo":
                    node["inputs"]["filename_prefix"] = filename_prefix
                    print(f"📝 Updated filename prefix: {filename_prefix}")

                #VHS_VideoCombine
                elif class_type == "VHS_VideoCombine":
                    node["inputs"]["filename_prefix"] = filename_prefix_enchanced
                    print(f"📝 Updated filename prefix: {filename_prefix_enchanced}")

                # Dimensions and batch size for WAN
                elif class_type == "WanSoundImageToVideo":
                    if "width" in node["inputs"]:
                        node["inputs"]["width"] = self.video_width
                    if "height" in node["inputs"]:
                        node["inputs"]["height"] = self.video_height
                    if "batch_size" in node["inputs"]:
                        node["inputs"]["batch_size"] = self.batch_size

    #this will use values sent in and also values already set
    #THIS IS USED FOR A VERY SPECIFIC WORKFLOW RIGHT NOW
    def update_workflow_for_firstimage_to_lastimage(self, 
                        last_image_file,
                        positive_prompt = "", 
                        negative_prompt = "",
                        noise_seed = None,
                        image_file = "",
                        filename_prefix = "",
                        filename_prefix_enchanced = "",
                        image_ref = ""):
        
        # Generate the random seed INSIDE the function
        if noise_seed is None:
            noise_seed = random.randint(0, 18446744073709551615)
            print(f"🎲 Fresh Seed Generated: {noise_seed}")
                
        #set our variables if new ones not sent in
        if image_file == "":
            image_file = self.image_file_name
        
        if filename_prefix == "":
            filename_prefix = f"{self.save_directory}\\{self.main_file_name}{self.image_counter}"

        if filename_prefix_enchanced == "":
            filename_prefix_enchanced = f"{self.save_directory}\\{self.main_file_name_enchanced}{self.image_counter}"

        if image_ref == "":
            image_ref = self.image_reference_filename

        # Inject new prompts, image paths, and settings safely
        for node_id, node in self.raw_workflow.items():
            if isinstance(node, dict) and "class_type" in node and "inputs" in node:
                class_type = node["class_type"]
                title = node.get("_meta", {}).get("title", "")

                # Prompts
                if class_type == "CLIPTextEncode":
                    if "Positive Prompt" in title:
                        node["inputs"]["text"] = positive_prompt

                # Inject random seed
                elif class_type == "KSamplerAdvanced" and "KSampler (Advanced) (First)" in title:
                    seed = noise_seed
                    node["inputs"]["noise_seed"] = seed
                    print(f"🎲 Injected noise_seed: {seed}")

                # Load Image Start and End Image
                elif class_type == "LoadImage":
                    if "First" in title:
                        node["inputs"]["image"] = image_file
                    elif "Last" in title:
                        node["inputs"]["image"] = last_image_file

                # Load Image Reference
                elif class_type == "LoadImageFromPath":
                    if "Load_Image_From_Path1" in title:
                        node["inputs"]["image"] = image_ref

                # SaveVideo filename
                elif class_type == "SaveVideo":
                    node["inputs"]["filename_prefix"] = filename_prefix
                    print(f"📝 Updated filename prefix: {filename_prefix}")

                #VHS_VideoCombine
                elif class_type == "VHS_VideoCombine":
                    node["inputs"]["filename_prefix"] = filename_prefix_enchanced
                    print(f"📝 Updated filename prefix: {filename_prefix_enchanced}")

                # Dimensions and batch size for WanFirstLastFrameToVideo
                elif class_type == "WanFirstLastFrameToVideo":
                    if "width" in node["inputs"]:
                        node["inputs"]["width"] = self.video_width
                    if "height" in node["inputs"]:
                        node["inputs"]["height"] = self.video_height
                    if "batch_size" in node["inputs"]:
                        node["inputs"]["batch_size"] = self.batch_size

                #



    #this will use values sent in and also values already set
    #THIS IS USED FOR A VERY SPECIFIC WORKFLOW RIGHT NOW
    def update_workflow(self, 
                        positive_prompt = "", 
                        negative_prompt = "",
                        noise_seed = None,
                        image_file = "",
                        filename_prefix = "",
                        filename_prefix_enchanced = "",
                        image_ref = "",
                        time_length = 0):
        
        # Generate the random seed INSIDE the function
        if noise_seed is None:
            noise_seed = random.randint(0, 18446744073709551615)
            print(f"🎲 Fresh Seed Generated: {noise_seed}")
                
        #set our variables if new ones not sent in
        if image_file == "":
            image_file = self.image_file_name
        
        if filename_prefix == "":
            filename_prefix = f"{self.save_directory}\\{self.main_file_name}{self.image_counter}"

        if filename_prefix_enchanced == "":
            filename_prefix_enchanced = f"{self.save_directory}\\{self.main_file_name_enchanced}{self.image_counter}"

        if image_ref == "":
            image_ref = self.image_reference_filename

        # Inject new prompts, image paths, and settings safely
        for node_id, node in self.raw_workflow.items():
            if isinstance(node, dict) and "class_type" in node and "inputs" in node:
                class_type = node["class_type"]
                title = node.get("_meta", {}).get("title", "")

                # Prompts
                if class_type == "CLIPTextEncode":
                    if "Positive Prompt" in title:
                        node["inputs"]["text"] = positive_prompt

                # Inject random seed
                elif class_type == "KSamplerAdvanced" and "KSampler (Advanced) (First)" in title:
                    seed = noise_seed
                    node["inputs"]["noise_seed"] = seed
                    print(f"🎲 Injected noise_seed: {seed}")

                # Load Image
                elif class_type == "LoadImage":
                    if "First Frame" in title or "Main Image" in title:
                        node["inputs"]["image"] = image_file

                # Load Image Reference
                elif class_type == "LoadImageFromPath":
                    if "Load_Image_From_Path1" in title:
                        node["inputs"]["image"] = image_ref

                # SaveVideo filename
                elif class_type == "SaveVideo":
                    node["inputs"]["filename_prefix"] = filename_prefix
                    print(f"📝 Updated filename prefix: {filename_prefix}")

                #VHS_VideoCombine
                elif class_type == "VHS_VideoCombine":
                    node["inputs"]["filename_prefix"] = filename_prefix_enchanced
                    print(f"📝 Updated filename prefix: {filename_prefix_enchanced}")

                # Dimensions and batch size for WAN
                elif class_type == "WanImageToVideo":
                    if "width" in node["inputs"]:
                        node["inputs"]["width"] = self.video_width
                    if "height" in node["inputs"]:
                        node["inputs"]["height"] = self.video_height
                    if "batch_size" in node["inputs"]:
                        node["inputs"]["batch_size"] = self.batch_size
                    if time_length > 0 and "length" in node["inputs"]:
                        #if we entered a length, it wont be 5 second default
                        #so we take out int length and times it by 16 fps (default wan fps)
                        #then we add the 1 extra frame as needed
                        node["inputs"]["length"] = (time_length * 16) + 1

    async def send_wrapped_workflow(self):
        # Wrap and send
        self.wrapped_workflow = {"prompt": self.raw_workflow}
        response = requests.post(f"{COMFYUI_URL}/prompt", json=self.wrapped_workflow)

        print("📡 Status code:", response.status_code)

        try:
            response_data = response.json()
            print("🧾 Response:", response_data)
            self.prompt_id = response_data.get("prompt_id")
            print(f"🆔 Prompt ID: {self.prompt_id}")
        except requests.exceptions.JSONDecodeError:
            print("⚠️ No JSON response received.")
            print("📄 Raw response:", response.text)
            self.prompt_id = None

    async def wait_for_completion(self, prompt_id, timeout=15000, interval=10):
        elapsed = 0
        while elapsed < timeout:
            try:
                status_response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
                if status_response.status_code == 200:
                    raw_data = status_response.json()
                    status_data = raw_data.get(prompt_id, {})
                    outputs = status_data.get("outputs", {})
                    status_info = status_data.get("status", {})
                    messages = status_info.get("messages", [])

                    # 🧭 Live status messages
                    for msg_type, msg_content in messages:
                        timestamp = msg_content.get("timestamp")
                        print(f"📡 Status: {msg_type} at {timestamp}")

                    # ✅ Completion check
                    if status_info.get("completed") and outputs:
                        print("✅ Workflow completed!")
                        return outputs
                else:
                    print(f"⚠️ Status check failed: {status_response.status_code}")
            except Exception as e:
                print(f"🚨 Error during status check: {e}")
            
            print(f"⏳ Waiting... elapsed: {elapsed}s")
            #time.sleep(interval)
            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError("⏳ Workflow did not complete within the timeout window.")

    def find_all_video_outputs(self, outputs):
        video_files = []
        for node_id, result in outputs.items():
            for key in ["images", "gifs", "animated"]:
                if key in result:
                    for item in result[key]:
                        if isinstance(item, dict) and item.get("filename", "").endswith(".mp4"):
                            video_files.append(item)
        return video_files

    def track_response(self, with_audio = False):
        video_path = ""
        # 🧾 Track and retrieve output
        if self.prompt_id:
            try:
                outputs = self.wait_for_completion(self.prompt_id)
                video_outputs = self.find_all_video_outputs(outputs)

                if video_outputs:
                    for item in video_outputs:
                        filename = item["filename"]
                        subfolder = item.get("subfolder", "")
                        output_type = item.get("type", "output")
                        #full_path = os.path.abspath(os.path.join("ComfyUI", output_type, subfolder, filename))
                        full_path = os.path.join(COMFYUI_DIRECTORY_MAIN, output_type, subfolder, filename)
                        print(f"🎬 Found video: {full_path}")
                        
                        #if self.main_file_name in full_path:

                        if with_audio:
                            if self.main_file_name_enchanced in full_path and '-audio' in full_path:                         
                                video_path = full_path
                        else:
                            if self.main_file_name_enchanced in full_path:                        
                                video_path = full_path

                else:
                    print("⚠️ No MP4 videos found in outputs.")
            except TimeoutError as e:
                print(str(e))

            return video_path


##new stuff
    def generate_flux_schnell_image(self, flux_prompt, negative_prompt=""):

        # Step 1: Update workflow with externally provided prompt
        self.update_workflow_fluxschnell(
            positive_prompt=flux_prompt,
            negative_prompt=negative_prompt
        )

        # Step 2: Send workflow to ComfyUI
        self.send_wrapped_workflow()

        # Step 3: Wait for image generation and return path
        image_path = self.track_image_response()
        return image_path


    async def find_all_image_outputs(self, outputs):
        image_files = []
        for node_id, result in outputs.items():
            for key in ["images"]:
                if key in result:
                    for item in result[key]:
                        if isinstance(item, dict) and item.get("filename", "").lower().endswith((".png", ".jpg", ".jpeg")):
                            image_files.append(item)
        return image_files


    async def track_image_response(self):
        image_paths = []
        image_path = ""
        if self.prompt_id:
            try:
                outputs = await self.wait_for_completion(self.prompt_id)
                image_outputs = await self.find_all_image_outputs(outputs)

                if image_outputs:
                    for item in image_outputs:
                        filename = item["filename"]
                        subfolder = item.get("subfolder", "")
                        output_type = item.get("type", "output")
                        full_path = os.path.join(COMFYUI_DIRECTORY_MAIN, output_type, subfolder, filename)
                        print(f"🖼️ Found image: {full_path}")

                        #if self.main_file_name in full_path:
                        image_path = full_path
                        image_paths.append(image_path)
                else:
                    print("⚠️ No images found in outputs.")
            except TimeoutError as e:
                print(str(e))

        return image_paths
    
    #just wait for a response for it to be done running the free mem
    def track_freemem_response(self):

        if self.prompt_id:
            try:
                outputs = self.wait_for_completion(self.prompt_id)
                
            except TimeoutError as e:
                print(str(e))

