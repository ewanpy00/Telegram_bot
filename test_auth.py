#!/usr/bin/env python3
"""
Скрипт для тестирования авторизации на makefilm.ai
"""

import asyncio
from playwright.async_api import async_playwright

async def test_authentication():
    """
    Тестирует процесс авторизации на makefilm.ai
    """
    print("🔐 Тестирование авторизации на makefilm.ai...")
    
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
            
            # Переходим на главную страницу
            print("🌐 Переходим на https://makefilm.ai...")
            await page.goto("https://makefilm.ai", wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # Проверяем текущий URL
            current_url = page.url
            print(f"📄 Текущий URL: {current_url}")
            
            # Проверяем авторизацию
            print("\n🔍 Проверяем авторизацию...")
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
                print("❌ Авторизация не обнаружена")
                
                # Ищем элементы для авторизации
                print("\n🔍 Ищем элементы для авторизации...")
                login_elements = [
                    'a:has-text("Login")',
                    'a:has-text("Sign In")',
                    'button:has-text("Login")',
                    'button:has-text("Sign In")',
                    '.login-button',
                    '.signin-button'
                ]
                
                for element_selector in login_elements:
                    try:
                        element = await page.query_selector(element_selector)
                        if element:
                            text = await element.inner_text()
                            print(f"  • {element_selector} - текст: '{text.strip()}'")
                    except:
                        pass
            else:
                print("✅ Авторизация успешна!")
                
                # Пытаемся перейти на страницу генератора
                print("\n🎯 Переходим на страницу генератора...")
                await page.goto("https://makefilm.ai/workspace/image-generator", wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                final_url = page.url
                print(f"📄 Финальный URL: {final_url}")
                
                if "image-generator" in final_url:
                    print("✅ Успешно перешли на страницу генератора!")
                else:
                    print("❌ Не удалось перейти на страницу генератора")
                    print("Возможно, нужна дополнительная авторизация")
            
            print("\n" + "="*60)
            print("📋 РЕЗУЛЬТАТ:")
            print("="*60)
            if is_authenticated:
                print("✅ Авторизация работает")
                print("✅ Можно переходить на страницу генератора")
            else:
                print("❌ Авторизация не работает")
                print("🔧 Нужно обновить cookies или авторизоваться вручную")
            print("="*60)
            
            # Ждем, чтобы пользователь мог посмотреть
            input("\nНажмите Enter для закрытия браузера...")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_authentication())
