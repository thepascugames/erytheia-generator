#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
from psd_tools import PSDImage

BASE_DIR = Path(__file__).parent
LOGOS_DIR = BASE_DIR
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

WIDTH, HEIGHT = 1080, 1440
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW_SCORE = (255, 198, 0)

def get_font(size, role="text"):
    font_name = "font_title.ttf" if role == "title" else "font_text.ttf"
    candidates = [
        BASE_DIR / font_name,
        BASE_DIR / f"font_{role}.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_centered_text(draw, text, center_x, center_y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = center_x - (tw / 2) - bbox[0]
    y = center_y - (th / 2) - bbox[1]
    draw.text((x, y), text, font=font, fill=fill)

def load_logo(path, max_size=102):
    if not path or not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None

def prepare_full_background(photo_path):
    if photo_path and os.path.exists(photo_path):
        photo = Image.open(photo_path).convert("RGB")
    else:
        photo = Image.new("RGB", (WIDTH, HEIGHT), (25, 25, 25))
    target_ratio = WIDTH / HEIGHT
    img_ratio = photo.width / photo.height
    if img_ratio > target_ratio:
        new_width = int(photo.height * target_ratio)
        left = (photo.width - new_width) // 2
        photo = photo.crop((left, 0, left + new_width, photo.height))
    else:
        new_height = int(photo.width / target_ratio)
        top = (photo.height - new_height) // 2
        photo = photo.crop((0, top, photo.width, top + new_height))
    return photo.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).convert("RGBA")

def prepare_box_photo(photo_path, box_w, box_h):
    if photo_path and os.path.exists(photo_path):
        photo = Image.open(photo_path).convert("RGB")
    else:
        photo = Image.new("RGB", (box_w, box_h), (200, 200, 200))
    target_ratio = box_w / box_h
    img_ratio = photo.width / photo.height
    if img_ratio > target_ratio:
        new_width = int(photo.height * target_ratio)
        left = (photo.width - new_width) // 2
        photo = photo.crop((left, 0, left + new_width, photo.height))
    else:
        new_height = int(photo.width / target_ratio)
        top = (photo.height - new_height) // 2
        photo = photo.crop((0, top, photo.width, top + new_height))
    return photo.resize((box_w, box_h), Image.Resampling.LANCZOS).convert("RGBA")

