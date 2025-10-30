#!/usr/bin/env python3
"""
Альтернативный способ получения cookies для makefilm.ai
Если автоматический скрипт не работает, используйте этот метод
"""

import json
import os

def create_cookies_template():
    """
    Создает шаблон файла cookies.json с инструкциями
    """
    print("🍪 Создание шаблона для cookies...")
    
    # Создаем шаблон cookies
    cookies_template = [
        {
            "name": "session_id",
            "value": "ВАШ_SESSION_ID_ЗДЕСЬ",
            "domain": ".makefilm.ai",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        },
        {
            "name": "auth_token", 
            "value": "ВАШ_AUTH_TOKEN_ЗДЕСЬ",
            "domain": ".makefilm.ai",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax"
        },
        {
            "name": "user_id",
            "value": "ВАШ_USER_ID_ЗДЕСЬ", 
            "domain": ".makefilm.ai",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax"
        }
    ]
    
    # Сохраняем шаблон
    with open("cookies_template.json", "w", encoding="utf-8") as f:
        json.dump(cookies_template, f, indent=2, ensure_ascii=False)
    
    print("✅ Создан файл cookies_template.json")
    print("\n" + "="*60)
    print("📝 ИНСТРУКЦИЯ ПО ПОЛУЧЕНИЮ COOKIES:")
    print("="*60)
    print("1. Откройте браузер Chrome или Safari")
    print("2. Перейдите на https://makefilm.ai")
    print("3. Авторизуйтесь на сайте")
    print("4. Нажмите F12 (или Cmd+Option+I на Mac)")
    print("5. Перейдите на вкладку 'Application' (Chrome) или 'Storage' (Safari)")
    print("6. В левом меню найдите 'Cookies' → 'https://makefilm.ai'")
    print("7. Скопируйте значения важных cookies:")
    print("   - session_id")
    print("   - auth_token") 
    print("   - user_id")
    print("   - csrf_token")
    print("8. Замените значения в файле cookies_template.json")
    print("9. Переименуйте файл в cookies.json")
    print("="*60)
    
    # Показываем пример важных cookies
    print("\n🔍 ВАЖНЫЕ COOKIES ДЛЯ ПОИСКА:")
    important_cookies = [
        "session_id", "sessionid", "PHPSESSID",
        "auth_token", "auth_token", "access_token",
        "user_id", "userid", "uid", 
        "csrf_token", "csrf", "_token",
        "remember_token", "remember_me"
    ]
    
    for cookie in important_cookies:
        print(f"  • {cookie}")
    
    print(f"\n📁 Файл шаблона создан: cookies_template.json")
    print("📝 Отредактируйте его и переименуйте в cookies.json")

if __name__ == "__main__":
    create_cookies_template()
