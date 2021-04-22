import logging

import requests


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