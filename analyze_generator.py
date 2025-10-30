#!/usr/bin/env python3
"""
Скрипт для анализа страницы генератора изображений makefilm.ai
"""

import asyncio
from playwright.async_api import async_playwright

async def analyze_image_generator():
    """
    Анализирует страницу генератора изображений и находит селекторы
    """
    print("🔍 Анализ страницы генератора изображений makefilm.ai...")
    
    try:
        async with async_playwright() as p:
            # Запускаем браузер в видимом режиме
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Загружаем cookies
            try:
                with open('cookies.json', 'r') as f:
                    import json
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
                    print("✅ Cookies загружены")
            except:
                print("⚠️ Cookies не найдены, продолжаем без авторизации")
            
            # Переходим на страницу генератора изображений
            print("🌐 Переходим на https://makefilm.ai/workspace/image-generator...")
            await page.goto("https://makefilm.ai/workspace/image-generator", wait_until='networkidle')
            await page.wait_for_timeout(5000)
            
            print("\n" + "="*60)
            print("🔍 АНАЛИЗ СТРАНИЦЫ ГЕНЕРАТОРА ИЗОБРАЖЕНИЙ:")
            print("="*60)
            
            # Получаем заголовок страницы
            title = await page.title()
            print(f"📄 Заголовок страницы: {title}")
            
            # Ищем все поля ввода
            print("\n📝 ПОЛЯ ВВОДА:")
            input_elements = await page.query_selector_all('input, textarea, [contenteditable="true"]')
            
            for i, element in enumerate(input_elements):
                try:
                    tag_name = await element.evaluate('el => el.tagName')
                    input_type = await element.get_attribute('type')
                    placeholder = await element.get_attribute('placeholder')
                    class_name = await element.get_attribute('class')
                    id_name = await element.get_attribute('id')
                    
                    print(f"  {i+1}. {tag_name}")
                    if input_type:
                        print(f"     Тип: {input_type}")
                    if placeholder:
                        print(f"     Placeholder: {placeholder}")
                    if class_name:
                        print(f"     Класс: {class_name}")
                    if id_name:
                        print(f"     ID: {id_name}")
                    print()
                except:
                    pass
            
            # Ищем все кнопки
            print("\n🔘 КНОПКИ:")
            button_elements = await page.query_selector_all('button, input[type="submit"], input[type="button"]')
            
            for i, element in enumerate(button_elements):
                try:
                    text = await element.inner_text()
                    class_name = await element.get_attribute('class')
                    id_name = await element.get_attribute('id')
                    button_type = await element.get_attribute('type')
                    
                    if text.strip():  # Показываем только кнопки с текстом
                        print(f"  {i+1}. Текст: '{text.strip()}'")
                        if button_type:
                            print(f"     Тип: {button_type}")
                        if class_name:
                            print(f"     Класс: {class_name}")
                        if id_name:
                            print(f"     ID: {id_name}")
                        print()
                except:
                    pass
            
            # Ищем ссылки на изображения
            print("\n🔗 ССЫЛКИ НА ИЗОБРАЖЕНИЯ:")
            link_elements = await page.query_selector_all('a')
            
            image_links = []
            for element in link_elements:
                try:
                    href = await element.get_attribute('href')
                    if href and any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', 'image', 'photo']):
                        image_links.append(href)
                        print(f"  • {href}")
                except:
                    pass
            
            if not image_links:
                print("  Ссылки на изображения не найдены (возможно, нужно сгенерировать изображение)")
            
            print("\n" + "="*60)
            print("📋 РЕКОМЕНДУЕМЫЕ СЕЛЕКТОРЫ:")
            print("="*60)
            
            # Предлагаем селекторы на основе найденных элементов
            print("\nДля поля ввода промпта:")
            print('prompt_input_selector = "input[type=\\"text\\"]"')
            print('prompt_input_selector = "textarea"')
            print('prompt_input_selector = "[contenteditable=\\"true\\"]"')
            
            print("\nДля кнопки генерации:")
            print('generate_button_selector = "button[type=\\"submit\\"]"')
            print('generate_button_selector = "button:has-text(\\"Generate\\")"')
            print('generate_button_selector = "button:has-text(\\"Create\\")"')
            
            print("\nДля ссылок на результаты:")
            print('result_selectors = ["a[href*=\\"image\\"]", "a[href*=\\"jpg\\"]", "a[href*=\\"png\\"]"]')
            
            print("\n" + "="*60)
            print("📝 ИНСТРУКЦИЯ:")
            print("="*60)
            print("1. Скопируйте подходящие селекторы из списка выше")
            print("2. Вставьте их в файл bot.py вместо TODO комментариев")
            print("3. Если селекторы не работают:")
            print("   - F12 → Elements → правый клик на элементе")
            print("   - Copy → Copy selector")
            print("="*60)
            
            # Ждем, чтобы пользователь мог посмотреть
            input("\nНажмите Enter для закрытия браузера...")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_image_generator())