def generate_graphic(
    mode,
    photo_path,
    score_home,
    score_away,
    scorers_erytheia,
    date_text,
    is_home=True,
    rival_logo_path=None,
    output_name="graphic.png"
):
    if mode == "halftime":
        base = Image.new("RGBA", (WIDTH, HEIGHT), (242, 242, 242))

        box_x, box_y = 33, 250
        box_w, box_h = 1014, 922
        
        box_photo = prepare_box_photo(photo_path, box_w, box_h)
        base.paste(box_photo, (box_x, box_y))

        psd_path = BASE_DIR / "half-time.psd"
        if psd_path.exists():
            try:
                psd = PSDImage.open(psd_path)
                template_layer = psd.composite().convert("RGBA")
                if template_layer.size != (WIDTH, HEIGHT):
                    template_layer = template_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
                
                pixels = template_layer.load()
                for y in range(box_y + 4, box_y + box_h - 4):
                    for x in range(box_x + 4, box_x + box_w - 4):
                        r, g, b, a = pixels[x, y]
                        if y < 1102 and 170 < r < 245 and 170 < g < 245 and 170 < b < 245:
                            pixels[x, y] = (r, g, b, 0)

                base = Image.alpha_composite(base, template_layer)
            except Exception:
                pass

        draw = ImageDraw.Draw(base)

        erytheia_logo = load_logo(LOGOS_DIR / "erytheia_shield_white.png", max_size=102)
        rival_logo = load_logo(rival_logo_path, max_size=102) if rival_logo_path else None

        if is_home:
            left_logo, right_logo = erytheia_logo, rival_logo
            left_score, right_score = score_home, score_away
        else:
            left_logo, right_logo = rival_logo, erytheia_logo
            left_score, right_score = score_away, score_home

        box_top = 1106
        box_height = 118
        center_y = box_top + (box_height / 2)

        draw.line([(WIDTH // 2, box_top + 16), (WIDTH // 2, box_top + box_height - 16)], fill=YELLOW_SCORE, width=4)

        score_font = get_font(98, role="title")
        draw_centered_text(draw, str(left_score), 482, center_y, score_font, YELLOW_SCORE)
        draw_centered_text(draw, str(right_score), 598, center_y, score_font, YELLOW_SCORE)

        if left_logo:
            lx = 365 - (left_logo.width // 2)
            ly = int(center_y - (left_logo.height // 2))
            base.paste(left_logo, (lx, ly), left_logo)

        if right_logo:
            rx = 715 - (right_logo.width // 2)
            ly = int(center_y - (right_logo.height // 2))
            base.paste(right_logo, (rx, ly), right_logo)

    else:
        # MODO FULL-TIME (Intacto)
        bg = prepare_full_background(photo_path)
        psd_path = BASE_DIR / "full-time.psd"
        if psd_path.exists():
            try:
                psd = PSDImage.open(psd_path)
                template_layer = psd.composite().convert("RGBA")
                if template_layer.size != (WIDTH, HEIGHT):
                    template_layer = template_layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
                base = Image.alpha_composite(bg, template_layer)
            except Exception:
                base = bg
        else:
            base = bg

        draw = ImageDraw.Draw(base)
        erytheia_logo = load_logo(LOGOS_DIR / "erytheia_shield_white.png", max_size=164)
        rival_logo = load_logo(rival_logo_path, max_size=164) if rival_logo_path else None

        if is_home:
            left_logo, right_logo = erytheia_logo, rival_logo
            left_score, right_score = score_home, score_away
            scorers, scorers_side = scorers_erytheia, "left"
        else:
            left_logo, right_logo = rival_logo, erytheia_logo
            left_score, right_score = score_away, score_home
            scorers, scorers_side = scorers_erytheia, "right"

        box_size = 162
        gap = 78
        total_w = box_size * 2 + gap
        scores_x = (WIDTH - total_w) // 2
        score_y = 985

        score_font = get_font(112, role="title")
        draw_centered_text(draw, str(left_score), scores_x + box_size / 2, score_y + box_size / 2, score_font, WHITE)
        draw_centered_text(draw, str(right_score), scores_x + box_size + gap + box_size / 2, score_y + box_size / 2, score_font, WHITE)

        if left_logo:
            ly = score_y + (box_size - left_logo.height) // 2
            lx = scores_x - left_logo.width - 40
            base.paste(left_logo, (lx, ly), left_logo)

        if right_logo:
            ly = score_y + (box_size - right_logo.height) // 2
            rx = scores_x + total_w + 40
            base.paste(right_logo, (rx, ly), right_logo)

        if scorers:
            scorer_font = get_font(23, role="text")
            line_h = 33
            start_y = 1185
            sep_x = WIDTH // 2
            sep_bottom = max(start_y + len(scorers) * line_h + 15, 1320)
            draw.line([(sep_x, start_y - 4), (sep_x, sep_bottom)], fill=WHITE, width=2)
            for i, line in enumerate(scorers):
                txt = line.upper()
                bbox = draw.textbbox((0, 0), txt, font=scorer_font)
                tw = bbox[2] - bbox[0]
                y_pos = start_y + i * line_h - bbox[1]
                if scorers_side == "left":
                    draw.text((sep_x - 45 - tw - bbox[0], y_pos), txt, font=scorer_font, fill=WHITE)
                else:
                    draw.text((sep_x + 45 - bbox[0], y_pos), txt, font=scorer_font, fill=WHITE)

        footer_center_y = 1384
        footer_font = get_font(22, role="text")
        date_up = date_text.upper()
        draw_centered_text(draw, date_up, WIDTH / 2, footer_center_y, footer_font, WHITE)

    out = OUTPUT_DIR / output_name
    base.convert("RGB").save(out, "PNG", quality=95)
    return str(out)
