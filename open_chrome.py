#!/usr/bin/env python3
"""
Скрипт для открытия Chrome с инструментами разработчика
"""

import subprocess
import webbrowser
import time

def open_chrome_with_devtools():
    """
    Открывает Chrome с инструментами разработчика
    """
    print("🚀 Открываем Chrome с инструментами разработчика...")
    
    try:
        # Открываем Chrome с инструментами разработчика
        subprocess.run([
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '--auto-open-devtools-for-tabs',
            'https://makefilm.ai'
        ])
        
        print("\n" + "="*60)
        print("📝 ИНСТРУКЦИЯ:")
        print("="*60)
        print("1. Chrome откроется с инструментами разработчика")
        print("2. Авторизуйтесь на makefilm.ai")
        print("3. В консоли введите: console.log(document.cookie)")
        print("4. Нажмите Enter")
        print("5. Скопируйте результат")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Ошибка при открытии Chrome: {e}")
        print("\n🔧 Альтернативный способ:")
        print("1. Откройте Chrome вручную")
        print("2. Перейдите на https://makefilm.ai")
        print("3. Нажмите F12")
        print("4. Перейдите на вкладку 'Console'")
        print("5. Введите: console.log(document.cookie)")

if __name__ == "__main__":
    open_chrome_with_devtools()
