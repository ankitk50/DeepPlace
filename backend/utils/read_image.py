from pathlib import Path
from typing import Union, Optional, Tuple, IO
import numpy as np
from PIL import Image
from io import BytesIO

try:
except ImportError as exc:
    raise ImportError("Pillow is required to use read_image.py: pip install pillow") from exc


PathLike = Union[str, Path]
FileLike = Union[PathLike, bytes, IO[bytes]]


def _open_pil(source: FileLike) -> Image.Image:
    if isinstance(source, (str, Path)):
        return Image.open(str(source))
    if isinstance(source, bytes):
        return Image.open(BytesIO(source))
    # assume file-like
    return Image.open(source)


def read_image(
    source: FileLike,
    target_size: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """
    Read an image from a path, bytes or file-like object and return a numpy array.

    Parameters:
    - source: path (str or Path), bytes, or file-like object opened in binary mode
    - as_gray: if True, convert image to grayscale (H, W). Otherwise returns RGB (H, W, 3)
    - target_size: optional (width, height) to resize the image

    Returns:
    - uint8 numpy array with shape (H, W) or (H, W, 3)
    """
    img = _open_pil(source)
    img = img.convert("RGB")

    if target_size is not None:
        # target_size is (width, height)
        img = img.resize((int(target_size[0]), int(target_size[1])), resample=Image.BILINEAR)

    arr = np.asarray(img)
    # ensure uint8
    if arr.dtype != np.uint8:
        arr = (arr * 255).astype(np.uint8)

    return arr