import torch
import cv2
import numpy as np

def bgr_to_rgb(image)-> np.ndarray:
    if image is None:
        raise FileNotFoundError(
            "Could not read the image"
        )

    image_rgb = cv2.cvtColor(image,cv2.COLOR_BGR2RGB) # type: ignore

    return image_rgb  # type:ignore


def resize_image(image,size=(512,512)) -> np.ndarray:
    if image is None:
        raise ValueError(
            "Input image is None"
        )

    image_resized = cv2.resize(image,size)

    expected_shape = (size[1] , size[0] , image.shape[2])

    if image_resized.shape != expected_shape:
        raise ValueError(
            f"Unexpected image Shape:"
            f"{image_resized.shape}"
            f"Expected : {expected_shape}"
        )

    return image_resized


def normalize_image(image) -> np.ndarray:
    if image is None:
        raise ValueError(
            "Input Image is None"
        )

    image_normalized = image.astype(np.float32) / 255.0


    if image_normalized.dtype != np.float32:
        raise TypeError(
            f"Expected float32, got {image_normalized.dtype}"
        )

    if image_normalized.min() < 0.0 or image_normalized.max() > 1.0:
        raise ValueError(
            "Normalized image values are outside [0, 1]"
        )

    return image_normalized


def to_tensor(image) -> torch.Tensor:
    if image is None:
        raise ValueError(
            "Input Image is None"
        )

    image_tensor = torch.from_numpy(image)

    if image_tensor.dtype != torch.float32:
        raise TypeError(
            f"Expected float32, got{image_tensor.dtype}"
        )

    if image_tensor.ndim != 3:
        raise ValueError(
            f"Expected 3 dimension (H,W,C)"
        )

    image_tensor = image_tensor.permute(2,0,1)

    return image_tensor


def preprocess_image(image , size=(512,512)) -> torch.Tensor:

    image = bgr_to_rgb(image)

    image = resize_image(image,size) # type: ignore

    image = normalize_image(image)

    image = to_tensor(image)

    return image
