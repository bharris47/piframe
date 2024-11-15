from PIL import Image


def scale_and_crop(img: Image.Image, target_width: int, target_height: int, resample: int = Image.LANCZOS) -> Image.Image:
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        new_height = target_height
        new_width = int(img.width * (target_height / img.height))
    else:
        new_width = target_width
        new_height = int(img.height * (target_width / img.width))

    resized_img = img.resize((new_width, new_height), resample)

    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    right = left + target_width
    bottom = top + target_height
    cropped_img = resized_img.crop((left, top, right, bottom))

    return cropped_img
