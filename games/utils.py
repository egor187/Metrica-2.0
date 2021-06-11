import logging
import io

import django.core.files.uploadedfile
from django.core.files.base import ContentFile

import requests
from PIL import Image


logger = logging.getLogger("Metrica_logger")


def get_default_cover(fp, source):

    file_name = 'default_cover.jpg'
    file_fp = f"{fp}\\{file_name}"

    try:
        open(file_fp, 'rb').read()
    except Exception as e:
        logger.warning(f"Error signature: {e}. Download default_cover")
        response = requests.get(source)
        with open(file_fp, "wb") as f:
            f.write(response.content)
            f.close()


def game_cover_double_reducer(avatar: django.core.files.uploadedfile.InMemoryUploadedFile):
    """
    Reduce given Django InMemoryUploadedFile in a half
    :param avatar: django.core.files.uploadedfile.InMemoryUploadedFile
    :return: InMemoryUploadedFile
    """
    user_avatar_filename = avatar.name
    buffer = io.BytesIO()
    reduced_user_avatar = Image.open(io.BytesIO(avatar.read())).reduce(2)  # Reduce file size in twice
    reduced_user_avatar.save(fp=buffer, format='JPEG')  # save reduced file in bytes stream object to buffer for
    # further implementation of InMemoryUploadedFile (Django wrapper on sends through form file)

    file_from_buffer = buffer.getvalue()  # access to buffer for getting reduced file
    stream_file = ContentFile(file_from_buffer)  # Django file wrapper to read streams objects

    in_memory_uploaded_file = django.core.files.uploadedfile.InMemoryUploadedFile(
        file=stream_file,
        field_name=None,
        name=user_avatar_filename,
        content_type='image/jpeg',
        size=len(stream_file),
        charset=None
    )

    return in_memory_uploaded_file
