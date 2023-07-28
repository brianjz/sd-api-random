# stable Diffusion random image generator

I just threw this together since sometimes I just wanted Stable Diffusion to automatically make a bunch of images pulled from a list of prompts.

## Setup
At minimum, you just need to set `DEFAULT_SAVE_PATH` and `DEFAULT_MODELS_DIR` inside the .py file. You need Stable Diffusion active with either 
[SD.Next](https://github.com/vladmandic/automatic) or [AUTOMATIC1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui) with the API running. Other 
UIs may work, but I mainly work with SD.Next.

## Usage
```
usage: sd-api-random.py [-h] [-f FILE] [-n NUM] [-r REPEAT] [-d DIMENSIONS] [-s STEPS] [-sp SAMPLER] [--saveprompt] [--keepmodel] [--usecurrent] [-noex]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Text file with list of prompts, one each line
  -n NUM, --num NUM     Number of images to generate per model
  -r REPEAT, --repeat REPEAT
                        Number of iterations of -num
  -d DIMENSIONS, --dimensions DIMENSIONS
                        Image dimensions WxH, defaults to 512x768
  -s STEPS, --steps STEPS
                        Number of steps, defaults to 30
  -sp SAMPLER, --sampler SAMPLER
                        Sampler, defaults to Euler a
  --saveprompt          Save the prompt to a separate text file in same directory
  --keepmodel           Don't roll back to initial model after completed
  --usecurrent          Use current loaded model, not random one
  -noex, --noextensions
                        Disable sending extension data [adetailer, etc]
```
