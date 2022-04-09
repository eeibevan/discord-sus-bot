import logging

import numpy
from PIL import Image
import numpy as np
import subprocess
import os
import typing
import pathlib
import logging

# output_width = 21  # Width of output gif, measured in sussy crewmates
twerk_frame_count = 6  # 0.png to 5.png

# Load twerk frames 🥵
# Modification from the original,
# I changed the backgrounds of the images
# to be transparent
twerk_frames = []
twerk_frames_data = []  # Image as numpy array, pre-calculated for performance
for i in range(6):
    try:
        img = Image.open(f"twerk_imgs/{i}.png").convert("RGBA")
    except Exception as e:
        print(f"Error loading twerk frames! Filename = {i}.png")
        print("Probably you renamed the twerk_imgs folder or forgot to set twerk_frame_count. baka")
        print(e)
        exit()
    twerk_frames.append(img)
    twerk_frames_data.append(np.array(img))

# Get dimensions of first twerk frame. Assume all frames have same dimensions
twerk_width, twerk_height = twerk_frames[0].size

# Modification from the original,
# Generate a transparent frame to
# use for transparent pixels in the
# original image
transparent_frame = Image.new(mode='RGBA', size=twerk_frames[0].size, color=(0, 0, 0, 0))


def to_sus(fp: typing.BinaryIO, data_dir: pathlib.Path, nearest_neighbor: bool = False, output_width: int = 21):
    # Get image to sussify!

    # Modification from the original,
    # use a file object, instead of a fixed
    # file name
    input_image = Image.open(fp).convert("RGBA")
    input_width, input_height = input_image.size

    # Height of output gif (in crewmates)
    output_height = int(output_width * (input_height / input_width) * (twerk_width / twerk_height))

    # Width, height of output in pixels
    output_px = (int(output_width * twerk_width), int(output_height * twerk_height))

    # Scale image to number of crewmates, so each crewmate gets one color
    if nearest_neighbor:
        input_image_scaled = input_image.resize((output_width, output_height), Image.NEAREST)
    else:
        input_image_scaled = input_image.resize((output_width, output_height))

    for frame_number in range(twerk_frame_count):
        print("Sussying frame #", frame_number)

        # Create blank canvas
        background = Image.new(mode="RGBA", size=output_px)
        for y in range(output_height):
            for x in range(output_width):
                r, g, b, a = input_image_scaled.getpixel((x, y))

                # Modification from the original,
                # if a pixel is invisible, don't
                # put in a crew mate
                if a == 0:
                    background.paste(transparent_frame, (x * twerk_width, y * twerk_height))
                else:
                    # Grab that twerk data we calculated earlier
                    # (x - y + frame_number) is the animation frame index,
                    # we use the position and frame number as offsets to produce the wave-like effect
                    sussified_frame_data = np.copy(twerk_frames_data[(x - y + frame_number) % len(twerk_frames)])
                    red, green, blue, alpha = sussified_frame_data.T
                    # Replace all pixels with color (214,224,240) with the input image color at that location
                    color_1 = (red == 214) & (green == 224) & (blue == 240)
                    sussified_frame_data[..., :-1][color_1.T] = (r, g, b)  # thx stackoverflow
                    # Repeat with color (131,148,191) but use two thirds of the input image color to get a darker color
                    color_2 = (red == 131) & (green == 148) & (blue == 191)
                    sussified_frame_data[..., :-1][color_2.T] = (int(r * 2 / 3), int(g * 2 / 3), int(b * 2 / 3))

                    # Convert sussy frame data back to sussy frame
                    sussified_frame = Image.fromarray(sussified_frame_data)

                    # Slap said frame onto the background
                    background.paste(sussified_frame, (x * twerk_width, y * twerk_height))
        logging.info(f'Writting suss-ed frame \'{data_dir}/sussified_{frame_number}.png\'')
        background.save(f"{data_dir}/sussified_{frame_number}.png")

    print("Converting sussy frames to sussy gif")
    # Convert sussied frames to gif. PIL has a built-in method to save gifs but
    # it has dithering which looks sus, so we use ffmpeg with dither=none
    subprocess.run(
        f'ffmpeg -f image2 -i {data_dir}/sussified_%d.png -filter_complex "[0:v] scale=sws_dither=none:,split [a][b];[a] palettegen=max_colors=255:stats_mode=single [p];[b][p] paletteuse=dither=none" -r 20 -y -hide_banner -loglevel error {data_dir}/sussified.gif', shell=True)

    # Remove temp files
    print("Ejecting temp files from folder")
    for frame_number in range(twerk_frame_count):
        os.remove(f"{data_dir}/sussified_{frame_number}.png")

    # lamkas a cute

    return open(f'{data_dir}/sussified.gif', mode='rb')
