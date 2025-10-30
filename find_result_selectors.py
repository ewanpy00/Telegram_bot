#!/usr/bin/env python3
"""
Скрипт для поиска селекторов готовых изображений на makefilm.ai
"""

import asyncio
from playwright.async_api import async_playwright

async def find_result_selectors():
    """
    Ищет селекторы для готовых изображений после генерации
    """
    print("🔍 Поиск селекторов для готовых изображений...")
    
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
            
            # Переходим на страницу генератора
            print("🌐 Переходим на https://makefilm.ai/workspace/image-generator...")
            await page.goto("https://makefilm.ai/workspace/image-generator", wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            print("\n" + "="*60)
            print("📝 ИНСТРУКЦИЯ:")
            print("="*60)
            print("1. Введите тестовый промпт в поле ввода")
            print("2. Нажмите кнопку Generate")
            print("3. Дождитесь появления готового изображения")
            print("4. Вернитесь в терминал и нажмите Enter")
            print("="*60)
            
            # Ждем, пока пользователь сгенерирует изображение
            input("\nНажмите Enter после генерации изображения...")
            
            print("\n🔍 Анализируем страницу на предмет готовых изображений...")
            
            # Ищем все ссылки
            print("\n🔗 ВСЕ ССЫЛКИ НА СТРАНИЦЕ:")
            links = await page.query_selector_all('a')
            for i, link in enumerate(links):
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and ('image' in href.lower() or 'jpg' in href.lower() or 'png' in href.lower() or 'download' in href.lower()):
                        print(f"  {i+1}. {href} - текст: '{text.strip()}'")
                except:
                    pass
            
            # Ищем все изображения
            print("\n🖼️ ВСЕ ИЗОБРАЖЕНИЯ НА СТРАНИЦЕ:")
            images = await page.query_selector_all('img')
            for i, img in enumerate(images):
                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt')
                    if src:
                        print(f"  {i+1}. {src} - alt: '{alt}'")
                except:
                    pass
            
            # Ищем кнопки скачивания
            print("\n⬇️ КНОПКИ СКАЧИВАНИЯ:")
            buttons = await page.query_selector_all('button, a')
            for i, button in enumerate(buttons):
                try:
                    text = await button.inner_text()
                    if text and ('download' in text.lower() or 'скачать' in text.lower() or 'save' in text.lower()):
                        print(f"  {i+1}. '{text.strip()}'")
                except:
                    pass
            
            print("\n" + "="*60)
            print("📋 РЕКОМЕНДУЕМЫЕ СЕЛЕКТОРЫ:")
            print("="*60)
            
            # Предлагаем селекторы на основе найденных элементов
            print("\nДля ссылок на изображения:")
            print('result_selectors = [')
            print('    "a[href*=\\"image\\"]",')
            print('    "a[href*=\\"jpg\\"]",')
            print('    "a[href*=\\"png\\"]",')
            print('    "a[href*=\\"download\\"]",')
            print('    ".download-link",')
            print('    ".result-image a"')
            print(']')
            
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
    asyncio.run(find_result_selectors())
