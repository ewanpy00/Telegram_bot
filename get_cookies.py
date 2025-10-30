#!/usr/bin/env python3
"""
Скрипт для получения cookies с сайта makefilm.ai
Запустите этот скрипт, авторизуйтесь на сайте вручную, и cookies будут сохранены
"""

import json
import os
import asyncio
from playwright.async_api import async_playwright

async def get_cookies():
    """
    Получает cookies с сайта makefilm.ai после ручной авторизации
    """
    print("🚀 Запуск браузера для получения cookies...")
    
    try:
        async with async_playwright() as p:
            # Запускаем браузер в видимом режиме
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Переходим на сайт makefilm.ai
                print("🌐 Переходим на https://makefilm.ai...")
                await page.goto("https://makefilm.ai", wait_until='networkidle')
                
                print("\n" + "="*60)
                print("📝 ИНСТРУКЦИЯ:")
                print("1. Авторизуйтесь на сайте makefilm.ai в открывшемся браузере")
                print("2. Убедитесь, что вы успешно вошли в аккаунт")
                print("3. Вернитесь в терминал и нажмите Enter")
                print("="*60 + "\n")
                
                # Ждем, пока пользователь авторизуется
                input("Нажмите Enter после успешной авторизации...")
                
                # Получаем все cookies
                cookies = await context.cookies()
                
                if cookies:
                    # Сохраняем cookies в файл
                    cookies_file = "cookies.json"
                    with open(cookies_file, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Cookies успешно сохранены в файл: {cookies_file}")
                    print(f"📊 Сохранено {len(cookies)} cookies")
                    
                    # Показываем информацию о cookies
                    print("\n📋 Информация о сохраненных cookies:")
                    for cookie in cookies:
                        print(f"  • {cookie['name']}: {cookie['domain']}")
                        
                else:
                    print("❌ Cookies не найдены. Убедитесь, что вы авторизованы на сайте.")
                    
            except Exception as e:
                print(f"❌ Ошибка при получении cookies: {e}")
                
            finally:
                # Закрываем браузер
                await browser.close()
                print("\n🔒 Браузер закрыт.")
                
    except Exception as e:
        print(f"❌ Ошибка при запуске браузера: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(get_cookies())
    except KeyboardInterrupt:
        print("\n⏹️ Операция отменена пользователем.")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
