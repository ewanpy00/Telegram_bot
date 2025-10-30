#!/usr/bin/env python3
"""
Бот с автоматической авторизацией на makefilm.ai
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MAKEFILM_COOKIES_PATH = os.getenv('MAKEFILM_COOKIES_PATH', 'cookies.json')
MAKEFILM_URL = 'https://makefilm.ai/workspace/image-generator'
TIMEOUT_SECONDS = int(os.getenv('TIMEOUT_SECONDS', '300'))

# Проверяем наличие обязательных переменных
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения!")

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Глобальные переменные для браузера
browser: Optional[Browser] = None
context: Optional[BrowserContext] = None


async def load_cookies_from_file(cookies_path: str) -> list:
    """
    Загружает cookies из JSON файла
    """
    try:
        if os.path.exists(cookies_path):
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                logger.info(f"Загружено {len(cookies)} cookies из {cookies_path}")
                return cookies
        else:
            logger.warning(f"Файл cookies не найден: {cookies_path}")
            return []
    except Exception as e:
        logger.error(f"Ошибка при загрузке cookies: {e}")
        return []


async def save_cookies_to_file(cookies_path: str, cookies: list):
    """
    Сохраняет cookies в JSON файл
    """
    try:
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        logger.info(f"Cookies сохранены в {cookies_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении cookies: {e}")


async def init_browser():
    """
    Инициализирует браузер Firefox
    """
    global browser, context
    
    try:
        playwright = await async_playwright().start()
        
        # Запускаем Firefox
        browser = await playwright.firefox.launch(
            headless=False,
            args=['--no-sandbox']
        )
        
        # Создаем контекст браузера
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0'
        )
        
        # Загружаем cookies для авторизации
        cookies = await load_cookies_from_file(MAKEFILM_COOKIES_PATH)
        if cookies:
            await context.add_cookies(cookies)
            logger.info("Cookies добавлены в контекст браузера")
        
        logger.info("Браузер Firefox успешно инициализирован")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации браузера: {e}")
        raise


async def close_browser():
    """
    Закрывает браузер и сохраняет cookies
    """
    global browser, context
    
    try:
        if context:
            # Сохраняем обновленные cookies
            cookies = await context.cookies()
            await save_cookies_to_file(MAKEFILM_COOKIES_PATH, cookies)
            
            await context.close()
            context = None
            
        if browser:
            await browser.close()
            browser = None
            
        logger.info("Браузер закрыт")
        
    except Exception as e:
        logger.error(f"Ошибка при закрытии браузера: {e}")


async def ensure_authentication(page: Page) -> bool:
    """
    Обеспечивает авторизацию на сайте makefilm.ai
    """
    try:
        logger.info("Проверяем авторизацию...")
        
        # Переходим на главную страницу
        await page.goto("https://makefilm.ai", wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Проверяем, авторизованы ли мы
        auth_indicators = [
            'a[href*="workspace"]',
            'a[href*="profile"]',
            'button:has-text("Logout")',
            '.user-menu',
            '[data-testid="user-menu"]',
            'a[href*="dashboard"]',
            'a[href*="account"]'
        ]
        
        is_authenticated = False
        for indicator in auth_indicators:
            try:
                element = await page.query_selector(indicator)
                if element:
                    is_authenticated = True
                    logger.info(f"Найден индикатор авторизации: {indicator}")
                    break
            except:
                continue
        
        if is_authenticated:
            logger.info("✅ Авторизация подтверждена")
            return True
        
        # Если не авторизованы, ищем элементы для авторизации
        logger.warning("❌ Авторизация не обнаружена, ищем элементы для входа...")
        
        login_elements = [
            'a:has-text("Login")',
            'a:has-text("Sign In")',
            'button:has-text("Login")',
            'button:has-text("Sign In")',
            '.login-button',
            '.signin-button',
            'a[href*="login"]',
            'a[href*="signin"]'
        ]
        
        login_found = False
        for element_selector in login_elements:
            try:
                element = await page.query_selector(element_selector)
                if element:
                    text = await element.inner_text()
                    logger.info(f"Найден элемент для авторизации: {element_selector} - '{text.strip()}'")
                    login_found = True
                    break
            except:
                pass
        
        if not login_found:
            logger.warning("Элементы для авторизации не найдены, возможно, нужна ручная авторизация")
            
            # Ждем, пока пользователь авторизуется вручную
            logger.info("⏳ Ожидаем ручной авторизации...")
            logger.info("📝 Инструкция:")
            logger.info("1. Авторизуйтесь на сайте в открывшемся браузере")
            logger.info("2. Перейдите на страницу генератора изображений")
            logger.info("3. Вернитесь в терминал и нажмите Enter")
            
            input("Нажмите Enter после авторизации...")
            
            # Проверяем авторизацию снова
            await page.reload()
            await page.wait_for_timeout(2000)
            
            for indicator in auth_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        logger.info("✅ Авторизация успешна после ручного входа")
                        return True
                except:
                    continue
        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка при проверке авторизации: {e}")
        return False


async def process_makefilm_request(prompt: str) -> str:
    """
    Обрабатывает запрос к makefilm.ai с автоматической авторизацией
    """
    if not context:
        raise Exception("Браузер не инициализирован")
    
    page = None
    try:
        # Создаем новую страницу
        page = await context.new_page()
        
        # Обеспечиваем авторизацию
        auth_success = await ensure_authentication(page)
        
        if not auth_success:
            logger.warning("Авторизация не удалась, но продолжаем...")
        
        # Переходим на страницу генератора изображений
        logger.info(f"Переходим на страницу генератора: {MAKEFILM_URL}")
        await page.goto(MAKEFILM_URL, wait_until='networkidle')
        
        # Ждем загрузки страницы
        await page.wait_for_timeout(3000)
        
        # Проверяем, что мы на правильной странице
        current_url = page.url
        logger.info(f"Текущий URL: {current_url}")
        
        # Если нас перенаправило на страницу авторизации
        if "login" in current_url.lower() or "signin" in current_url.lower() or "auth" in current_url.lower():
            logger.warning("Обнаружена страница авторизации, пытаемся найти ссылку на генератор...")
            
            # Ищем ссылки на workspace или генератор
            workspace_links = [
                'a[href*="workspace"]',
                'a[href*="image-generator"]',
                'a:has-text("Workspace")',
                'a:has-text("Generator")'
            ]
            
            for link_selector in workspace_links:
                try:
                    link = await page.query_selector(link_selector)
                    if link:
                        logger.info(f"Найдена ссылка на генератор: {link_selector}")
                        await link.click()
                        await page.wait_for_timeout(3000)
                        break
                except:
                    continue
        
        # CSS-селектор для поля ввода промпта
        prompt_input_selector = 'body > div > div > div.flex-1.flex.flex-col > main > div > div > div > div.px-8.pt-1 > div > div > div.p-4.pb-12 > textarea'
        
        # Ищем поле ввода промпта
        try:
            await page.wait_for_selector(prompt_input_selector, timeout=15000)
            prompt_input = await page.query_selector(prompt_input_selector)
            
            if not prompt_input:
                raise Exception("Не удалось найти поле ввода промпта")
                
        except Exception as e:
            logger.error(f"Ошибка при поиске поля ввода: {e}")
            # Пробуем альтернативные селекторы
            alternative_selectors = [
                'textarea',
                'div.p-4.pb-12 textarea',
                'input[type="text"]',
                '[contenteditable="true"]',
                'input[placeholder*="prompt"]',
                'input[placeholder*="describe"]'
            ]
            
            prompt_input = None
            for selector in alternative_selectors:
                try:
                    prompt_input = await page.query_selector(selector)
                    if prompt_input:
                        logger.info(f"Найдено поле ввода с селектором: {selector}")
                        break
                except:
                    continue
            
            if not prompt_input:
                raise Exception("Не удалось найти поле ввода промпта ни одним из способов")
        
        # Очищаем поле и вводим промпт
        await prompt_input.fill('')
        await prompt_input.type(prompt, delay=100)
        logger.info(f"Введен промпт: {prompt}")
        
        # CSS-селектор для кнопки генерации
        generate_button_selector = 'body > div > div > div.flex-1.flex.flex-col > main > div > div > div > div.px-8.pt-1 > div > div > div.absolute.bottom-3.right-4.flex.items-center.gap-3 > button.inline-flex.items-center.justify-center.gap-2.whitespace-nowrap.ring-offset-background.focus-visible\\:outline-none.focus-visible\\:ring-2.focus-visible\\:ring-ring.focus-visible\\:ring-offset-2.disabled\\:pointer-events-none.disabled\\:opacity-50.\\[\\&_svg\\]\\:pointer-events-none.\\[\\&_svg\\]\\:size-4.\\[\\&_svg\\]\\:shrink-0.hover\\:bg-primary\\/90.py-2.px-6.h-8.rounded-lg.bg-gradient-to-r.from-blue-600.via-blue-500.to-blue-400.hover\\:from-blue-700.hover\\:via-blue-600.hover\\:to-blue-500.disabled\\:from-gray-300.disabled\\:to-gray-400.disabled\\:cursor-not-allowed.shadow-lg.hover\\:shadow-xl.transition-all.duration-200.text-white.font-medium.text-sm.border-0'
        
        # Ищем и нажимаем кнопку генерации
        try:
            await page.wait_for_selector(generate_button_selector, timeout=15000)
            generate_button = await page.query_selector(generate_button_selector)
            
            if not generate_button:
                raise Exception("Не удалось найти кнопку генерации")
                
        except Exception as e:
            logger.error(f"Ошибка при поиске кнопки генерации: {e}")
            # Пробуем альтернативные селекторы
            alternative_buttons = [
                'div.absolute.bottom-3.right-4 button',
                'button.bg-gradient-to-r.from-blue-600',
                'button:has-text("Generate")',
                'button:has-text("Create")',
                'button:has-text("Submit")',
                'button[type="submit"]',
                '.generate-btn',
                '.create-btn'
            ]
            
            generate_button = None
            for selector in alternative_buttons:
                try:
                    generate_button = await page.query_selector(selector)
                    if generate_button:
                        logger.info(f"Найдена кнопка генерации с селектором: {selector}")
                        break
                except:
                    continue
            
            if not generate_button:
                raise Exception("Не удалось найти кнопку генерации ни одним из способов")
        
        # Нажимаем кнопку генерации
        await generate_button.click()
        logger.info("Запущена генерация")
        
        # Селекторы для поиска результата
        result_selectors = [
            'a[href*="image"]',
            'a[href*="jpg"]',
            'a[href*="png"]',
            'a[href*="gif"]',
            'a[href*="webp"]',
            'a[href*="result"]',
            'a[href*="download"]',
            '.result-link',
            '.download-link',
            '.image-link',
            '[data-result-url]',
            '[data-image-url]'
        ]
        
        # Ждем появления результата
        logger.info(f"Ожидаем результат генерации (таймаут: {TIMEOUT_SECONDS} сек)...")
        
        result_url = None
        for selector in result_selectors:
            try:
                # Ждем появления элемента с результатом
                await page.wait_for_selector(selector, timeout=TIMEOUT_SECONDS * 1000)
                
                # Получаем ссылку на результат
                result_element = await page.query_selector(selector)
                if result_element:
                    # Пробуем получить href атрибут
                    href = await result_element.get_attribute('href')
                    if href:
                        result_url = href
                        break
                    
                    # Пробуем получить data-result-url атрибут
                    data_url = await result_element.get_attribute('data-result-url')
                    if data_url:
                        result_url = data_url
                        break
                        
            except Exception as e:
                logger.debug(f"Селектор {selector} не сработал: {e}")
                continue
        
        if not result_url:
            # Если не нашли ссылку, пробуем найти текст с URL
            try:
                page_content = await page.content()
                import re
                # Ищем URL изображений в тексте страницы
                url_pattern = r'https?://[^\s<>"\']+\.(?:jpg|jpeg|png|gif|webp|bmp)'
                urls = re.findall(url_pattern, page_content)
                if urls:
                    result_url = urls[0]
            except Exception as e:
                logger.error(f"Ошибка при поиске URL в тексте: {e}")
        
        if not result_url:
            raise Exception("Не удалось получить ссылку на результат генерации")
        
        # Если ссылка относительная, делаем её абсолютной
        if result_url.startswith('/'):
            result_url = MAKEFILM_URL + result_url
        
        logger.info(f"Получена ссылка на результат: {result_url}")
        return result_url
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        raise
    finally:
        if page:
            await page.close()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    """
    await message.answer(
        "🖼️ Добро пожаловать в MakeFilm AI Bot!\n\n"
        "Отправьте мне текстовый промпт, и я создам для вас изображение с помощью makefilm.ai\n\n"
        "Пример: 'Создай фото котика, играющего в саду'"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help
    """
    await message.answer(
        "📖 Помощь по использованию бота:\n\n"
        "• Отправьте любой текстовый промпт для создания изображения\n"
        "• Бот обработает ваш запрос и вернет ссылку на результат\n"
        "• Время обработки может занять несколько минут\n\n"
        "Команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/status - Проверить статус бота"
    )


@dp.message(Command("status"))
async def cmd_status(message: Message):
    """
    Обработчик команды /status
    """
    status_text = "🟢 Бот работает нормально\n"
    
    if browser and context:
        status_text += "🟢 Браузер инициализирован\n"
    else:
        status_text += "🔴 Браузер не инициализирован\n"
    
    cookies_exist = os.path.exists(MAKEFILM_COOKIES_PATH)
    if cookies_exist:
        status_text += f"🟢 Cookies найдены: {MAKEFILM_COOKIES_PATH}\n"
    else:
        status_text += f"🔴 Cookies не найдены: {MAKEFILM_COOKIES_PATH}\n"
    
    status_text += f"⏱️ Таймаут ожидания: {TIMEOUT_SECONDS} сек"
    
    await message.answer(status_text)


@dp.message()
async def handle_text_message(message: Message):
    """
    Обработчик всех текстовых сообщений
    """
    user_prompt = message.text.strip()
    
    if not user_prompt:
        await message.answer("❌ Пожалуйста, отправьте текстовый промпт для генерации изображения.")
        return
    
    # Отправляем сообщение о начале обработки
    processing_msg = await message.answer("⏳ Обрабатываю ваш запрос…")
    
    try:
        logger.info(f"Обработка запроса от пользователя {message.from_user.id}: {user_prompt}")
        
        # Обрабатываем запрос через makefilm.ai
        result_url = await process_makefilm_request(user_prompt)
        
        # Отправляем результат пользователю
        await processing_msg.edit_text(
            f"🖼️ Ваше изображение готово!\n\n"
            f"📝 Промпт: {user_prompt}\n"
            f"🔗 Ссылка: {result_url}\n\n"
            f"⏰ Время обработки: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        logger.info(f"Результат отправлен пользователю {message.from_user.id}")
        
    except Exception as e:
        error_msg = f"❌ Произошла ошибка при обработке запроса:\n\n{str(e)}\n\nПопробуйте еще раз или обратитесь к администратору."
        
        await processing_msg.edit_text(error_msg)
        logger.error(f"Ошибка при обработке запроса от пользователя {message.from_user.id}: {e}")


async def main():
    """
    Основная функция запуска бота
    """
    try:
        logger.info("Запуск Telegram бота с автоматической авторизацией...")
        
        # Инициализируем браузер
        await init_browser()
        
        # Запускаем бота
        logger.info("Бот запущен и готов к работе!")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        # Закрываем браузер при завершении
        await close_browser()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
