# 🍪 САМЫЙ ПРОСТОЙ СПОСОБ ПОЛУЧЕНИЯ COOKIES

## 🚀 Способ через адресную строку (работает везде!)

### Шаг 1: Авторизуйтесь на makefilm.ai
1. Откройте браузер
2. Перейдите на **https://makefilm.ai**
3. **Авторизуйтесь** на сайте

### Шаг 2: Получите cookies через адресную строку
1. В **адресной строке** браузера введите:
```
javascript:console.log(document.cookie)
```
2. Нажмите **Enter**
3. В консоли появится строка с cookies

### Шаг 3: Альтернативный способ
Если первый не работает, попробуйте:
```
javascript:alert(document.cookie)
```

## 📝 Пример результата:
```
session_id=abc123def456; auth_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9; user_id=12345; csrf_token=csrf_abc123
```

## 🔧 Создание файла cookies.json

После получения строки cookies, создайте файл `cookies.json`:

```json
[
  {
    "name": "session_id",
    "value": "abc123def456",
    "domain": ".makefilm.ai",
    "path": "/",
    "expires": -1,
    "httpOnly": false,
    "secure": true,
    "sameSite": "Lax"
  },
  {
    "name": "auth_token",
    "value": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
    "domain": ".makefilm.ai",
    "path": "/",
    "expires": -1,
    "httpOnly": false,
    "secure": true,
    "sameSite": "Lax"
  },
  {
    "name": "user_id",
    "value": "12345",
    "domain": ".makefilm.ai",
    "path": "/",
    "expires": -1,
    "httpOnly": false,
    "secure": true,
    "sameSite": "Lax"
  },
  {
    "name": "csrf_token",
    "value": "csrf_abc123",
    "domain": ".makefilm.ai",
    "path": "/",
    "expires": -1,
    "httpOnly": false,
    "secure": true,
    "sameSite": "Lax"
  }
]
```

## 🎯 Быстрый способ:

1. **Авторизуйтесь** на makefilm.ai
2. **Вставьте в адресную строку:**
   ```
   javascript:console.log(document.cookie)
   ```
3. **Нажмите Enter**
4. **Скопируйте** результат из консоли
5. **Создайте файл** `cookies.json` с JSON выше
6. **Замените значения** на ваши реальные cookies

## ✅ Проверка:
```bash
python3 bot.py
```

Если все правильно, бот запустится без ошибок!
