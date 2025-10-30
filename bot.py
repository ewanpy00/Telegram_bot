#!/usr/bin/env python3
"""
Telegram Bot для автоматизации работы с makefilm.ai (генерация изображений)
Использует aiogram для Telegram API и Playwright для автоматизации браузера
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
TIMEOUT_SECONDS = int(os.getenv('TIMEOUT_SECONDS', '300'))  # 5 минут по умолчанию

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
    
    Args:
        cookies_path: Путь к файлу с cookies
        
    Returns:
        Список cookies для Playwright
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
    
    Args:
        cookies_path: Путь к файлу для сохранения
        cookies: Список cookies для сохранения
    """
    try:
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        logger.info(f"Cookies сохранены в {cookies_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении cookies: {e}")


async def init_browser():
    """
    Инициализирует браузер и загружает cookies для авторизации
    """
    global browser, context
    
    try:
        playwright = await async_playwright().start()
        
        # Запускаем браузер с минимальными параметрами для стабильности
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-default-apps',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        
        # Создаем контекст браузера
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Загружаем cookies для авторизации
        cookies = await load_cookies_from_file(MAKEFILM_COOKIES_PATH)
        if cookies:
            await context.add_cookies(cookies)
            logger.info("Cookies добавлены в контекст браузера")
        
        logger.info("Браузер успешно инициализирован")
        
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


