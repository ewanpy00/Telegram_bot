#!/usr/bin/env python3
"""
Скрипт для сохранения состояния авторизации (storageState)
Запустите один раз, авторизуйтесь вручную, и состояние сохранится
"""

import asyncio
import json
import os
from playwright.async_api import async_playwright

async def save_auth_state():
    """
    Сохраняет состояние авторизации в файл
    """
    print("🔐 Сохранение состояния авторизации...")
    
    try:
        async with async_playwright() as p:
            # Запускаем браузер в видимом режиме
            browser = await p.firefox.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🌐 Переходим на https://makefilm.ai...")
            await page.goto("https://makefilm.ai", wait_until='networkidle')
            
            print("\n" + "="*60)
            print("📝 ИНСТРУКЦИЯ ПО АВТОРИЗАЦИИ:")
            print("="*60)
            print("1. Авторизуйтесь на сайте makefilm.ai")
            print("2. Используйте любой способ входа (Google, OAuth, email/password)")
            print("3. Убедитесь, что вы успешно вошли в аккаунт")
            print("4. Перейдите на страницу генератора изображений:")
            print("   https://makefilm.ai/workspace/image-generator")
            print("5. Убедитесь, что страница загрузилась корректно")
            print("6. Вернитесь в терминал и нажмите Enter")
            print("="*60)
            
            # Ждем, пока пользователь авторизуется
            input("\nНажмите Enter после успешной авторизации...")
            
            # Проверяем, что мы авторизованы
            current_url = page.url
            print(f"📄 Текущий URL: {current_url}")
            
            # Проверяем индикаторы авторизации
            auth_indicators = [
                'a[href*="workspace"]',
                'a[href*="profile"]',
                'button:has-text("Logout")',
                '.user-menu',
                '[data-testid="user-menu"]'
            ]
            
            is_authenticated = False
            for indicator in auth_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        is_authenticated = True
                        print(f"✅ Найден индикатор авторизации: {indicator}")
                        break
                except:
                    continue
            
            if not is_authenticated:
                print("⚠️ Авторизация не обнаружена, но продолжаем...")
            
            # Сохраняем состояние браузера
            storage_state_file = "auth_state.json"
            await context.storage_state(path=storage_state_file)
            
            print(f"✅ Состояние авторизации сохранено в файл: {storage_state_file}")
            
            # Также сохраняем cookies для совместимости
            cookies = await context.cookies()
            cookies_file = "cookies.json"
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Cookies также сохранены в файл: {cookies_file}")
            
            print("\n🎉 Авторизация успешно сохранена!")
            print("🚀 Теперь можно запускать основного бота:")
            print("python3 bot_with_storage.py")
            
            # Ждем, чтобы пользователь мог посмотреть
            input("\nНажмите Enter для закрытия браузера...")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(save_auth_state())
