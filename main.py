from argparse import ArgumentParser
import sys
import discord
from dotenv import load_dotenv
import os
import sus
import logging
import pathlib
import time

load_dotenv()  # take environment variables from .env

data_dir: pathlib.Path
input_dir: pathlib.Path
result_dir: pathlib.Path

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message: discord.Message):
    # Make sure the message is directed to us
    if message.author == client.user:
        return

    # Only respond to direct calls, Mentions, & DMs
    if '!sus' not in message.content and not isinstance(message.channel,
                                                        discord.DMChannel) and client.user not in message.mentions:
        return

    # Input flags
    text_content: str = message.content.upper()
    use_nearest_neighbor = 'nn'.upper() in text_content or 'nearest' in text_content
    output_width = 21  # Default output width from the original project
    if 'width: '.upper() in text_content:
        start_index = text_content.find('width: '.upper()) + len('width: ')
        char_buffer = str()
        for c in text_content[start_index:]:
            if not c.isdigit():
                break
            char_buffer += c
        try:
            output_width = int(char_buffer)
        except ValueError:
            logging.error(f'Failed to parse `output_width`, got: \'{char_buffer}\'')

    # Search for images
    # Either the poster of the image, or a direct reply to an image should work
    # if we can't find either of those, send a message and stop
    if not message.attachments and message.reference is None:
        await message.reply('I need an image you sussy baka!')
        logging.warning('Susser called, but no attachments found')
        return

    image_attachment = None

    # Case 1: Poster of the image called the bot
    # Search the attachments for some image type
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith('image/'):
                image_attachment = attachment

    # Case 2: A reply to an image called the bot
    # Search the attachments for some image type
    if image_attachment is None and message.reference is not None:
        for attachment in message.reference.resolved.attachments:
            if attachment.content_type.startswith('image/'):
                image_attachment = attachment

    # If we failed to find an image in the post &
    # the parent if this is a reply
    # then issue a similar error message
    if image_attachment is None:
        await message.reply('I need an image you sussy baka!')
        logging.warning('Susser called, attachments searched, but no images found')
        return

    current_time_ns = time.time_ns()

    # Save the found image to the `input_dir`
    # for conversion
    # Add the curren time in nanoseconds,
    # to avoid conflicts with images of the same name
    save_path: pathlib.Path = input_dir / (str(current_time_ns) + '_' + image_attachment.filename)
    logging.info(f'Downloading image to {str(save_path)}')
    with open(str(save_path), "wb+") as f:
        # Pull the image from Discord's servers
        await image_attachment.save(f)

        # Sussify the image, passing the flags from the message
        logging.info(
            f'Sussing image (\'{image_attachment.filename}\') with `nearest_neighbor`: {use_nearest_neighbor}, '
            '`output_width`: {output_width}')
        result = sus.to_sus(f, data_dir=data_dir, nearest_neighbor=use_nearest_neighbor, output_width=output_width)

        use_nearest_neighbor_text = ""
        if use_nearest_neighbor:
            use_nearest_neighbor_text = '_used-nearest-neighbor_'

        # Keep the result in `result_dir`
        file_name = str(current_time_ns) + use_nearest_neighbor_text + '.gif'
        saved_result = result_dir / file_name
        with open(str(saved_result), 'wb') as sr:
            sr.write(result.read())

        # Seek to the end of the file to get Python to tell us the size
        result.seek(0, 2)
        file_size = round(result.tell() / 1e6, 2)
        logging.info(f'Generated a file "{file_name}" with approximate size: {file_size} MB')

        # Seek back to the beginning of the file
        # Since most things expect it to be in that state
        result.seek(0, 0)

        # Generate a sensible filename for our creation
        discord_file_name = pathlib.Path(image_attachment.filename).stem + '-sussed.gif'

        # Deliver our gift to Discord
        try:
            await message.reply('', file=discord.File(result, filename=discord_file_name))
        except discord.HTTPException as e:
            if e.status == 413:
                await message.reply(f'Too many dumpers for Discord to handle (about {file_size}MB worth). '
                                    'Try reducing `width`')
            else:
                raise


def checkdir_with_logging(directory_: pathlib.Path, path_name: str):
    if not directory_.exists():
        logging.info(f"{path_name}:'{directory_.absolute()}' does not exist. Creating!")
        directory_.mkdir(parents=True)

    if not directory_.is_dir():
        logging.error(f"{path_name}:'{directory_.absolute()}' exists, but is not a directory!")
        sys.exit(1)


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-l', '--log', help='Log level', choices=['debug', 'info', 'warning', 'error', 'critical'],
                        type=str, default='info')
    args = parser.parse_args()

    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.log}')
    logging.basicConfig(level=numeric_level)

    data_dir = pathlib.Path(os.getenv("DataDir"))
    checkdir_with_logging(data_dir, 'DataDir')

    result_dir = data_dir / 'results/'
    checkdir_with_logging(result_dir, 'result_dir')

    input_dir = data_dir / 'inputs/'
    checkdir_with_logging(input_dir, 'input_dir')

    client.run(os.getenv("Token"))
