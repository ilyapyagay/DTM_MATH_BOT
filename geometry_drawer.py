import io
import re
import math
from PIL import Image, ImageDraw, ImageFont


def get_font(size=20):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "arial.ttf"
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_rectangle(w_text="a", h_text="b", title="Прямоугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1, x2, y2 = 110, 90, 410, 270
    
    draw.rectangle([x1, y1, x2, y2], fill="#e0f2fe", outline="#0284c7", width=4)
    
    m = 15
    for (cx, cy, dx, dy) in [(x1, y1, 1, 1), (x2, y1, -1, 1), (x2, y2, -1, -1), (x1, y2, 1, -1)]:
        draw.line([(cx + dx*m, cy), (cx + dx*m, cy + dy*m), (cx, cy + dy*m)], fill="#0284c7", width=2)
        
    draw.text(((x1+x2)//2 - 25, y2 + 12), str(w_text), fill="#0f172a", font=font_label)
    draw.text((x2 + 15, (y1+y2)//2 - 10), str(h_text), fill="#0f172a", font=font_label)
    
    draw.text((x1-25, y1-25), "A", fill="#64748b", font=font_label)
    draw.text((x2+10, y1-25), "B", fill="#64748b", font=font_label)
    draw.text((x2+10, y2+10), "C", fill="#64748b", font=font_label)
    draw.text((x1-25, y2+10), "D", fill="#64748b", font=font_label)
    return img


def draw_square(side_text="a", title="Квадрат"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1, x2, y2 = 150, 80, 370, 300
    
    draw.rectangle([x1, y1, x2, y2], fill="#dcfce7", outline="#16a34a", width=4)
    
    # Tick marks on sides
    draw.line([((x1+x2)//2 - 5, y1 - 5), ((x1+x2)//2 + 5, y1 + 5)], fill="#16a34a", width=3)
    draw.line([((x1+x2)//2 - 5, y2 - 5), ((x1+x2)//2 + 5, y2 + 5)], fill="#16a34a", width=3)
    draw.line([(x1 - 5, (y1+y2)//2 - 5), (x1 + 5, (y1+y2)//2 + 5)], fill="#16a34a", width=3)
    draw.line([(x2 - 5, (y1+y2)//2 - 5), (x2 + 5, (y1+y2)//2 + 5)], fill="#16a34a", width=3)
    
    draw.text(((x1+x2)//2 - 20, y2 + 15), str(side_text), fill="#0f172a", font=font_label)
    draw.text((x2 + 15, (y1+y2)//2 - 10), str(side_text), fill="#0f172a", font=font_label)
    return img


def draw_right_triangle(cat1="a", cat2="b", hypot="c", title="Прямоугольный треугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1 = 120, 300
    x2, y2 = 400, 300
    x3, y3 = 120, 80
    
    draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill="#fef9c3", outline="#ca8a04", width=4)
    
    # Right angle mark
    m = 20
    draw.line([(x1+m, y1), (x1+m, y1-m), (x1, y1-m)], fill="#ca8a04", width=2)
    
    draw.text(((x1+x2)//2 - 20, y1 + 12), str(cat1), fill="#0f172a", font=font_label)
    draw.text((x1 - 55, (y1+y3)//2), str(cat2), fill="#0f172a", font=font_label)
    draw.text(((x2+x3)//2 + 15, (y2+y3)//2 - 15), str(hypot), fill="#0f172a", font=font_label)
    return img


def draw_triangle(base="a", height="h", title="Треугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1 = 90, 300
    x2, y2 = 430, 300
    x3, y3 = 240, 80
    
    draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill="#f3e8ff", outline="#9333ea", width=4)
    
    # Dashed height
    draw.line([(x3, y3), (x3, y1)], fill="#9333ea", width=2)
    
    # Right angle mark at height base
    m = 12
    draw.line([(x3, y1-m), (x3+m, y1-m), (x3+m, y1)], fill="#9333ea", width=2)
    
    draw.text(((x1+x2)//2 - 20, y1 + 12), f"a = {base}", fill="#0f172a", font=font_label)
    draw.text((x3 + 8, (y1+y3)//2), f"h = {height}", fill="#9333ea", font=font_label)
    return img


def draw_circle(rad="R", diam=None, title="Окружность / Круг"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy, r = 260, 200, 110
    
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#fee2e2", outline="#dc2626", width=4)
    
    # Center dot
    draw.ellipse([cx-5, cy-5, cx+5, cy+5], fill="#dc2626")
    draw.text((cx-15, cy+8), "O", fill="#0f172a", font=font_label)
    
    if diam:
        draw.line([(cx-r, cy), (cx+r, cy)], fill="#dc2626", width=3)
        draw.text((cx - 30, cy - 30), f"D = {diam}", fill="#0f172a", font=font_label)
    else:
        draw.line([(cx, cy), (cx+r, cy)], fill="#dc2626", width=3)
        draw.text((cx + r//2 - 20, cy - 28), f"R = {rad}", fill="#0f172a", font=font_label)
        
    return img


def draw_adjacent_angles(a1="α", a2="β", title="Смежные углы (Сумма 180°)"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy = 260, 280
    
    # Horizontal line
    draw.line([(60, cy), (460, cy)], fill="#0f172a", width=4)
    # Ray at ~65 degrees
    ang = math.radians(65)
    rx = cx + 180 * math.cos(ang)
    ry = cy - 180 * math.sin(ang)
    draw.line([(cx, cy), (rx, ry)], fill="#2563eb", width=4)
    
    # Arcs
    draw.arc([cx-60, cy-60, cx+60, cy+60], start=180, end=360-65, fill="#dc2626", width=3)
    draw.arc([cx-45, cy-45, cx+45, cy+45], start=360-65, end=360, fill="#16a34a", width=3)
    
    draw.text((cx - 80, cy - 40), str(a1), fill="#dc2626", font=font_label)
    draw.text((cx + 50, cy - 40), str(a2), fill="#16a34a", font=font_label)
    return img


def draw_vertical_angles(a1="α", a2="β", title="Вертикальные углы (Равны)"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy = 260, 200
    
    draw.line([(80, 320), (440, 80)], fill="#0f172a", width=4)
    draw.line([(80, 80), (440, 320)], fill="#0f172a", width=4)
    
    draw.arc([cx-50, cy-50, cx+50, cy+50], start=360-33, end=33, fill="#dc2626", width=3)
    draw.arc([cx-50, cy-50, cx+50, cy+50], start=180-33, end=180+33, fill="#dc2626", width=3)
    
    draw.text((cx - 85, cy - 12), str(a1), fill="#dc2626", font=font_label)
    draw.text((cx + 60, cy - 12), str(a1), fill="#dc2626", font=font_label)
    return img


def draw_cube(side="a", title="Куб / Параллелепипед"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    
    # Front face
    x1, y1, x2, y2 = 140, 160, 300, 320
    # Back face shift
    dx, dy = 70, -60
    
    # Front face
    draw.rectangle([x1, y1, x2, y2], fill="#e0e7ff", outline="#4f46e5", width=4)
    
    # Back top and right edges
    draw.line([(x1, y1), (x1+dx, y1+dy), (x2+dx, y1+dy), (x2, y1)], fill="#4f46e5", width=3)
    draw.line([(x2+dx, y1+dy), (x2+dx, y2+dy), (x2, y2)], fill="#4f46e5", width=3)
    
    # Hidden dashed lines
    draw.line([(x1, y2), (x1+dx, y2+dy)], fill="#94a3b8", width=2)
    draw.line([(x1+dx, y2+dy), (x2+dx, y2+dy)], fill="#94a3b8", width=2)
    draw.line([(x1+dx, y2+dy), (x1+dx, y1+dy)], fill="#94a3b8", width=2)
    
    draw.text(((x1+x2)//2 - 15, y2 + 10), str(side), fill="#0f172a", font=font_label)
    draw.text((x2 + 10, (y1+y2)//2), str(side), fill="#0f172a", font=font_label)
    return img


def draw_clock(hour=3, title="Циферблат часов"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(22)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy, r = 260, 210, 110
    
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#ffffff", outline="#0f172a", width=4)
    draw.ellipse([cx-5, cy-5, cx+5, cy+5], fill="#0f172a")
    
    # Clock numbers
    for h in [12, 3, 6, 9]:
        ang = math.radians(h * 30 - 90)
        nx = cx + (r - 25) * math.cos(ang) - 8
        ny = cy + (r - 25) * math.sin(ang) - 10
        draw.text((nx, ny), str(h), fill="#64748b", font=font_label)
        
    # Minute hand pointing at 12
    draw.line([(cx, cy), (cx, cy - r + 25)], fill="#0f172a", width=4)
    
    # Hour hand
    hang = math.radians(hour * 30 - 90)
    hx = cx + (r - 45) * math.cos(hang)
    hy = cy + (r - 45) * math.sin(hang)
    draw.line([(cx, cy), (hx, hy)], fill="#dc2626", width=6)
    
    angle_deg = (hour % 12) * 30
    if angle_deg > 180:
        angle_deg = 360 - angle_deg
    draw.text((25, 340), f"Угол между стрелками: {angle_deg}°", fill="#dc2626", font=font_label)
    return img


def generate_geometry_image(question_text: str) -> bytes:
    """Генерирует наглядный геометрический чертёж PNG по условию задачи"""
    text = question_text.lower()
    
    # Извлекаем числа из текста
    nums = re.findall(r'\b\d+(?:[\.,]\d+)?\b', question_text)
    
    if "прямоугольник" in text and "треугольник" not in text:
        w = nums[0] + " см" if len(nums) > 0 else "a"
        h = nums[1] + " см" if len(nums) > 1 else ("b" if len(nums) == 0 else nums[0]+" см")
        if "периметр" in text and len(nums) > 1:
            title = f"Прямоугольник (P = {nums[0]})"
            w = nums[1] + " см"
            h = "?"
        elif "площадь" in text and len(nums) > 1:
            title = f"Прямоугольник (S = {nums[0]})"
            w = nums[1] + " см"
            h = "?"
        else:
            title = "Прямоугольник"
        img = draw_rectangle(w, h, title)
        
    elif "квадрат" in text:
        side = nums[0] + " см" if len(nums) > 0 else "a"
        title = f"Квадрат (Периметр = {nums[0]} см)" if "периметр" in text and len(nums)>0 else "Квадрат"
        if "площадь" in text and len(nums)>0:
            title = f"Квадрат (Площадь = {nums[0]} см²)"
        img = draw_square(side, title)
        
    elif "прямоугольн" in text and ("треугольник" in text or "катет" in text or "гипотенуз" in text):
        c1 = nums[0] + " см" if len(nums) > 0 else "a"
        c2 = nums[1] + " см" if len(nums) > 1 else "b"
        hyp = nums[2] + " см" if len(nums) > 2 else "c = ?"
        img = draw_right_triangle(c1, c2, hyp)
        
    elif "равносторон" in text and "треугольник" in text:
        side = nums[0] + " см" if len(nums) > 0 else "a"
        img = draw_triangle(side, side, "Равносторонний треугольник")
        
    elif "треугольник" in text:
        b = nums[0] + " см" if len(nums) > 0 else "a"
        h = nums[1] + " см" if len(nums) > 1 else "h"
        img = draw_triangle(b, h)
        
    elif any(k in text for k in ["окружност", "круг", "радиус", "диаметр"]):
        if "диаметр" in text and len(nums) > 0:
            img = draw_circle(rad="?", diam=nums[0] + " см")
        else:
            r = nums[0] + " см" if len(nums) > 0 else "R"
            img = draw_circle(rad=r)
            
    elif "смежн" in text:
        a1 = nums[0] + "°" if len(nums) > 0 else "α"
        a2 = "?" if len(nums) > 0 else "β"
        img = draw_adjacent_angles(a1, a2)
        
    elif "вертикальн" in text:
        a1 = nums[0] + "°" if len(nums) > 0 else "α"
        img = draw_vertical_angles(a1, a1)
        
    elif any(k in text for k in ["куб", "параллелепипед", "объем", "объём"]):
        side = nums[0] + " см" if len(nums) > 0 else "a"
        img = draw_cube(side)
        
    elif any(k in text for k in ["час", "стрелк", "циферблат"]):
        hr = int(nums[0]) if len(nums) > 0 and int(nums[0]) <= 12 else 3
        img = draw_clock(hr)
        
    else:
        # Универсальный чертеж геометрической задачи
        img = draw_rectangle("a", "b", "Геометрический чертеж")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
