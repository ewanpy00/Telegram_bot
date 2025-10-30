#!/usr/bin/env python3
"""
Telegram Bot для makefilm.ai с использованием сохраненного состояния авторизации
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from typing import Optional, Tuple

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
AUTH_STATE_PATH = os.getenv('AUTH_STATE_PATH', 'auth_state.json')
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


async def init_browser():
    """
    Инициализирует браузер с сохраненным состоянием авторизации
    """
    global browser, context
    
    try:
        playwright = await async_playwright().start()
        
        # Проверяем наличие файла состояния авторизации
        if not os.path.exists(AUTH_STATE_PATH):
            logger.error(f"Файл состояния авторизации не найден: {AUTH_STATE_PATH}")
            logger.error("Запустите сначала: python3 save_auth_state.py")
            raise FileNotFoundError(f"Файл {AUTH_STATE_PATH} не найден!")
        
        # Запускаем браузер
        browser = await playwright.firefox.launch(
            headless=False,  # Можно изменить на True для скрытого режима
            args=['--no-sandbox']
        )

        # Создаем контекст с сохраненным состоянием авторизации
        context = await browser.new_context(
            storage_state=AUTH_STATE_PATH,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0'
        )

        # Увеличиваем таймауты по умолчанию для медленных сетей
        context.set_default_timeout(60000)

        logger.info(f"✅ Браузер инициализирован с состоянием авторизации из {AUTH_STATE_PATH}")

        # Проверяем авторизацию (не фейлим весь запуск при таймауте)
        page = await context.new_page()
        page.set_default_navigation_timeout(60000)
        try:
            try:
                await page.goto("https://makefilm.ai", wait_until='networkidle', timeout=45000)
            except Exception:
                # Фолбек — более мягкое ожидание
                await page.goto("https://makefilm.ai", wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_load_state('domcontentloaded')
        except Exception as nav_err:
            logger.warning(f"Не удалось полноценно открыть главную страницу (продолжаем): {nav_err}")
            # Не поднимаем ошибку, т.к. дальше можем сразу перейти в генератор
        
        # Проверяем индикаторы авторизации
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
                    logger.info(f"✅ Авторизация подтверждена: {indicator}")
                    break
            except:
                continue
        
        if not is_authenticated:
            logger.warning("⚠️ Авторизация не обнаружена, возможно, состояние устарело")
            logger.warning("🔄 Попробуйте обновить состояние: python3 save_auth_state.py")

        await page.close()

    except Exception as e:
        # Не прерываем запуск бота полностью — позволим обработчикам попытаться перейти на нужную страницу
        logger.error(f"Ошибка при инициализации браузера: {e}")
        # Не делаем raise


async def close_browser():
    """
    Закрывает браузер
    """
    global browser, context
    
    try:
        if context:
            await context.close()
            context = None
            
        if browser:
            await browser.close()
            browser = None
            
        logger.info("Браузер закрыт")
        
    except Exception as e:
        logger.error(f"Ошибка при закрытии браузера: {e}")


async def process_makefilm_request(prompt: str) -> Tuple[str, Optional[str], Optional[str]]:
    if not context:
        raise Exception("Браузер не инициализирован")
    page = None
    result_url = None
    img_src = None
    file_path = None
    try:
        page = await context.new_page()
        await page.goto(MAKEFILM_URL, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        # 1. Явный поиск и ввод промпта
        prompt_input_selector = 'body > div > div > div.flex-1.flex.flex-col > main > div > div > div > div.px-8.pt-1 > div > div > div.p-4.pb-12 > textarea'
        logger.info('Ищу поле для ввода промпта...')
        try:
            await page.wait_for_selector(prompt_input_selector, timeout=15000)
            prompt_input = await page.query_selector(prompt_input_selector)
            if not prompt_input:
                logger.error('Поле для текста промпта не найдено (None)')
                raise Exception('Не найдено поле для промпта!')
            await prompt_input.focus()
            await prompt_input.fill("")
            await page.keyboard.type(prompt, delay=70)
            await prompt_input.dispatch_event('input')
            await prompt_input.dispatch_event('change')
            logger.info(f"Промпт введен: {prompt}")
        except Exception as e:
            logger.error(f'Ошибка при поиске/вводе промпта: {e}')
            raise

        # 2. Выбор V1 (как есть, после ввода)
        logger.info('Перед выбором V1...')
        v1_button_selector = 'body > div > div > div.flex-1.flex.flex-col > main > div > div > div > div.px-8.pt-1 > div > div > div.absolute.bottom-3.right-4.flex.items-center.gap-3 > div > div > button'
        v1_btn = page.locator(v1_button_selector).first
        picked = False
        try:
            await v1_btn.wait_for(timeout=8000)
            await v1_btn.scroll_into_view_if_needed()
            await v1_btn.click()
            await page.wait_for_timeout(300)
            dropdown_candidates = [
                "div[role='listbox']",
                "div[role='menu']",
                ".select-content",
                "[data-radix-popper-content-wrapper]"
            ]
            dropdown = None
            for candidate in dropdown_candidates:
                try:
                    dropdown = page.locator(candidate).first
                    await dropdown.wait_for(timeout=2000)
                    break
                except: continue
            if dropdown:
                try:
                    opt = dropdown.get_by_role("option", name=r"v1", exact=False)
                    if await opt.count() > 0:
                        await opt.first.scroll_into_view_if_needed()
                        await opt.first.click()
                        picked = True
                        logger.info("V1 pick: via role/option inside dropdown")
                except: pass
            if dropdown and not picked:
                try:
                    opt_text = dropdown.locator("text=/v1/i").first
                    await opt_text.wait_for(timeout=1000)
                    await opt_text.click()
                    picked = True
                    logger.info("V1 pick: via visible text inside dropdown")
                except: pass
            if dropdown and not picked:
                for sel in ["[data-testid='version-v1']", "[data-value='v1']", "[data-variant='v1']", "button:has-text('v1')"]:
                    try:
                        el = dropdown.locator(sel).first
                        await el.wait_for(timeout=1000)
                        await el.click()
                        picked = True
                        logger.info(f"V1 pick: via {sel} plastic inside dropdown")
                        break
                    except: continue
            if not picked:
                try:
                    opt = page.get_by_role("option", name=r"v1", exact=False)
                    if await opt.count() > 0:
                        await opt.first.scroll_into_view_if_needed()
                        await opt.first.click()
                        picked = True
                        logger.info("V1 pick: fallback to whole page by role/option")
                except: pass
            if not picked:
                try:
                    opt_text = page.locator("text=/v1/i").first
                    await opt_text.wait_for(timeout=1000)
                    await opt_text.click()
                    picked = True
                    logger.info("V1 pick: fallback to whole page by visible text")
                except: pass
            if not picked:
                try:
                    await page.keyboard.type('v')
                    await page.keyboard.press('Enter')
                    picked = True
                    logger.info("V1 pick: fallback by keyboard")
                except: pass
            if not picked:
                logger.warning('V1 модель по меню НЕ выбрана (выполнен весь набор стратегий). См. скрин.')
                await page.screenshot(path='v1_failed.png')
            else:
                logger.info("V1 модель выбрана успешно")
        except Exception as e:
            logger.warning(f'Выбор V1 модели не удался: {e}')
            try:
                await page.screenshot(path='v1_error.png')
            except: pass

        # 3. Клик по кнопке Generate и НАЧАЛО ожидания результата
        generate_button_selector = 'body > div > div > div.flex-1.flex.flex-col > main > div > div > div > div.px-8.pt-1 > div > div > div.absolute.bottom-3.right-4.flex.items-center.gap-3 > button.inline-flex.items-center.justify-center.gap-2.whitespace-nowrap.ring-offset-background.focus-visible\\:outline-none.focus-visible\\:ring-2.focus-visible\\:ring-ring.focus-visible\\:ring-offset-2.disabled\\:pointer-events-none.disabled\\:opacity-50.\\[\\&_svg\\]\\:pointer-events-none.\\[\\&_svg\\]\\:size-4.\\[\\&_svg\\]\\:shrink-0.hover\\:bg-primary\\/90.py-2.px-6.h-8.rounded-lg.bg-gradient-to-r.from-blue-600.via-blue-500.to-blue-400.hover\\:from-blue-700.hover\\:via-blue-600.hover\\:to-blue-500.disabled\\:from-gray-300.disabled\\:to-gray-400.disabled\\:cursor-not-allowed.shadow-lg.hover\\:shadow-xl.transition-all.duration-200.text-white.font-medium.text-sm.border-0'
        try:
            logger.info('Перед поиском кнопки Generate...')
            await page.wait_for_selector(generate_button_selector, timeout=15000)
            generate_button = await page.query_selector(generate_button_selector)
            if not generate_button:
                logger.error('Кнопка генерации не найдена (None)')
                raise Exception('Кнопка генерации не найдена!')
            await generate_button.scroll_into_view_if_needed()
            await generate_button.hover(timeout=1500)
            await generate_button.click()
            logger.info("Кнопка Generate нажата. Ждем появления итогового изображения...")
        except Exception as e:
            logger.error(f"Ошибка при поиске/клике по кнопке генерации: {e}")
            raise

        # Вот теперь — цикл ожидания итогового <img>
        final_img_selector = 'img[src*="makefilm.ai"][src$=".jpg"]:not([src*="thumb"])'
        logger.info("Ожидание появления итогового <img> после старта генерации...")
        img_src = None
        for i in range(300):
            try:
                img = await page.query_selector(final_img_selector)
                src = await img.get_attribute('src') if img else None
                if img and src and 'thumb' not in src:
                    img_src = src
                    logger.info(f'Готовое фото найдено: {src}')
                    break
            except Exception as e:
                logger.info(f'wait img error: {e}')
            await page.wait_for_timeout(1000)
        else:
            logger.warning('Финальное фото не появилось, продолжаем без него.')
        # Remove watermark и download
        menu_selector = "#radix-:ru:"
        remove_selector = "text=/remove watermark/i"
        try:
            logger.info("Ожидаю меню watermark...")
            await page.wait_for_selector(menu_selector, timeout=8000)
            await page.click(menu_selector)
            await page.wait_for_timeout(350)
            logger.info("Ожидаю Remove watermark...")
            await page.wait_for_selector(remove_selector, timeout=5000)
            async with page.expect_download(timeout=15000) as download_info:
                await page.click(remove_selector)
            download = await download_info.value
            file_path = os.path.join("/tmp", f"nofilter_{download.suggested_filename}")
            await download.save_as(file_path)
            logger.info(f"Фото без watermark скачано: {file_path}")
        except Exception as e:
            logger.warning(f"Remove watermark/download fail: {e}")
            file_path = None
        return result_url, img_src, file_path
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        return None, None, None
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
    
    auth_state_exists = os.path.exists(AUTH_STATE_PATH)
    if auth_state_exists:
        status_text += f"🟢 Состояние авторизации найдено: {AUTH_STATE_PATH}\n"
    else:
        status_text += f"🔴 Состояние авторизации не найдено: {AUTH_STATE_PATH}\n"
    
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
        result_url, img_src, file_path = await process_makefilm_request(user_prompt)
        
        photo_sent = False
        # Отправка уже готового файла из download
        if file_path:
            try:
                with open(file_path, "rb") as photo_file:
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=photo_file,
                        caption=f"🖼️ Ваше изображение без watermark\nПромпт: {user_prompt}"
                    )
                photo_sent = True
            except Exception as e:
                logger.warning(f"Ошибка при отправке файла: {e}")
        # Пытаемся скачать по direct src
        if not photo_sent and img_src:
            try:
                import aiohttp
                logger.info('Скачиваю изображение по <img src> через aiohttp...')
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_src) as resp:
                        if resp.status == 200:
                            img_path = "/tmp/alt_img.jpg"
                            with open(img_path, "wb") as f:
                                f.write(await resp.read())
                            with open(img_path, "rb") as f:
                                await bot.send_photo(
                                    chat_id=message.chat.id,
                                    photo=f,
                                    caption=f"🖼️ Ваше изображение (резервно, через <img src>)\nПромпт: {user_prompt}"
                                )
                            photo_sent = True
            except Exception as e:
                logger.warning(f"Reserve img download failed: {e}")
        # Фолбек — только ссылка если всё не удалось
        if not photo_sent:
            await processing_msg.edit_text(
                f"🖼️ Ваше изображение готово!\n\n"
                f"📝 Промпт: {user_prompt}\n"
                f"🔗 Ссылка: {result_url}\n\n"
                f"⏰ Время обработки: {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            await processing_msg.edit_text("🖼️ Файл сгенерирован и отправлен!\nПроверьте последний медиа-файл в чате.")
        
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
        logger.info("Запуск Telegram бота с сохраненным состоянием авторизации...")
        
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
