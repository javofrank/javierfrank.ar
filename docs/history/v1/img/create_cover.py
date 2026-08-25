import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

def create_rounded_mask(size, radius):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), size], radius=radius, fill=255)
    return mask

def make_cover():
    width = 1200
    height = 630
    
    # 1. Base canvas in Navy
    img = Image.new('RGBA', (width, height), (14, 31, 51, 255))
    
    # 2. Background building image
    bg_path = 'docs/img/buenos-aires.jpg'
    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert('RGBA')
        bg_ratio = bg.width / bg.height
        target_ratio = width / height
        if bg_ratio > target_ratio:
            new_h = height
            new_w = int(height * bg_ratio)
        else:
            new_w = width
            new_h = int(width / bg_ratio)
        bg = bg.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        bg = bg.crop((left, top, left + width, top + height))
        
        # Blur & subtle darken for modern depth
        bg = bg.filter(ImageFilter.GaussianBlur(3))
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.35)
        img.paste(bg, (0, 0))
    
    # 3. Smooth gradient overlay (deep navy left to translucent navy right)
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for x in range(width):
        prog = x / width
        alpha = int(245 - prog * 85)  # 245 on left, 160 on right
        draw_ov.line([(x, 0), (x, height)], fill=(14, 31, 51, alpha))
        
    img = Image.alpha_composite(img, overlay)
    
    # Red top accent line
    top_bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw_tb = ImageDraw.Draw(top_bar)
    draw_tb.rectangle([(0, 0), (width, 6)], fill=(226, 35, 26, 255))
    img = Image.alpha_composite(img, top_bar)
    
    # Fonts
    def get_font(filename, size):
        p = f"C:/Windows/Fonts/{filename}"
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
        return ImageFont.load_default()

    font_kicker = get_font("segoeuib.ttf", 16) or get_font("arialbd.ttf", 16)
    font_name = get_font("segoeuib.ttf", 52) or get_font("arialbd.ttf", 52)
    font_tag = get_font("segoeuib.ttf", 19) or get_font("arialbd.ttf", 19)
    font_desc = get_font("segoeui.ttf", 22) or get_font("arial.ttf", 22)
    font_badges = get_font("segoeuib.ttf", 15) or get_font("arialbd.ttf", 15)
    font_url = get_font("segoeuib.ttf", 20) or get_font("arialbd.ttf", 20)
    font_contact = get_font("segoeui.ttf", 17) or get_font("arial.ttf", 17)

    # 4. Translucent elements layer
    ui_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw_ui = ImageDraw.Draw(ui_layer)

    balloon_path = 'docs/img/remax-balloon-2026.png'
    pill_x, pill_y = 70, 60
    pill_w, pill_h = 390, 42
    draw_ui.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=21, fill=(255, 255, 255, 28), outline=(255, 255, 255, 60), width=1)
    
    # Feature Badges
    badges_y = 350
    badges = ["• Análisis de Mercado", "• Inversiones", "• Asesoramiento"]
    bx = 70
    for b in badges:
        bbox = draw_ui.textbbox((0, 0), b, font=font_badges)
        bw = bbox[2] - bbox[0] + 28
        bh = 36
        draw_ui.rounded_rectangle([bx, badges_y, bx + bw, badges_y + bh], radius=10, fill=(255, 255, 255, 22), outline=(255, 255, 255, 45), width=1)
        draw_ui.text((bx + 14, badges_y + 8), b, font=font_badges, fill=(255, 255, 255, 230))
        bx += bw + 12

    # Bottom divider line
    draw_ui.line([(70, 495), (660, 495)], fill=(255, 255, 255, 40), width=1)
    
    # URL pill button
    url_btn_y = 520
    url_btn_w = 205
    url_btn_h = 42
    draw_ui.rounded_rectangle([70, url_btn_y, 70 + url_btn_w, url_btn_y + url_btn_h], radius=21, fill=(226, 35, 26, 255))
    draw_ui.text((70 + 34, url_btn_y + 9), "javierfrank.ar", font=font_url, fill=(255, 255, 255, 255))
    draw_ui.text((70 + url_btn_w + 24, url_btn_y + 11), "+54 9 11 3378 2524  ·  RE/MAX Amazing", font=font_contact, fill=(200, 215, 230, 230))

    img = Image.alpha_composite(img, ui_layer)
    draw = ImageDraw.Draw(img)

    # Draw texts that go over translucent layers
    if os.path.exists(balloon_path):
        balloon = Image.open(balloon_path).convert('RGBA')
        b_w, b_h = balloon.size
        target_b_h = 26
        target_b_w = int(b_w * (target_b_h / b_h))
        balloon_small = balloon.resize((target_b_w, target_b_h), Image.Resampling.LANCZOS)
        img.paste(balloon_small, (pill_x + 14, pill_y + 8), balloon_small)
        draw.text((pill_x + 46, pill_y + 10), "RE/MAX AMAZING  ·  BUENOS AIRES", font=font_kicker, fill=(255, 255, 255, 240))
    else:
        draw.text((pill_x + 20, pill_y + 10), "RE/MAX AMAZING  ·  BUENOS AIRES", font=font_kicker, fill=(255, 255, 255, 240))

    # Name and Title
    name_x = 70
    name_y = 128
    draw.text((name_x, name_y), "Javier Frank", font=font_name, fill=(255, 255, 255, 255))
    
    # Red accent bar before Tag
    tag_y = name_y + 68
    draw.rectangle([(name_x, tag_y + 6), (name_x + 18, tag_y + 18)], fill=(226, 35, 26, 255))
    draw.text((name_x + 28, tag_y), "AGENTE INMOBILIARIO", font=font_tag, fill=(255, 125, 120, 255))

    # Subtitle / value proposition
    desc_y = tag_y + 44
    draw.text((name_x, desc_y), "Asesoramiento personalizado, compra,", font=font_desc, fill=(240, 245, 250, 245))
    draw.text((name_x, desc_y + 30), "venta y tasación de propiedades.", font=font_desc, fill=(240, 245, 250, 245))
    draw.text((name_x, desc_y + 60), "Decisiones seguras con respaldo profesional.", font=font_desc, fill=(185, 200, 218, 220))

    # 5. Right Side Photo Card (using studio photo fotojfconfondo.jpg)
    photo_path = 'docs/img/fotojfconfondo.jpg'
    if os.path.exists(photo_path):
        photo = Image.open(photo_path).convert('RGB')
        
        card_w = 400
        card_h = 500
        card_x = 720
        card_y = 65
        
        # Soft shadow behind card
        shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(shadow)
        sh_draw.rounded_rectangle([card_x - 12, card_y - 12, card_x + card_w + 12, card_y + card_h + 12], radius=32, fill=(0, 0, 0, 150))
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        img = Image.alpha_composite(img, shadow)
        
        # Crop & resize photo to fit exactly in card_w x card_h
        photo_cropped = ImageOps.fit(photo, (card_w, card_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.25))
        
        # Rounded corner mask
        mask = create_rounded_mask((card_w, card_h), radius=26)
        
        # Paste rounded photo
        photo_rgba = photo_cropped.convert('RGBA')
        photo_card = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        photo_card.paste(photo_rgba, (card_x, card_y), mask)
        
        # Draw elegant border on card
        photo_card_draw = ImageDraw.Draw(photo_card)
        photo_card_draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=26, outline=(255, 255, 255, 70), width=2)
        
        img = Image.alpha_composite(img, photo_card)
        
        # RE/MAX Badge overlapping bottom right of photo
        if os.path.exists(balloon_path):
            badge_icon = Image.open(balloon_path).convert('RGBA')
            badge_icon = badge_icon.resize((48, 54), Image.Resampling.LANCZOS)
            
            badge_w, badge_h = 80, 80
            badge_x = card_x + card_w - 50
            badge_y = card_y + card_h - 60
            
            # Badge shadow
            b_shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            b_sh_draw = ImageDraw.Draw(b_shadow)
            b_sh_draw.rounded_rectangle([badge_x - 4, badge_y - 4, badge_x + badge_w + 4, badge_y + badge_h + 4], radius=22, fill=(0, 0, 0, 160))
            b_shadow = b_shadow.filter(ImageFilter.GaussianBlur(10))
            img = Image.alpha_composite(img, b_shadow)
            
            # Badge frame
            badge_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            b_draw = ImageDraw.Draw(badge_layer)
            b_draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=20, fill=(255, 255, 255, 255), outline=(226, 35, 26, 220), width=2)
            badge_layer.paste(badge_icon, (badge_x + 16, badge_y + 13), badge_icon)
            
            img = Image.alpha_composite(img, badge_layer)

    # Save final JPG
    final_rgb = img.convert('RGB')
    final_rgb.save('docs/img/imagen-de-portada.jpg', 'JPEG', quality=95)
    print("Cover image updated with flawless styling!")

if __name__ == '__main__':
    make_cover()
