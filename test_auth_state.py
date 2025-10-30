#!/usr/bin/env python3
"""
Тест состояния авторизации
"""

import os
import json
from datetime import datetime

def test_auth_state():
    """
    Тестирует файл состояния авторизации
    """
    print("🔐 Тестирование состояния авторизации...")
    
    auth_state_file = "auth_state.json"
    
    if not os.path.exists(auth_state_file):
        print(f"❌ Файл {auth_state_file} не найден")
        print("🔧 Запустите: python3 save_auth_state.py")
        return False
    
    try:
        # Загружаем состояние авторизации
        with open(auth_state_file, 'r', encoding='utf-8') as f:
            auth_state = json.load(f)
        
        print(f"✅ Файл {auth_state_file} найден")
        
        # Анализируем состояние
        if 'cookies' in auth_state:
            cookies = auth_state['cookies']
            print(f"📊 Найдено {len(cookies)} cookies")
            
            # Проверяем важные cookies
            important_cookies = {
                'csrf_access_token': False,
                'csrf_refresh_token': False,
                'profile': False,
                'session_id': False
            }
            
            for cookie in cookies:
                name = cookie.get('name', '')
                domain = cookie.get('domain', '')
                
                if name in important_cookies:
                    important_cookies[name] = True
                    print(f"  ✅ {name}: {domain}")
                
                if 'makefilm.ai' in domain:
                    print(f"  🌐 Домен: {domain}")
        
        if 'origins' in auth_state:
            origins = auth_state['origins']
            print(f"🌐 Найдено {len(origins)} источников")
            
            for origin in origins:
                origin_url = origin.get('origin', '')
                if 'makefilm.ai' in origin_url:
                    print(f"  ✅ {origin_url}")
        
        print("\n📋 Статус важных cookies:")
        all_good = True
        for name, found in important_cookies.items():
            if found:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name} - НЕ НАЙДЕН")
                all_good = False
        
        if all_good:
            print("\n🎉 Состояние авторизации готово!")
            print("✅ Можно запускать основного бота")
        else:
            print("\n⚠️ Некоторые важные cookies отсутствуют")
            print("🔧 Возможно, нужно обновить состояние")
        
        return all_good
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
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
    print("🧪 Тест состояния авторизации")
    print("="*50)
    
    auth_ok = test_auth_state()
    test_config()
    
    print("\n" + "="*50)
    print("📋 РЕЗУЛЬТАТ:")
    print("="*50)
    
    if auth_ok:
        print("✅ Состояние авторизации готово")
        print("🚀 Можно запускать: python3 bot_with_storage.py")
    else:
        print("❌ Состояние авторизации требует настройки")
        print("🔧 Запустите: python3 save_auth_state.py")
    
    print("\n📝 Инструкция:")
    print("1. python3 save_auth_state.py - сохранить состояние")
    print("2. Настроить токен в .env")
    print("3. python3 bot_with_storage.py - запустить бота")