async def process_makefilm_request(prompt: str) -> str:
    """
    Обрабатывает запрос к makefilm.ai и возвращает ссылку на результат
    
    Args:
        prompt: Текстовый промпт для генерации
        
    Returns:
        Ссылка на сгенерированный результат
        
    Raises:
        Exception: При ошибке обработки запроса
    """
    if not context:
        raise Exception("Браузер не инициализирован")
    
    page = None
    try:
        # Создаем новую страницу
        page = await context.new_page()
        
        # Сначала переходим на главную страницу для авторизации
        logger.info("Переходим на главную страницу makefilm.ai для авторизации...")
        await page.goto("https://makefilm.ai", wait_until='networkidle')
        
        # Ждем загрузки и проверяем авторизацию
        await page.wait_for_timeout(3000)
        
        # Проверяем, авторизованы ли мы
        try:
            # Ищем элементы, которые появляются только после авторизации
            auth_indicators = [
                'a[href*="workspace"]',  # Ссылка на workspace
                'a[href*="profile"]',    # Ссылка на профиль
                'button:has-text("Logout")',  # Кнопка выхода
                '.user-menu',            # Меню пользователя
                '[data-testid="user-menu"]',  # Тестовый ID меню пользователя
                'a[href*="dashboard"]',  # Ссылка на дашборд
                'a[href*="account"]'      # Ссылка на аккаунт
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
            
            if not is_authenticated:
                logger.warning("Авторизация не обнаружена, но продолжаем с имеющимися cookies...")
            
        except Exception as e:
            logger.warning(f"Ошибка при проверке авторизации: {e}")
        
        # Теперь переходим на страницу генератора изображений
        logger.info(f"Переходим на страницу генератора: {MAKEFILM_URL}")
        await page.goto(MAKEFILM_URL, wait_until='networkidle')
        
        # Ждем загрузки страницы
        await page.wait_for_timeout(2000)
        
        # Проверяем, что мы на правильной странице
        current_url = page.url
        logger.info(f"Текущий URL: {current_url}")
        
        # Если нас перенаправило на страницу авторизации, пытаемся найти ссылку на генератор
        if "login" in current_url.lower() or "signin" in current_url.lower() or "auth" in current_url.lower():
            logger.warning("Обнаружена страница авторизации, ищем ссылку на генератор...")
            
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
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
        
        # CSS-селектор для поля ввода промпта (получен с сайта makefilm.ai)
        prompt_input_selector = 'body > div > div > div.flex-1.flex.flex-col > main > div > div > div > div.px-8.pt-1 > div > div > div.p-4.pb-12 > textarea'
        
        # Ищем поле ввода промпта
        try:
            await page.wait_for_selector(prompt_input_selector, timeout=10000)
            prompt_input = await page.query_selector(prompt_input_selector)
            
            if not prompt_input:
                raise Exception("Не удалось найти поле ввода промпта")
                
        except Exception as e:
            logger.error(f"Ошибка при поиске поля ввода: {e}")
            # Пробуем альтернативные селекторы
            alternative_selectors = [
                'textarea',  # Простой селектор для textarea
                'div.p-4.pb-12 textarea',  # Более короткий селектор
                'input[type="text"]',
                '[contenteditable="true"]',
                '.prompt-input',
                '#prompt'
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

        # Надежный выбор версии модели V1 (через Locator API)
        v1_button_selector = 'body > div > div > div.flex-1.flex.flex-col > main > div > div > div > div.px-8.pt-1 > div > div > div.absolute.bottom-3.right-4.flex.items-center.gap-3 > div > div > button'
        v1_btn = page.locator(v1_button_selector).first
        try:
            await v1_btn.wait_for(timeout=8000)
            await v1_btn.scroll_into_view_if_needed()
            await v1_btn.hover(timeout=2000)

            label = ""
            try:
                label = (await v1_btn.inner_text()).strip()
            except:
                pass

            if not label or 'v1' not in label.lower():
                # Открываем список моделей
                await v1_btn.click()
                # Ждем появления контента дропдауна
                dropdown = page.locator("div[role='menu'], div[role='listbox'], [data-radix-popper-content-wrapper], .select-content").first
                try:
                    await dropdown.wait_for(timeout=3000)
                except:
                    pass

                picked = False
                # 1) Семантические опции по роли
                try:
                    opt = page.get_by_role("option", name=r"^v1$", exact=False)
                    if await opt.count() > 0:
                        await opt.first.scroll_into_view_if_needed()
                        await opt.first.click()
                        picked = True
                except:
                    pass

                # 2) Текстовая метка
                if not picked:
                    try:
                        opt_text = page.locator("text=/^v1$/i").first
                        await opt_text.wait_for(timeout=1500)
                        await opt_text.scroll_into_view_if_needed()
                        await opt_text.click()
                        picked = True
                    except:
                        pass

                # 3) Атрибуты/тестовые id
                if not picked:
                    for sel in ["[data-testid='version-v1']", "[data-value='v1']", "[data-variant='v1']", "button:has-text('v1')"]:
                        loc = page.locator(sel).first
                        try:
                            await loc.wait_for(timeout=1500)
                            await loc.scroll_into_view_if_needed()
                            await loc.click()
                            picked = True
                            break
                        except:
                            continue

                # 4) Клавиатурный фолбек: буква 'v' и Enter
                if not picked:
                    try:
                        await page.keyboard.type('v')
                        await page.keyboard.press('Enter')
                    except:
                        pass
            else:
                await v1_btn.click()
                await page.wait_for_timeout(150)
        except Exception as e:
            logger.info(f'Выбор V1 пропущен/не обязателен: {e}')

        # Диагностика состояния кнопки V1
        state = await page.evaluate("""
        (sel) => {
          const b = document.querySelector(sel);
          if (!b) return {found:false};
          const cs = getComputedStyle(b);
          return {
            found: true,
            disabled: b.hasAttribute('disabled') || b.getAttribute('aria-disabled')==='true',
            pe: cs.pointerEvents,
            text: b.innerText || ''
          };
        }
        """, v1_button_selector)
        logger.info(f"V1 button state: {state}")

        # CSS-селектор для кнопки генерации (получен с сайта makefilm.ai)
        generate_button_selector = 'body > div > div > div.flex-1.flex.flex-col > main > div > div > div > div.px-8.pt-1 > div > div > div.absolute.bottom-3.right-4.flex.items-center.gap-3 > button.inline-flex.items-center.justify-center.gap-2.whitespace-nowrap.ring-offset-background.focus-visible\\:outline-none.focus-visible\\:ring-2.focus-visible\\:ring-ring.focus-visible\\:ring-offset-2.disabled\\:pointer-events-none.disabled\\:opacity-50.\\[\\&_svg\\]\\:pointer-events-none.\\[\\&_svg\\]\\:size-4.\\[\\&_svg\\]\\:shrink-0.hover\\:bg-primary\\/90.py-2.px-6.h-8.rounded-lg.bg-gradient-to-r.from-blue-600.via-blue-500.to-blue-400.hover\\:from-blue-700.hover\\:via-blue-600.hover\\:to-blue-500.disabled\\:from-gray-300.disabled\\:to-gray-400.disabled\\:cursor-not-allowed.shadow-lg.hover\\:shadow-xl.transition-all.duration-200.text-white.font-medium.text-sm.border-0'
        
        # Ищем и нажимаем кнопку генерации
        try:
            await page.wait_for_selector(generate_button_selector, timeout=10000)
            generate_button = await page.query_selector(generate_button_selector)
            
            if not generate_button:
                raise Exception("Не удалось найти кнопку генерации")
                
        except Exception as e:
            logger.error(f"Ошибка при поиске кнопки генерации: {e}")
            # Пробуем альтернативные селекторы
            alternative_buttons = [
                'div.absolute.bottom-3.right-4 button',  # Более короткий селектор
                'button.bg-gradient-to-r.from-blue-600',  # По градиенту
                'button:has-text("Generate")',
                'button:has-text("Create")',
                'button[type="submit"]',
                '.btn-primary',
                '#submit-btn'
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
        
        # TODO: ВСТАВЬТЕ ПРАВИЛЬНЫЙ CSS-СЕЛЕКТОР ДЛЯ ОЖИДАНИЯ РЕЗУЛЬТАТА
        # Пример селекторов для изображений (замените на актуальные):
        result_selectors = [
            'a[href*="image"]',  # Ссылка на изображение
            'a[href*="photo"]',  # Ссылка на фото
            'a[href*="jpg"]',    # Ссылка на JPG
            'a[href*="png"]',    # Ссылка на PNG
            'a[href*="result"]', # Ссылка на результат
            '.result-link',      # Класс ссылки на результат
            '.download-link',    # Класс ссылки на скачивание
            '[data-result-url]'  # Атрибут с URL результата
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
        await message.answer("❌ Пожалуйста, отправьте текстовый промпт для генерации видео.")
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
        logger.info("Запуск Telegram бота...")
        
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
