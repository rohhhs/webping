import os
from PIL import Image
import subprocess
import argparse
import re

CURRENTPATH = r'C:\rohhs\scripts\python\convertors\webping' #setten by hands
CURRENTDIR = os.getcwd()
if CURRENTDIR != CURRENTPATH:
    CURRENTDIR = CURRENTPATH

SETTING = os.path.join(CURRENTPATH, 'setting.txt')

INPUTDIR = os.path.join(CURRENTDIR, 'input')
INPUTFILE = os.path.join(INPUTDIR, 'setting.txt')
IMAGESDIR = os.path.join(INPUTDIR, 'images')

OUTPUTDIR = os.path.join(CURRENTDIR, 'output')
OUTPUTFILE = os.path.join(OUTPUTDIR, 'response')

os.makedirs(OUTPUTDIR,exist_ok=True)

class WebPConverter:
    def __init__(self, height=None, width=None, quality=80, ext='.webp'):
        self.height = height
        self.width = width
        self.quality = quality

    def convert_to_webp(self, image_path, output_path):
        # Get the file extension
        ext = os.path.splitext(image_path)[1].lower()

        # Define supported extensions by PIL
        supported_by_pillow = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

        if ext in supported_by_pillow:
            try:
                # Open the image using Pillow
                with Image.open(image_path) as img:
                    original_width, original_height = img.size

                    # Resize the image if height and width are specified
                    if self.width and self.height:
                        img = img.resize((self.width, self.height), Image.LANCZOS)
                    elif self.width:
                        # Calculate height based on the aspect ratio
                        new_height = int((self.width / original_width) * original_height)
                        img = img.resize((self.width, new_height), Image.LANCZOS)
                    elif self.height:
                        # Calculate width based on the aspect ratio
                        new_width = int((self.height / original_height) * original_width)
                        img = img.resize((new_width, self.height), Image.LANCZOS)

                    # Save the image as .webp with the specified quality
                    img.save(output_path, 'webp', quality=self.quality)
                print(f"Converted {image_path} to {output_path} using Pillow")
            except Exception as e:
                print(f"Failed to convert {image_path} using Pillow: {e}")
                return
        else:
            try:
                # Prepare ffmpeg command with height, width, and quality if specified
                ffmpeg_command = ['ffmpeg', '-i', image_path, '-qscale:v', str(self.quality)]

                if self.width and self.height:
                    ffmpeg_command.extend(['-vf', f'scale={self.width}:{self.height}'])
                elif self.width:
                    ffmpeg_command.extend(['-vf', f'scale={self.width}:-1'])
                elif self.height:
                    ffmpeg_command.extend(['-vf', f'scale=-1:{self.height}'])

                ffmpeg_command.append(output_path)

                # Use ffmpeg for unsupported formats
                subprocess.run(ffmpeg_command, check=True)
                print(f"Converted {image_path} to {output_path} using ffmpeg")
            except subprocess.CalledProcessError as e:
                print(f"Failed to convert {image_path} using ffmpeg: {e}")
                return

if __name__ == "__main__":
    print ('works')
    converter = WebPConverter(height=1720, width=None, quality=90, ext='.webp')
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str)
    parser.add_argument('--output', type=str)

    args = parser.parse_args()
    if args.input:
        input = args.input
        if args.output:
            output = args.output
        else:
            number = 0
            for root, dirs, files in os.walk(OUTPUTDIR):
                for file in files:
                    number += 1
            output = os.path.join(OUTPUTDIR, f'image'+ number +'.webp')
        # WebPConverter.convert_to_webp(input, output)
        converter.convert_to_webp(input, output) # setten
    else:

        # print(INPUTDIR)
        # print(OUTPUTDIR)

        images = []

        for root, dirs, files in os.walk(INPUTDIR):
            for file in files:
                images.append(os.path.join(root, file))

        if len(images) != 0:
            for image in images:
                inputpath = image
                outputpath = os.path.join(OUTPUTDIR, os.path.relpath(inputpath, INPUTDIR))
                
                outputpath = outputpath.replace('/', '\\')

                last_slash_index = outputpath.rfind('\\')
                last_period_index = outputpath.rfind('.')

                outputdir = outputpath[:last_slash_index]
                os.makedirs(outputdir,exist_ok=True)

                outputpath = outputpath[:last_period_index] + '.webp'

                print (inputpath)
                print (outputpath)
                
                converter.convert_to_webp(inputpath, outputpath) #setten
                # WebPConverter.convert_to_webp(self, inputpath, outputpath)
        else:
            print ('No images specified')