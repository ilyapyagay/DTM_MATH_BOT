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


# --- ОТРИСОВКА ГРАФИКОВ ФУНКЦИЙ (РАЗДЕЛ 9) ---

def draw_function_graph(eq_str="y = kx + b", func_type="linear", k=1.0, b=0.0, a=1.0):
    img = Image.new("RGB", (520, 400), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(20)
    font_sm = get_font(14)
    
    draw.text((20, 15), f"График: {eq_str}", fill="#0f172a", font=font_title)
    
    ox, oy = 260, 220
    scale = 20
    
    # Сетка
    for x in range(-12, 13):
        px = ox + x * scale
        color = "#cbd5e1" if x == 0 else "#e2e8f0"
        width = 2 if x == 0 else 1
        draw.line([(px, 48), (px, 385)], fill=color, width=width)
        if x != 0 and x % 5 == 0:
            draw.text((px - 8, oy + 5), str(x), fill="#64748b", font=font_sm)
            
    for y in range(-8, 9):
        py = oy - y * scale
        color = "#cbd5e1" if y == 0 else "#e2e8f0"
        width = 2 if y == 0 else 1
        draw.line([(20, py), (500, py)], fill=color, width=width)
        if y != 0 and y % 5 == 0:
            draw.text((ox + 6, py - 8), str(y), fill="#64748b", font=font_sm)
            
    # Оси и стрелки
    draw.line([(495, oy-5), (500, oy), (495, oy+5)], fill="#0f172a", width=2)
    draw.line([(ox-5, 53), (ox, 48), (ox+5, 53)], fill="#0f172a", width=2)
    draw.text((485, oy - 25), "x", fill="#0f172a", font=font_title)
    draw.text((ox + 10, 48), "y", fill="#0f172a", font=font_title)
    draw.text((ox - 15, oy + 5), "0", fill="#0f172a", font=font_sm)
    
    # Линия графика
    points = []
    for step in range(-250, 251):
        x_val = step / 20.0
        if func_type == "linear":
            y_val = k * x_val + b
        else:
            y_val = a * (x_val**2) + k * x_val + b
        px = ox + x_val * scale
        py = oy - y_val * scale
        if 45 <= py <= 390 and 20 <= px <= 500:
            points.append((px, py))
            
    if len(points) > 1:
        draw.line(points, fill="#2563eb", width=4)
        
    # Точки пересечения или вершина
    if func_type == "linear":
        # Пересечение с Oy (0, b)
        py_int = oy - b * scale
        if 48 <= py_int <= 385:
            draw.ellipse([ox-5, py_int-5, ox+5, py_int+5], fill="#dc2626")
    else:
        # Вершина параболы (-k/(2a), c - k^2/(4a))
        vx = -k / (2 * a) if a != 0 else 0
        vy = a * (vx**2) + k * vx + b
        px_v = ox + vx * scale
        py_v = oy - vy * scale
        if 48 <= py_v <= 385 and 20 <= px_v <= 500:
            draw.ellipse([px_v-5, py_v-5, px_v+5, py_v+5], fill="#dc2626")
            draw.text((px_v + 8, py_v - 10), f"({round(vx,1)}; {round(vy,1)})", fill="#dc2626", font=font_sm)
            
    return img


# --- ОТРИСОВКА ГЕОМЕТРИИ (РАЗДЕЛ 10) С УЧЕТОМ УСЛОВИЙ ---

def draw_rectangle(w_text="a", h_text="b", title="Прямоугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
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
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1, x2, y2 = 150, 80, 370, 300
    
    draw.rectangle([x1, y1, x2, y2], fill="#dcfce7", outline="#16a34a", width=4)
    
    for (lx1, ly1, lx2, ly2) in [
        (((x1+x2)//2 - 5, y1 - 5), ((x1+x2)//2 + 5, y1 + 5)),
        (((x1+x2)//2 - 5, y2 - 5), ((x1+x2)//2 + 5, y2 + 5)),
        ((x1 - 5, (y1+y2)//2 - 5), (x1 + 5, (y1+y2)//2 + 5)),
        ((x2 - 5, (y1+y2)//2 - 5), (x2 + 5, (y1+y2)//2 + 5))
    ]:
        draw.line([lx1, lx2], fill="#16a34a", width=3)
        
    draw.text(((x1+x2)//2 - 20, y2 + 15), str(side_text), fill="#0f172a", font=font_label)
    draw.text((x2 + 15, (y1+y2)//2 - 10), str(side_text), fill="#0f172a", font=font_label)
    return img


def draw_right_triangle(cat1="a", cat2="b", hypot="c", title="Прямоугольный треугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1 = 120, 310
    x2, y2 = 410, 310
    x3, y3 = 120, 80
    
    draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill="#fef9c3", outline="#ca8a04", width=4)
    
    m = 20
    draw.line([(x1+m, y1), (x1+m, y1-m), (x1, y1-m)], fill="#ca8a04", width=2)
    
    draw.text(((x1+x2)//2 - 20, y1 + 12), str(cat1), fill="#0f172a", font=font_label)
    draw.text((x1 - 65, (y1+y3)//2), str(cat2), fill="#0f172a", font=font_label)
    draw.text(((x2+x3)//2 + 15, (y2+y3)//2 - 15), str(hypot), fill="#0f172a", font=font_label)
    return img


def draw_triangle(base="a", height="h", title="Треугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1 = 90, 310
    x2, y2 = 430, 310
    x3, y3 = 240, 80
    
    draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill="#f3e8ff", outline="#9333ea", width=4)
    draw.line([(x3, y3), (x3, y1)], fill="#9333ea", width=2)
    
    m = 12
    draw.line([(x3, y1-m), (x3+m, y1-m), (x3+m, y1)], fill="#9333ea", width=2)
    
    draw.text(((x1+x2)//2 - 20, y1 + 12), f"a = {base}", fill="#0f172a", font=font_label)
    draw.text((x3 + 8, (y1+y3)//2), f"h = {height}", fill="#9333ea", font=font_label)
    return img


def draw_circle(rad="R", diam=None, title="Окружность / Круг"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy, r = 260, 210, 110
    
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#fee2e2", outline="#dc2626", width=4)
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
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy = 260, 280
    
    draw.line([(60, cy), (460, cy)], fill="#0f172a", width=4)
    ang = math.radians(65)
    rx = cx + 180 * math.cos(ang)
    ry = cy - 180 * math.sin(ang)
    draw.line([(cx, cy), (rx, ry)], fill="#2563eb", width=4)
    
    draw.arc([cx-60, cy-60, cx+60, cy+60], start=180, end=360-65, fill="#dc2626", width=3)
    draw.arc([cx-45, cy-45, cx+45, cy+45], start=360-65, end=360, fill="#16a34a", width=3)
    
    draw.text((cx - 80, cy - 40), str(a1), fill="#dc2626", font=font_label)
    draw.text((cx + 50, cy - 40), str(a2), fill="#16a34a", font=font_label)
    return img


def draw_clock(hour=3, title="Циферблат часов"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy, r = 260, 210, 110
    
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#ffffff", outline="#0f172a", width=4)
    draw.ellipse([cx-5, cy-5, cx+5, cy+5], fill="#0f172a")
    
    for h in [12, 3, 6, 9]:
        ang = math.radians(h * 30 - 90)
        nx = cx + (r - 25) * math.cos(ang) - 8
        ny = cy + (r - 25) * math.sin(ang) - 10
        draw.text((nx, ny), str(h), fill="#64748b", font=font_label)
        
    draw.line([(cx, cy), (cx, cy - r + 25)], fill="#0f172a", width=4)
    hang = math.radians(hour * 30 - 90)
    hx = cx + (r - 45) * math.cos(hang)
    hy = cy + (r - 45) * math.sin(hang)
    draw.line([(cx, cy), (hx, hy)], fill="#dc2626", width=6)
    
    angle_deg = (hour % 12) * 30
    if angle_deg > 180:
        angle_deg = 360 - angle_deg
    draw.text((25, 340), f"Угол между стрелками: {angle_deg}°", fill="#dc2626", font=font_label)
    return img


def generate_geometry_image(question_text: str, section_id: int = 10) -> bytes:
    """Интеллектуальная генерация графика (Раздел 9) или геометрического чертежа по условию (Раздел 10)"""
    text = question_text.lower()
    
    # 1. РАЗДЕЛ 9: ФУНКЦИИ И ГРАФИКИ
    if section_id == 9 or any(k in text for k in ["функци", "график", "парабол", "угловой коэффициент"]):
        # Поиск линейного уравнения вида y = kx + b
        lin_m = re.search(r'y\s*=\s*(-?\d*(?:\.\d+)?)\s*x\s*([\+\-]\s*\d+(?:\.\d+)?)?', text)
        quad_m = re.search(r'y\s*=\s*(-?\d*)\s*x[²2]\s*([\+\-]\s*\d+)?\s*x?\s*([\+\-]\s*\d+)?', text)
        
        if "²" in text or "x^2" in text or "парабол" in text:
            # Отрисовка параболы
            a_val, b_val = 1.0, 0.0
            if " - " in text and "x²" in text:
                b_val = -4.0
            img = draw_function_graph(eq_str="y = ax² + bx + c", func_type="quad", k=b_val, a=a_val)
        elif lin_m:
            k_str = lin_m.group(1)
            b_str = lin_m.group(2)
            k_val = float(k_str) if k_str not in ["", "-", "+"] else (-1.0 if k_str=="-" else 1.0)
            b_val = float(b_str.replace(" ", "")) if b_str else 0.0
            img = draw_function_graph(eq_str=f"y = {k_val}x + {b_val}", func_type="linear", k=k_val, b=b_val)
        else:
            img = draw_function_graph(eq_str="y = kx + b", func_type="linear", k=2.0, b=1.0)
            
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # 2. РАЗДЕЛ 10: ПЛАНИМЕТРИЯ (ГЕОМЕТРИЯ)
    nums = re.findall(r'\b\d+(?:[\.,]\d+)?\b', question_text)
    
    if "прямоугольник" in text and "треугольник" not in text:
        # Анализ условия на периметр / площадь / длину / ширину
        p_match = re.search(r'периметр[^\d]*(\d+)', text)
        s_match = re.search(r'площад[^\d]*(\d+)', text)
        l_match = re.search(r'длин[^\d]*(\d+)', text)
        w_match = re.search(r'ширин[^\d]*(\d+)', text)
        
        w_val = w_match.group(1) + " см" if w_match else ("?" if (p_match or s_match) and l_match else (nums[0]+" см" if len(nums)>0 else "a"))
        h_val = l_match.group(1) + " см" if l_match else ("?" if (p_match or s_match) and w_match else (nums[1]+" см" if len(nums)>1 else "b"))
        
        title = "Прямоугольник"
        if p_match:
            title = f"Прямоугольник (Периметр P = {p_match.group(1)})"
        elif s_match:
            title = f"Прямоугольник (Площадь S = {s_match.group(1)})"
            
        img = draw_rectangle(w_val, h_val, title)
        
    elif "квадрат" in text:
        p_match = re.search(r'периметр[^\d]*(\d+)', text)
        s_match = re.search(r'площад[^\d]*(\d+)', text)
        
        side = "a = ?" if (p_match or s_match) else (nums[0] + " см" if len(nums)>0 else "a")
        title = "Квадрат"
        if p_match:
            title = f"Квадрат (Периметр P = {p_match.group(1)})"
        elif s_match:
            title = f"Квадрат (Площадь S = {s_match.group(1)})"
            
        img = draw_square(side, title)
        
    elif "прямоугольн" in text and ("треугольник" in text or "катет" in text or "гипотенуз" in text):
        hyp_match = re.search(r'гипотенуз[^\d]*(\d+)', text)
        cat_matches = re.findall(r'катет[^\d]*(\d+)', text)
        
        if hyp_match and len(cat_matches) > 0:
            hyp_val = hyp_match.group(1) + " см"
            c1 = cat_matches[0] + " см"
            c2 = "?"
        elif len(cat_matches) >= 2:
            c1 = cat_matches[0] + " см"
            c2 = cat_matches[1] + " см"
            hyp_val = "?"
        else:
            c1 = nums[0] + " см" if len(nums)>0 else "a"
            c2 = nums[1] + " см" if len(nums)>1 else "b"
            hyp_val = nums[2] + " см" if len(nums)>2 else "c = ?"
            
        img = draw_right_triangle(c1, c2, hyp_val)
        
    elif "равносторон" in text and "треугольник" in text:
        side = nums[0] + " см" if len(nums) > 0 else "a"
        img = draw_triangle(side, "h", "Равносторонний треугольник")
        
    elif "треугольник" in text:
        b = nums[0] + " см" if len(nums) > 0 else "a"
        h = nums[1] + " см" if len(nums) > 1 else "h"
        img = draw_triangle(b, h)
        
    elif any(k in text for k in ["окружност", "круг", "радиус", "диаметр"]):
        d_match = re.search(r'диаметр[^\d]*(\d+)', text)
        r_match = re.search(r'радиус[^\d]*(\d+)', text)
        
        if d_match:
            img = draw_circle(rad="?", diam=d_match.group(1) + " см")
        elif r_match:
            img = draw_circle(rad=r_match.group(1) + " см")
        else:
            r = nums[0] + " см" if len(nums) > 0 else "R"
            img = draw_circle(rad=r)
            
    elif "смежн" in text:
        a1 = nums[0] + "°" if len(nums) > 0 else "α"
        a2 = "?" if len(nums) > 0 else "β"
        img = draw_adjacent_angles(a1, a2)
        
    elif any(k in text for k in ["час", "стрелк", "циферблат"]):
        hr = int(nums[0]) if len(nums) > 0 and int(nums[0]) <= 12 else 3
        img = draw_clock(hr)
        
    else:
        img = draw_rectangle("a", "b", "Геометрический чертеж")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
