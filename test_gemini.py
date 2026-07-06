import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

# Проверяем доступные модели
print("Доступные модели:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"- {model.name}")

# Тестируем генерацию
try:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    response = model.generate_content("Привет! Ответь одним словом: работает?")
    print(f"\nОтвет: {response.text}")
except Exception as e:
    print(f"\nОшибка: {e}")