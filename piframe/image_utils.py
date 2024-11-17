from PIL import Image, ImageDraw, ImageFont


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

def overlay_prompt(image: Image.Image, text: str) -> Image.Image:
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_size = 24
    font = ImageFont.load_default(size=font_size)
    text_width = draw.textlength(text, font=font)
    padding = 10
    background_height = font_size + 2 * padding
    text_x = (image.width - text_width) // 2
    text_y = image.height - background_height + padding

    draw.rectangle([(0, image.height - background_height), (image.width, image.height)], fill=(0, 0, 0, 200))
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=1.0)
    combined = Image.alpha_composite(image, overlay)
    return combined.convert("RGB")