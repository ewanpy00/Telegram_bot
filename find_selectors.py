#!/usr/bin/env python3
"""
Скрипт для поиска CSS-селекторов на сайте makefilm.ai
"""

import asyncio
from playwright.async_api import async_playwright

async def find_selectors():
    """
    Ищет подходящие CSS-селекторы на сайте makefilm.ai
    """
    print("🔍 Поиск CSS-селекторов на makefilm.ai...")
    
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
            
            # Переходим на сайт
            print("🌐 Переходим на makefilm.ai...")
            await page.goto("https://makefilm.ai", wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            print("\n" + "="*60)
            print("🔍 ПОИСК СЕЛЕКТОРОВ:")
            print("="*60)
            
            # Ищем поля ввода
            print("\n📝 ПОЛЯ ВВОДА:")
            input_selectors = [
                'input[type="text"]',
                'input[type="search"]',
                'textarea',
                '[contenteditable="true"]',
                'input[placeholder*="prompt"]',
                'input[placeholder*="text"]',
                'input[placeholder*="describe"]',
                '.prompt-input',
                '.text-input',
                '#prompt',
                '#text-input'
            ]
            
            for selector in input_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        placeholder = await element.get_attribute('placeholder')
                        print(f"✅ {selector} - placeholder: {placeholder}")
                except:
                    pass
            
            # Ищем кнопки
            print("\n🔘 КНОПКИ:")
            button_selectors = [
                'button[type="submit"]',
                'button:has-text("Generate")',
                'button:has-text("Create")',
                'button:has-text("Submit")',
                'button:has-text("Send")',
                '.generate-btn',
                '.create-btn',
                '.submit-btn',
                '#generate',
                '#create',
                '#submit'
            ]
            
            for selector in button_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        print(f"✅ {selector} - текст: {text}")
                except:
                    pass
            
            # Ищем ссылки на результаты
            print("\n🔗 ССЫЛКИ НА РЕЗУЛЬТАТЫ:")
            result_selectors = [
                'a[href*="image"]',
                'a[href*="photo"]',
                'a[href*="jpg"]',
                'a[href*="png"]',
                'a[href*="gif"]',
                'a[href*="result"]',
                'a[href*="download"]',
                '.result-link',
                '.download-link',
                '.image-link',
                '[data-result-url]',
                '[data-image-url]'
            ]
            
            for selector in result_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ {selector} - найдено: {len(elements)} элементов")
                except:
                    pass
            
            print("\n" + "="*60)
            print("📋 ИНСТРУКЦИЯ:")
            print("="*60)
            print("1. Скопируйте подходящие селекторы из списка выше")
            print("2. Вставьте их в файл bot.py вместо TODO комментариев")
            print("3. Если селекторы не работают, используйте DevTools:")
            print("   - F12 → Elements → правый клик на элементе")
            print("   - Copy → Copy selector")
            print("="*60)
            
            # Ждем, чтобы пользователь мог посмотреть
            input("\nНажмите Enter для закрытия браузера...")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(find_selectors())
