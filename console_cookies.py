#!/usr/bin/env python3
"""
Простой скрипт для получения cookies через консоль браузера
"""

print("🍪 Получение cookies через консоль браузера")
print("\n" + "="*60)
print("📝 ИНСТРУКЦИЯ:")
print("="*60)
print("1. Откройте браузер Chrome или Safari")
print("2. Перейдите на https://makefilm.ai")
print("3. Авторизуйтесь на сайте")
print("4. Нажмите F12 (или Cmd+Option+I)")
print("5. Перейдите на вкладку 'Console' (Консоль)")
print("6. Скопируйте и вставьте этот код:")
print("="*60)

console_code = '''
// Получаем все cookies
const cookies = document.cookie.split(';');
const cookieArray = [];

cookies.forEach(cookie => {
    const [name, value] = cookie.trim().split('=');
    if (name && value) {
        cookieArray.push({
            name: name,
            value: value,
            domain: ".makefilm.ai",
            path: "/",
            expires: -1,
            httpOnly: false,
            secure: true,
            sameSite: "Lax"
        });
    }
});

// Выводим результат
console.log('Найдено cookies:', cookieArray.length);
console.log(JSON.stringify(cookieArray, null, 2));

// Копируем в буфер обмена
navigator.clipboard.writeText(JSON.stringify(cookieArray, null, 2)).then(() => {
    console.log('✅ Cookies скопированы в буфер обмена!');
}).catch(err => {
    console.log('❌ Ошибка копирования. Скопируйте JSON вручную.');
});
'''

print(console_code)
print("="*60)
print("7. Нажмите Enter в консоли")
print("8. Скопируйте выведенный JSON")
print("9. Сохраните его в файл cookies.json")
print("="*60)

print("\n🔍 АЛЬТЕРНАТИВНЫЙ СПОСОБ:")
print("Если консоль не работает, используйте этот код:")
print("="*60)

alternative_code = '''
// Простой способ - просто вывести cookies
console.log('Все cookies:', document.cookie);

// Или по одному
document.cookie.split(';').forEach(cookie => {
    console.log(cookie.trim());
});
'''

print(alternative_code)
print("="*60)
print("\n📁 После получения cookies:")
print("1. Скопируйте результат")
print("2. Создайте файл cookies.json")
print("3. Вставьте JSON в файл")
print("4. Запустите бота: python3 bot.py")
