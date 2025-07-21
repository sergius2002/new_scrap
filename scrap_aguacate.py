#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import nest_asyncio
import telebot
from playwright.async_api import async_playwright
import time
import logging
import shutil
import tempfile
import json

# Permitir la ejecución anidada de loops de eventos
nest_asyncio.apply()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Inicializar el bot con el token proporcionado
bot = telebot.TeleBot('7442937067:AAEK2y8mULc6FAM4CTyuyrUM0hySZNdq5EY')

# Definir el chat ID del grupo directamente
default_chat_id = '-4090514300'

# Variables globales para el navegador
browser = None
page = None

# Archivo para almacenar los valores anteriores
VALUES_FILE = 'previous_values.json'

def load_previous_values():
    try:
        if os.path.exists(VALUES_FILE):
            with open(VALUES_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error al cargar valores anteriores: {str(e)}")
    return {
        'minimos_inferior': None,
        'minimos_superior': None,
        'banesco_inferior': None,
        'venezuela_inferior': None,
        'banesco_superior': None,
        'venezuela_superior': None
    }

def save_previous_values(values):
    try:
        with open(VALUES_FILE, 'w') as f:
            json.dump(values, f)
    except Exception as e:
        logging.error(f"Error al guardar valores anteriores: {str(e)}")

# Función para enviar mensajes a Telegram con reintentos
def safe_send_message(chat_id, message, parse_mode=None):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            bot.send_message(chat_id, message, parse_mode=parse_mode)
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Error enviando mensaje (intento {attempt + 1}): {str(e)}. Reintentando...")
                time.sleep(5)
            else:
                logging.error(f"Fallo tras {max_retries} intentos enviando mensaje: {str(e)}")

def compare_values(old_value, new_value):
    if old_value is None or new_value is None:
        return ""
    
    try:
        old = float(old_value.replace('$', '').replace(',', '').strip())
        new = float(new_value.replace('$', '').replace(',', '').strip())
        
        if new > old:
            return "📈"
        elif new < old:
            return "📉"
        else:
            return "🟰"
    except:
        return ""

async def cleanup_playwright_temp():
    """Limpia los archivos temporales de Playwright"""
    temp_dir = tempfile.gettempdir()
    playwright_temp = os.path.join(temp_dir, "playwright-artifacts-*")
    
    try:
        for item in os.listdir(temp_dir):
            if item.startswith("playwright-artifacts-"):
                full_path = os.path.join(temp_dir, item)
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    logging.info(f"Directorio temporal eliminado: {full_path}")
    except Exception as e:
        logging.error(f"Error al limpiar archivos temporales: {str(e)}")

async def initialize_browser():
    global browser, page
    if page:
        await page.close()
    if browser:
        await browser.close()
    
    await cleanup_playwright_temp()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto("https://www.aguacatewallet.com/auth/login")
    email_input = page.locator('input[name="email"]')
    password_input = page.locator('input[name="password"]')
    login_button = page.locator('button[type="submit"]')

    await email_input.fill("sergio.plaza.altamirano@gmail.com")
    await password_input.fill("karjon-razHiv-puvru2")
    await login_button.click()

    menu_button = page.locator('button:has-text("menu")')
    await menu_button.click()

    remesas_button = page.locator('span.pl-5.flex.flex-row.justify-start.gap-8:has-text("Remesas")')
    await remesas_button.click()

    await page.wait_for_selector('h1.text-lg.my-7', timeout=60000)

async def is_session_expired():
    global page
    current_url = page.url
    if "auth/login" in current_url:
        return True
    try:
        await page.wait_for_selector('h1.text-lg.my-7', timeout=10000)
        return False
    except Exception:
        try:
            login_input = page.locator('input[name="email"]')
            return await login_input.is_visible(timeout=5000)
        except Exception:
            return True

async def extract_data():
    global page
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if await is_session_expired():
                logging.info("Sesión expirada. Reestableciendo sesión...")
                await initialize_browser()

            await page.reload()
            await page.wait_for_selector('h1.text-lg.my-7', timeout=60000)

            minimos_inferior = (await page.locator('h1.text-lg.my-7').nth(0).text_content()).strip().replace("Mínimo", "").strip()
            minimos_superior = (await page.locator('h1.text-lg.my-7').nth(1).text_content()).strip().replace("Mínimo", "").strip()
            banesco_inferior = (await page.locator('span.text-xl.font-bold').nth(0).text_content()).strip()
            venezuela_inferior = (await page.locator('span.text-xl.font-bold').nth(1).text_content()).strip()
            banesco_superior = (await page.locator('xpath=/html/body/app-root/ng-component/app-navbar/mat-sidenav-container/mat-sidenav-content/div/app-remittance/div/div/app-rates/div/div[2]/app-rate-value-card[1]/mat-card/div/div/span[1]').text_content()).strip()
            venezuela_superior = (await page.locator('xpath=/html/body/app-root/ng-component/app-navbar/mat-sidenav-container/mat-sidenav-content/div/app-remittance/div/div/app-rates/div/div[2]/app-rate-value-card[4]/mat-card/div/div/span[1]').text_content()).strip()

            # Cargar valores anteriores
            previous_values = load_previous_values()

            # Comparar valores
            minimos_inferior_icon = compare_values(previous_values['minimos_inferior'], minimos_inferior)
            banesco_inferior_icon = compare_values(previous_values['banesco_inferior'], banesco_inferior)
            venezuela_inferior_icon = compare_values(previous_values['venezuela_inferior'], venezuela_inferior)
            minimos_superior_icon = compare_values(previous_values['minimos_superior'], minimos_superior)
            banesco_superior_icon = compare_values(previous_values['banesco_superior'], banesco_superior)
            venezuela_superior_icon = compare_values(previous_values['venezuela_superior'], venezuela_superior)

            # Guardar nuevos valores
            new_values = {
                'minimos_inferior': minimos_inferior,
                'minimos_superior': minimos_superior,
                'banesco_inferior': banesco_inferior,
                'venezuela_inferior': venezuela_inferior,
                'banesco_superior': banesco_superior,
                'venezuela_superior': venezuela_superior
            }
            save_previous_values(new_values)

            resultado = (
                    "<pre>"
                    "📊 Datos Extraídos:\n\n"
                    "{:<22} : {} {}\n".format("Mínimos ", minimos_inferior, minimos_inferior_icon) +
                    "{:<22} : {} {}\n".format("Banesco ", banesco_inferior, banesco_inferior_icon) +
                    "{:<22} : {} {}\n\n".format("Venezuela ", venezuela_inferior, venezuela_inferior_icon) +
                    "{:<22} : {} {}\n".format("Mínimos ", minimos_superior, minimos_superior_icon) +
                    "{:<22} : {} {}\n".format("Banesco ", banesco_superior, banesco_superior_icon) +
                    "{:<22} : {} {}".format("Venezuela ", venezuela_superior, venezuela_superior_icon) +
                    "</pre>"
            )
            return resultado

        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Intento {attempt + 1} falló: {str(e)}. Reintentando...")
                await asyncio.sleep(5)
            else:
                logging.error(f"Error persistente tras {max_retries} intentos: {str(e)}")
                return f"❌ Error tras {max_retries} intentos: {str(e)}"

async def close_browser():
    global browser, page
    if page:
        await page.close()
        page = None
    if browser:
        await browser.close()
        browser = None
    
    await cleanup_playwright_temp()

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    safe_send_message(message.chat.id,
                      "¡Hola! Usa /agua para obtener los datos actuales de las tasas.")

# Comando /agua
@bot.message_handler(commands=['agua'])
def handle_agua(message):
    async def run_extraction():
        try:
            await initialize_browser()
            resultado = await extract_data()
            safe_send_message(message.chat.id, resultado, parse_mode="HTML")
        except Exception as e:
            safe_send_message(message.chat.id, f"❌ Error al extraer datos: {str(e)}")
        finally:
            await close_browser()

    asyncio.run(run_extraction())

# Función para manejar el polling con reintentos
def run_polling():
    while True:
        try:
            logging.info("Iniciando polling...")
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            logging.error(f"Error en polling: {str(e)}. Reintentando en 10 segundos...")
            time.sleep(10)

# Iniciar el bot
if __name__ == '__main__':
    logging.info("Bot iniciado...")
    run_polling()