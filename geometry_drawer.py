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


def extract_num(s):
    if not s:
        return None
    nums = re.findall(r'\d+(?:[\.,]\d+)?', str(s))
    if nums:
        try:
            return float(nums[0].replace(',', '.'))
        except Exception:
            pass
    return None


def compute_dynamic_box(val_x, val_y, center=(260, 195), max_w=320, max_h=240, min_w=100, min_h=80):
    """Вычисляет пропорциональные координаты рамки фигуры, чтобы длинная сторона была длинной, а короткая — короткой"""
    if not val_x or not val_y or val_x <= 0 or val_y <= 0:
        return 110, 90, 410, 270
    
    ratio = val_x / val_y
    if (max_w / ratio) <= max_h:
        w = max_w
        h = max_w / ratio
    else:
        h = max_h
        w = max_h * ratio
        
    w = max(int(w), min_w)
    h = max(int(h), min_h)
    
    cx, cy = center
    return cx - w//2, cy - h//2, cx + w//2, cy + h//2


# --- ОТРИСОВКА ГРАФИКОВ ФУНКЦИЙ (РАЗДЕЛ 9) ---

def draw_function_graph(eq_str="y = kx + b", func_type="linear", k=1.0, b=0.0, a=1.0):
    img = Image.new("RGB", (520, 400), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(20)
    font_sm = get_font(14)
    
    draw.text((20, 15), f"График: {eq_str}", fill="#0f172a", font=font_title)
    
    ox, oy = 260, 220
    scale = 20
    
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
            
    draw.line([(495, oy-5), (500, oy), (495, oy+5)], fill="#0f172a", width=2)
    draw.line([(ox-5, 53), (ox, 48), (ox+5, 53)], fill="#0f172a", width=2)
    draw.text((485, oy - 25), "x", fill="#0f172a", font=font_title)
    draw.text((ox + 10, 48), "y", fill="#0f172a", font=font_title)
    draw.text((ox - 15, oy + 5), "0", fill="#0f172a", font=font_sm)
    
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
        
    if func_type == "linear":
        py_int = oy - b * scale
        if 48 <= py_int <= 385:
            draw.ellipse([ox-5, py_int-5, ox+5, py_int+5], fill="#dc2626")
    else:
        vx = -k / (2 * a) if a != 0 else 0
        vy = a * (vx**2) + k * vx + b
        px_v = ox + vx * scale
        py_v = oy - vy * scale
        if 48 <= py_v <= 385 and 20 <= px_v <= 500:
            draw.ellipse([px_v-5, py_v-5, px_v+5, py_v+5], fill="#dc2626")
            draw.text((px_v + 8, py_v - 10), f"({round(vx,1)}; {round(vy,1)})", fill="#dc2626", font=font_sm)
            
    return img


# --- ОТРИСОВКА ЗАДАЧ НА УГЛЫ ---

def draw_triangle_angles(a1="90°", a2="35°", a3="?", title="Углы треугольника (Сумма 180°)"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1 = 120, 310
    x2, y2 = 420, 310
    x3, y3 = 120, 90
    
    draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill="#fef9c3", outline="#ca8a04", width=4)
    
    if "90" in str(a1):
        m = 22
        draw.line([(x1+m, y1), (x1+m, y1-m), (x1, y1-m)], fill="#dc2626", width=3)
        draw.text((x1 + 8, y1 - 32), "90°", fill="#dc2626", font=font_label)
    else:
        draw.text((x1 + 10, y1 - 30), str(a1), fill="#dc2626", font=font_label)
        
    draw.arc([x2-80, y2-80, x2+80, y2+80], start=180, end=216, fill="#2563eb", width=3)
    draw.text((x2 - 110, y2 - 35), str(a2), fill="#2563eb", font=font_label)
    
    draw.arc([x3-60, y3-60, x3+60, y3+60], start=0, end=54, fill="#16a34a", width=3)
    draw.text((x3 + 20, y3 + 35), str(a3), fill="#16a34a", font=font_label)
    return img


def draw_isosceles_angles(base_ang="50°", vert_ang="?", title="Равнобедренный треугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1 = 100, 310
    x2, y2 = 420, 310
    x3, y3 = 260, 80
    
    draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill="#f3e8ff", outline="#9333ea", width=4)
    
    draw.line([((x1+x3)//2 - 10, (y1+y3)//2 - 5), ((x1+x3)//2 + 5, (y1+y3)//2 + 10)], fill="#9333ea", width=3)
    draw.line([((x2+x3)//2 - 5, (y2+y3)//2 + 10), ((x2+x3)//2 + 10, (y2+y3)//2 - 5)], fill="#9333ea", width=3)
    
    draw.arc([x1-50, y1-50, x1+50, y1+50], start=305, end=360, fill="#2563eb", width=3)
    draw.arc([x2-50, y2-50, x2+50, y2+50], start=180, end=235, fill="#2563eb", width=3)
    draw.text((x1 + 45, y1 - 25), str(base_ang), fill="#2563eb", font=font_label)
    draw.text((x2 - 85, y2 - 25), str(base_ang), fill="#2563eb", font=font_label)
    
    draw.arc([x3-50, y3-50, x3+50, y3+50], start=55, end=125, fill="#dc2626", width=3)
    draw.text((x3 - 15, y3 + 50), str(vert_ang), fill="#dc2626", font=font_label)
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
    
    draw.text((cx - 95, cy - 45), str(a1), fill="#dc2626", font=font_label)
    draw.text((cx + 55, cy - 45), str(a2), fill="#16a34a", font=font_label)
    return img


def draw_vertical_angles(a1="α", a2="β", title="Вертикальные углы (Равны друг другу)"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy = 260, 200
    
    draw.line([(80, 320), (440, 80)], fill="#0f172a", width=4)
    draw.line([(80, 80), (440, 320)], fill="#0f172a", width=4)
    
    draw.arc([cx-50, cy-50, cx+50, cy+50], start=360-33, end=33, fill="#dc2626", width=3)
    draw.arc([cx-50, cy-50, cx+50, cy+50], start=180-33, end=180+33, fill="#dc2626", width=3)
    
    draw.text((cx - 95, cy - 12), str(a1), fill="#dc2626", font=font_label)
    draw.text((cx + 60, cy - 12), str(a2), fill="#dc2626", font=font_label)
    return img


def draw_angle_bisector(total="80°", half="?", title="Биссектриса угла (Делит угол пополам)"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    cx, cy = 120, 290
    
    draw.line([(cx, cy), (440, cy)], fill="#0f172a", width=4)
    ang_tot = math.radians(70)
    rx = cx + 280 * math.cos(ang_tot)
    ry = cy - 280 * math.sin(ang_tot)
    draw.line([(cx, cy), (rx, ry)], fill="#0f172a", width=4)
    
    ang_half = math.radians(35)
    bx = cx + 290 * math.cos(ang_half)
    by = cy - 290 * math.sin(ang_half)
    draw.line([(cx, cy), (bx, by)], fill="#16a34a", width=3)
    
    draw.arc([cx-70, cy-70, cx+70, cy+70], start=360-70, end=360-35, fill="#2563eb", width=3)
    draw.arc([cx-55, cy-55, cx+55, cy+55], start=360-35, end=360, fill="#2563eb", width=3)
    
    draw.text((cx + 80, cy - 85), f"Половина = {half}", fill="#16a34a", font=font_label)
    draw.text((cx + 90, cy - 30), f"Половина = {half}", fill="#16a34a", font=font_label)
    draw.text((25, 340), f"Весь угол = {total}", fill="#0f172a", font=font_label)
    return img


def draw_quadrilateral_angles(a1="80°", a2="90°", a3="100°", a4="?", title="Углы четырехугольника (Сумма 360°)"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    x1, y1 = 110, 300
    x2, y2 = 410, 300
    x3, y3 = 340, 100
    x4, y4 = 160, 120
    
    draw.polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], fill="#e0f2fe", outline="#0284c7", width=4)
    
    draw.text((x1 + 15, y1 - 35), str(a1), fill="#0f172a", font=font_label)
    draw.text((x2 - 55, y2 - 35), str(a2), fill="#0f172a", font=font_label)
    draw.text((x3 - 55, y3 + 15), str(a3), fill="#0f172a", font=font_label)
    draw.text((x4 + 15, y4 + 15), str(a4), fill="#dc2626", font=font_label)
    return img


def draw_parallelogram_angles(acute="60°", obtuse="?", title="Углы параллелограмма / Ромба"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    shift = 90
    x1, y1 = 120, 290
    x2, y2 = 410, 290
    x3, y3 = 410 + shift, 110
    x4, y4 = 120 + shift, 110
    
    draw.polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], fill="#dcfce7", outline="#16a34a", width=4)
    
    draw.text((x1 + 25, y1 - 32), str(acute), fill="#2563eb", font=font_label)
    draw.text((x3 - 65, y3 + 12), str(acute), fill="#2563eb", font=font_label)
    draw.text((x2 - 45, y2 - 32), str(obtuse), fill="#dc2626", font=font_label)
    draw.text((x4 + 15, y4 + 12), str(obtuse), fill="#dc2626", font=font_label)
    return img


# --- ОСНОВНЫЕ ФИГУРЫ С ДИНАМИЧЕСКИМИ ПРОПОРЦИЯМИ ---

def draw_rectangle(w_text="a", h_text="b", title="Прямоугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    
    val_w = extract_num(w_text)
    val_h = extract_num(h_text)
    x1, y1, x2, y2 = compute_dynamic_box(val_w, val_h)
    
    draw.rectangle([x1, y1, x2, y2], fill="#e0f2fe", outline="#0284c7", width=4)
    
    m = min(15, (x2-x1)//4, (y2-y1)//4)
    for (cx, cy, dx, dy) in [(x1, y1, 1, 1), (x2, y1, -1, 1), (x2, y2, -1, -1), (x1, y2, 1, -1)]:
        draw.line([(cx + dx*m, cy), (cx + dx*m, cy + dy*m), (cx, cy + dy*m)], fill="#0284c7", width=2)
        
    draw.text(((x1+x2)//2 - 25, y2 + 10), str(w_text), fill="#0f172a", font=font_label)
    draw.text((x2 + 12, (y1+y2)//2 - 10), str(h_text), fill="#0f172a", font=font_label)
    return img


def draw_square(side_text="a", title="Квадрат"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    val_s = extract_num(side_text)
    x1, y1, x2, y2 = compute_dynamic_box(val_s, val_s)
    
    draw.rectangle([x1, y1, x2, y2], fill="#dcfce7", outline="#16a34a", width=4)
    
    for (lx1, ly1, lx2, ly2) in [
        (((x1+x2)//2 - 5, y1 - 5), ((x1+x2)//2 + 5, y1 + 5)),
        (((x1+x2)//2 - 5, y2 - 5), ((x1+x2)//2 + 5, y2 + 5)),
        ((x1 - 5, (y1+y2)//2 - 5), (x1 + 5, (y1+y2)//2 + 5)),
        ((x2 - 5, (y1+y2)//2 - 5), (x2 + 5, (y1+y2)//2 + 5))
    ]:
        draw.line([lx1, lx2], fill="#16a34a", width=3)
        
    draw.text(((x1+x2)//2 - 20, y2 + 12), str(side_text), fill="#0f172a", font=font_label)
    draw.text((x2 + 12, (y1+y2)//2 - 10), str(side_text), fill="#0f172a", font=font_label)
    return img


def draw_right_triangle(cat1="a", cat2="b", hypot="c", title="Прямоугольный треугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    
    val_c1 = extract_num(cat1)
    val_c2 = extract_num(cat2)
    x1, y1, x2, y2 = compute_dynamic_box(val_c1, val_c2)
    
    x3, y3 = x1, y1
    draw.polygon([(x1, y2), (x2, y2), (x3, y3)], fill="#fef9c3", outline="#ca8a04", width=4)
    
    m = min(20, (x2-x1)//4, (y2-y3)//4)
    draw.line([(x1+m, y2), (x1+m, y2-m), (x1, y2-m)], fill="#ca8a04", width=2)
    
    draw.text(((x1+x2)//2 - 20, y2 + 10), str(cat1), fill="#0f172a", font=font_label)
    draw.text((x1 - 65, (y2+y3)//2), str(cat2), fill="#0f172a", font=font_label)
    draw.text(((x2+x3)//2 + 15, (y2+y3)//2 - 15), str(hypot), fill="#0f172a", font=font_label)
    return img


def draw_triangle(base="a", height="h", title="Треугольник"):
    img = Image.new("RGB", (520, 380), color="#f8fafc")
    draw = ImageDraw.Draw(img)
    font_title = get_font(21)
    font_label = get_font(18)
    
    draw.text((25, 20), title, fill="#0f172a", font=font_title)
    val_b = extract_num(base)
    val_h = extract_num(height)
    x1, y1, x2, y2 = compute_dynamic_box(val_b, val_h)
    
    x3, y3 = (x1+x2)//2, y1
    draw.polygon([(x1, y2), (x2, y2), (x3, y3)], fill="#f3e8ff", outline="#9333ea", width=4)
    draw.line([(x3, y3), (x3, y2)], fill="#9333ea", width=2)
    
    m = min(12, (x2-x1)//6, (y2-y3)//6)
    draw.line([(x3, y2-m), (x3+m, y2-m), (x3+m, y2)], fill="#9333ea", width=2)
    
    draw.text(((x1+x2)//2 - 20, y2 + 10), f"a = {base}", fill="#0f172a", font=font_label)
    draw.text((x3 + 8, (y2+y3)//2), f"h = {height}", fill="#9333ea", font=font_label)
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
    if angle_deg > 180: angle_deg = 360 - angle_deg
    draw.text((25, 340), f"Угол между стрелками: {angle_deg}°", fill="#dc2626", font=font_label)
    return img


def generate_geometry_image(question_text: str, section_id: int = 10) -> bytes:
    """Интеллектуальная генерация графика (Раздел 9) или пропорционального чертежа (Раздел 10)"""
    text = question_text.lower()
    nums = re.findall(r'\b\d+(?:[\.,]\d+)?\b', question_text)
    
    # 1. РАЗДЕЛ 9: ФУНКЦИИ И ГРАФИКИ
    if section_id == 9 or any(k in text for k in ["функци", "график", "парабол", "угловой коэффициент"]):
        lin_m = re.search(r'y\s*=\s*(-?\d*(?:\.\d+)?)\s*x\s*([\+\-]\s*\d+(?:\.\d+)?)?', text)
        if "²" in text or "x^2" in text or "парабол" in text:
            a_val, b_val = 1.0, 0.0
            if " - " in text and "x²" in text: b_val = -4.0
            img = draw_function_graph("y = ax² + bx + c", "quad", b_val, 0.0, a_val)
        elif lin_m:
            k_str, b_str = lin_m.group(1), lin_m.group(2)
            k_val = float(k_str) if k_str not in ["", "-", "+"] else (-1.0 if k_str=="-" else 1.0)
            b_val = float(b_str.replace(" ", "")) if b_str else 0.0
            img = draw_function_graph(f"y = {k_val}x + {b_val}", "linear", k_val, b_val)
        else:
            img = draw_function_graph("y = kx + b", "linear", 2.0, 1.0)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # 2. РАЗДЕЛ 10: ПЛАНИМЕТРИЯ — УГЛЫ
    if "угл" in text or "°" in question_text or "смежн" in text or "вертикальн" in text or "биссектрис" in text:
        if "смежн" in text:
            if "в 4 раза" in text:
                img = draw_adjacent_angles("x", "4x", "Смежные углы (Сумма 180° = x + 4x)")
            elif len(nums) > 0:
                val = float(nums[0].replace(',', '.'))
                if val < 90: img = draw_adjacent_angles(f"{nums[0]}°", "?")
                else: img = draw_adjacent_angles("?", f"{nums[0]}°")
            else:
                img = draw_adjacent_angles("α", "β")
        elif "вертикальн" in text:
            val = nums[0] + "°" if len(nums) > 0 else "α"
            img = draw_vertical_angles(val, val)
        elif "биссектрис" in text:
            if "развернут" in text: img = draw_angle_bisector("180°", "90°", "Биссектриса развернутого угла")
            else: img = draw_angle_bisector(nums[0]+"°" if len(nums)>0 else "80°", "?")
        elif "равнобедрен" in text and "угл" in text:
            base = nums[0]+"°" if len(nums)>0 else "50°"
            img = draw_isosceles_angles(base, "?")
        elif "четырехугольник" in text and "угл" in text:
            img = draw_quadrilateral_angles(nums[0]+"°" if len(nums)>0 else "80°", nums[1]+"°" if len(nums)>1 else "90°", nums[2]+"°" if len(nums)>2 else "100°", "?")
        elif any(k in text for k in ["ромб", "параллелограмм"]) and "угл" in text:
            img = draw_parallelogram_angles(nums[0]+"°" if len(nums)>0 else "60°", "?")
        elif "треугольник" in text and ("90°" in question_text or "прямоугольн" in text):
            ang2 = nums[0]+"°" if len(nums)>0 and nums[0]!="90" else (nums[1]+"°" if len(nums)>1 else "35°")
            img = draw_triangle_angles("90°", ang2, "?")
        elif any(k in text for k in ["час", "стрелк", "циферблат"]):
            hr = int(nums[0]) if len(nums) > 0 and int(nums[0]) <= 12 else 3
            img = draw_clock(hr)
        else:
            img = draw_triangle_angles("α", "β", "?", "Углы в геометрии")
            
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # 3. РАЗДЕЛ 10: ПЛАНИМЕТРИЯ — ФИГУРЫ С ПРОПОРЦИЯМИ
    if "прямоугольник" in text and "треугольник" not in text:
        p_m = re.search(r'периметр[^\d]*(\d+(?:[\.,]\d+)?)', text)
        s_m = re.search(r'площад[^\d]*(\d+(?:[\.,]\d+)?)', text)
        l_m = re.search(r'длин[^\d]*(\d+(?:[\.,]\d+)?)', text)
        w_m = re.search(r'ширин[^\d]*(\d+(?:[\.,]\d+)?)', text)
        
        w_val = w_m.group(1)+" см" if w_m else ("?" if (p_m or s_m) and l_m else (nums[0]+" см" if len(nums)>0 else "a"))
        h_val = l_m.group(1)+" см" if l_m else ("?" if (p_m or s_m) and w_m else (nums[1]+" см" if len(nums)>1 else "b"))
        
        title = "Прямоугольник"
        if p_m: title = f"Прямоугольник (Периметр P = {p_m.group(1)})"
        elif s_m: title = f"Прямоугольник (Площадь S = {s_m.group(1)})"
        img = draw_rectangle(w_val, h_val, title)
        
    elif "квадрат" in text:
        p_m = re.search(r'периметр[^\d]*(\d+(?:[\.,]\d+)?)', text)
        s_m = re.search(r'площад[^\d]*(\d+(?:[\.,]\d+)?)', text)
        side = "a = ?" if (p_m or s_m) else (nums[0]+" см" if len(nums)>0 else "a")
        title = f"Квадрат (P = {p_m.group(1)})" if p_m else (f"Квадрат (S = {s_m.group(1)})" if s_m else "Квадрат")
        img = draw_square(side, title)
        
    elif "прямоугольн" in text and ("треугольник" in text or "катет" in text or "гипотенуз" in text):
        hyp_m = re.search(r'гипотенуз[^\d]*(\d+(?:[\.,]\d+)?)', text)
        cats = re.findall(r'катет[^\d]*(\d+(?:[\.,]\d+)?)', text)
        if hyp_m and len(cats)>0: img = draw_right_triangle(cats[0]+" см", "?", hyp_m.group(1)+" см")
        elif len(cats)>=2: img = draw_right_triangle(cats[0]+" см", cats[1]+" см", "?")
        else: img = draw_right_triangle(nums[0]+" см" if len(nums)>0 else "a", nums[1]+" см" if len(nums)>1 else "b", nums[2]+" см" if len(nums)>2 else "c = ?")
        
    elif "равносторон" in text and "треугольник" in text:
        side = nums[0]+" см" if len(nums)>0 else "a"
        img = draw_triangle(side, side, "Равносторонний треугольник")
        
    elif "треугольник" in text:
        b = nums[0]+" см" if len(nums)>0 else "a"
        h = nums[1]+" см" if len(nums)>1 else "h"
        img = draw_triangle(b, h)
        
    elif any(k in text for k in ["окружност", "круг", "радиус", "диаметр"]):
        d_m = re.search(r'диаметр[^\d]*(\d+(?:[\.,]\d+)?)', text)
        r_m = re.search(r'радиус[^\d]*(\d+(?:[\.,]\d+)?)', text)
        if d_m: img = draw_circle(rad="?", diam=d_m.group(1)+" см")
        elif r_m: img = draw_circle(rad=r_m.group(1)+" см")
        else: img = draw_circle(rad=nums[0]+" см" if len(nums)>0 else "R")
        
    else:
        img = draw_rectangle("a", "b", "Геометрический чертеж")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
