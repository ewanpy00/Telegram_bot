#!/usr/bin/env python3
"""
Простой тест cookies без браузера
"""

import json
import os
from datetime import datetime

def test_cookies():
    """
    Тестирует cookies без запуска браузера
    """
    print("🍪 Тестирование cookies...")
    
    # Проверяем наличие файла cookies
    cookies_file = "cookies.json"
    if not os.path.exists(cookies_file):
        print(f"❌ Файл {cookies_file} не найден")
        print("🔧 Создайте файл cookies.json с вашими cookies")
        return False
    
    try:
        # Загружаем cookies
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        print(f"✅ Файл {cookies_file} найден")
        print(f"📊 Загружено {len(cookies)} cookies")
        
        # Анализируем cookies
        print("\n🔍 Анализ cookies:")
        
        important_cookies = {
            'csrf_access_token': False,
            'csrf_refresh_token': False,
            'profile': False,
            'session_id': False,
            'auth_token': False
        }
        
        for cookie in cookies:
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            domain = cookie.get('domain', '')
            expires = cookie.get('expires', 0)
            
            # Проверяем важные cookies
            if name in important_cookies:
                important_cookies[name] = True
                print(f"  ✅ {name}: {value[:20]}..." if len(value) > 20 else f"  ✅ {name}: {value}")
            
            # Проверяем домен
            if 'makefilm.ai' in domain:
                print(f"  🌐 Домен: {domain}")
            
            # Проверяем срок действия
            if expires > 0:
                exp_date = datetime.fromtimestamp(expires)
                if exp_date < datetime.now():
                    print(f"  ⚠️ Cookie {name} истек: {exp_date}")
                else:
                    print(f"  ✅ Cookie {name} действителен до: {exp_date}")
        
        # Проверяем наличие важных cookies
        print("\n📋 Статус важных cookies:")
        all_good = True
        for name, found in important_cookies.items():
            if found:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name} - НЕ НАЙДЕН")
                all_good = False
        
        if all_good:
            print("\n🎉 Все важные cookies найдены!")
            print("✅ Авторизация должна работать")
        else:
            print("\n⚠️ Некоторые важные cookies отсутствуют")
            print("🔧 Возможно, нужно обновить cookies")
        
        return all_good
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        print("🔧 Проверьте формат файла cookies.json")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_config():
    """
    Тестирует конфигурацию
    """
    print("\n🔧 Тестирование конфигурации...")
    
    # Проверяем файл .env
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ Файл {env_file} найден")
        
        with open(env_file, 'r') as f:
            content = f.read()
            
        if "your_telegram_bot_token_here" in content:
            print("⚠️ Токен Telegram не настроен")
            print("🔧 Замените 'your_telegram_bot_token_here' на реальный токен")
        else:
            print("✅ Токен Telegram настроен")
    else:
        print(f"❌ Файл {env_file} не найден")
        print("🔧 Создайте файл .env с токеном")

if __name__ == "__main__":
    print("🧪 Простой тест конфигурации")
    print("="*50)
    
    cookies_ok = test_cookies()
    test_config()
    
    print("\n" + "="*50)
    print("📋 РЕЗУЛЬТАТ:")
    print("="*50)
    
    if cookies_ok:
        print("✅ Cookies готовы к использованию")
        print("✅ Можно запускать бота")
    else:
        print("❌ Cookies требуют обновления")
        print("🔧 Обновите cookies перед запуском бота")
    
    print("\n🚀 Для запуска бота:")
    print("python3 bot.py")
