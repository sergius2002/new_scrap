import asyncio
import re
import datetime
from datetime import timedelta
import hashlib
import subprocess
import sys
import time
import os
import shutil
import tempfile
from playwright.async_api import async_playwright
from openpyxl import Workbook
import pandas as pd
from saldo_bancos_db import SaldoBancosDB

# --------------------------
# PRINTS DE DEPURACIÓN
# --------------------------
print("INICIO SCRIPT")
print(f"Directorio actual: {os.getcwd()}")
print(f"Archivos en carpeta actual: {os.listdir('.')}")
print("-" * 50)


# --------------------------
# Funciones Auxiliares
# --------------------------

async def fill_input(frame, selector, text):
    """Rellena un campo de entrada en el frame especificado."""
    await frame.click(selector)
    await frame.fill(selector, "")
    await frame.type(selector, text, delay=100)  # Simula tipeo humano


async def click_with_retries(page, frame, selector, max_retries=3):
    """Intenta hacer clic en un elemento con varios reintentos."""
    for attempt in range(max_retries):
        try:
            if not frame.is_detached():
                await frame.wait_for_selector(selector, state="visible", timeout=7000)
                await frame.hover(selector)
                await frame.click(selector)
                print(f"Click en '{selector}' exitoso en el intento {attempt + 1}")
                return
            else:
                print("El frame fue desvinculado. Reintentando obtener el frame...")
                frame = await get_target_frame(page)
                if not frame:
                    raise Exception("No se pudo obtener el frame luego de que fue desvinculado.")
        except PlaywrightTimeoutError:
            print(f"Intento {attempt + 1} fallido al hacer clic en '{selector}': Timeout.")
        except Exception as e:
            print(f"Intento {attempt + 1} fallido al hacer clic en '{selector}': {e}")
        await asyncio.sleep(1)
    raise Exception(f"No se pudo hacer clic en '{selector}' tras {max_retries} intentos.")


async def get_target_frame(page):
    """Obtiene un frame cuyo URL contenga 'appempresas.bancoestado.cl' o retorna None."""
    frames = page.frames
    print(f"🔍 DEBUG: Total de frames encontrados: {len(frames)}")
    
    for i, frame in enumerate(frames):
        print(f"🔍 DEBUG: Frame {i+1}: {frame.url}")
        if re.search(r"appempresas\.bancoestado\.cl", frame.url):
            print(f"✅ Frame objetivo encontrado: {frame.url}")
            return frame
    
    print("❌ No se encontró el frame objetivo.")
    print("🔍 DEBUG: Buscando frames que contengan 'bancoestado'...")
    
    for i, frame in enumerate(frames):
        if "bancoestado" in frame.url.lower():
            print(f"🔍 DEBUG: Frame con 'bancoestado' encontrado {i+1}: {frame.url}")
    
    return None


async def find_and_click(context, selector):
    """Busca y hace clic en un elemento en el contexto dado (Page o Frame)."""
    try:
        if await context.is_visible(selector):
            await context.hover(selector)
            await context.click(selector)
            print(f"Click en '{selector}' exitoso en el contexto dado.")
            return True
    except Exception as e:
        print(f"Error al intentar clic en '{selector}' en el contexto dado: {e}")
    return False


async def extract_transfers(iframe):
    """Extrae datos de la tabla de Transferencias Recibidas en la página actual."""
    try:
        await iframe.wait_for_selector("table.table__container", state="visible", timeout=15000)
        print("Tabla encontrada, extrayendo datos...")
    except PlaywrightTimeoutError:
        print("No se encontró la tabla de transferencias.")
        return []

    table = await iframe.query_selector("table.table__container")
    if not table:
        print("Tabla de transferencias no encontrada.")
        return []

    rows = await table.query_selector_all("tbody tr")
    transfers = []
    print(f"Se encontraron {len(rows)} filas en la tabla")
    
    for row in rows:
        cols = await row.query_selector_all("td")
        if len(cols) < 7:
            continue
            
        try:
            num_operacion = (await cols[0].inner_text()).strip()
            fecha_hora = (await cols[1].inner_text()).strip()
            cuenta_destino = (await cols[2].inner_text()).strip()
            rut_origen = (await cols[3].inner_text()).strip()
            cuenta_origen = (await cols[4].inner_text()).strip()
            nombre_origen = (await cols[5].inner_text()).strip()
            monto = (await cols[6].inner_text()).strip()
            
            # Limpiar el monto
            monto = monto.replace("$", "").replace(".", "").replace(" ", "").strip()
            
            transfer = {
                "N° Operación": num_operacion,
                "Fecha - Hora": fecha_hora,
                "Cuenta Destino": cuenta_destino,
                "Rut Origen": rut_origen,
                "Cuenta Origen": cuenta_origen,
                "Nombre Origen": nombre_origen,
                "Monto": monto
            }
            transfers.append(transfer)
            print(f"Transferencia extraída: {num_operacion} - {monto}")
            
        except Exception as e:
            print(f"Error al procesar una fila: {e}")
            continue
            
    return transfers


async def extract_all_transfers(iframe):
    """Extrae datos de todas las páginas de la tabla de Transferencias Recibidas."""
    all_transfers = []
    page_num = 1
    previous_first_op = None

    while True:
        print(f"\nExtrayendo datos de la página {page_num}...")
        transfers = await extract_transfers(iframe)
        if not transfers:
            print("No se encontraron transferencias en esta página, finalizando paginación.")
            break

        current_first_op = transfers[0].get("N° Operación", "")
        if previous_first_op is not None and current_first_op == previous_first_op:
            print("El contenido de la tabla no ha cambiado. Fin de la paginación.")
            break

        previous_first_op = current_first_op
        print(f"Se extrajeron {len(transfers)} transferencias en la página {page_num}")
        all_transfers.extend(transfers)

        try:
            next_button = iframe.locator("(//div[contains(.,'Siguiente')])[15]")
            if await next_button.count() == 0:
                print("No se encontró el botón 'Siguiente'. Fin de la paginación.")
                break

            await next_button.scroll_into_view_if_needed()
            await next_button.wait_for(state="visible", timeout=5000)

            disabled_attr = await next_button.get_attribute("disabled")
            if disabled_attr is not None:
                print("El botón 'Siguiente' está deshabilitado. Fin de la paginación.")
                break

            print("Avanzando a la siguiente página...")
            await next_button.click()
            await iframe.wait_for_timeout(3000)
            page_num += 1
        except Exception as e:
            print(f"No se pudo avanzar a la siguiente página: {e}")
            break

    print(f"Total de transferencias extraídas: {len(all_transfers)}")
    return all_transfers


def export_to_excel(transfers, filename="transferencias_combinadas.xlsx"):
    """Transforma y exporta la lista de transferencias a un archivo Excel."""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Transferencias"

        headers = ["N° Operación", "fecha_detec", "fecha", "rs", "rut", "monto", "facturación", "empresa", "hash", "cuenta"]
        ws.append(headers)

        for transfer in transfers:
            try:
                op = str(transfer.get("N° Operación", "")).strip()
                fecha_detec = str(transfer.get("Fecha - Hora", "")).strip()
                try:
                    fecha_part = fecha_detec.split(" ")[0]
                    fecha_obj = datetime.datetime.strptime(fecha_part, "%d/%m/%Y")
                    fecha = fecha_obj.strftime("%Y-%m-%d")
                except Exception:
                    fecha = ""
                rs = str(transfer.get("Nombre Origen", "")).strip()
                rut_raw = str(transfer.get("Rut Origen", ""))
                rut = rut_raw.replace(" ", "").replace(".", "").strip()
                monto_raw = str(transfer.get("Monto", "")).strip()
                try:
                    monto_clean = monto_raw.replace("$", "").replace(".", "").replace(" ", "").replace(",", "")
                    monto = int(monto_clean)
                except Exception:
                    monto = 0
                try:
                    rut_num_str = rut.split("-")[0]
                    rut_num = int(rut_num_str)
                    facturacion = "empresa" if rut_num > 50000000 else "persona"
                except Exception:
                    facturacion = ""
                
                # Asignar empresa basada en el RUT de la empresa
                rut_empresa = str(transfer.get("rut_empresa", "")).strip()
                empresa = ""
                if rut_empresa == "774691731":
                    empresa = "STS CRISTOBAL"
                elif rut_empresa == "777734482":
                    empresa = "DETAL"
                elif rut_empresa == "77936187K":
                    empresa = "ST CRISTOBAL ESTADO"
                
                # Crear el hash primero
                hash_input = f"{int(op)}{fecha_detec}{int(monto)}{rut}{empresa}{rs}"
                hash_md5 = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
                
                # Después de crear el hash, agregar el prefijo "BANCO ESTADO" al nombre de la empresa
                if empresa:
                    if empresa == "ST CRISTOBAL ESTADO":
                        # Mantener "ST CRISTOBAL ESTADO" sin cambios
                        pass
                    elif empresa == "STS CRISTOBAL":
                        # Cambiar "STS CRISTOBAL" a "STS ESTADO"
                        empresa = "STS ESTADO"
                    else:
                        # Agregar prefijo "BANCO ESTADO" a las otras empresas
                        empresa = f"BANCO ESTADO {empresa}"
                
                cuenta = str(transfer.get("cuenta", "")).strip()

                row = [op, fecha_detec, fecha, rs, rut, monto, facturacion, empresa, hash_md5, cuenta]
                ws.append(row)
            except Exception as e:
                print(f"Error al procesar transferencia: {e}")
                continue

        # Crear directorio para los archivos si no existe
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar el archivo en el directorio de salida
        file_path = os.path.join(output_dir, filename)
        wb.save(file_path)
        print(f"Archivo Excel guardado en: {file_path}")
        print(f"Total de transferencias guardadas: {len(transfers)}")
    except Exception as e:
        print(f"Error al guardar el archivo Excel: {e}")


async def cleanup_playwright_temp():
    """Limpia los archivos temporales de Playwright"""
    temp_dir = tempfile.gettempdir()
    try:
        # Encontrar y eliminar directorios temporales de Playwright
        for item in os.listdir(temp_dir):
            if item.startswith("playwright-artifacts-"):
                full_path = os.path.join(temp_dir, item)
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    print(f"Directorio temporal eliminado: {full_path}")
    except Exception as e:
        print(f"Error al limpiar archivos temporales: {e}")


async def cleanup_browser_resources(browser, context_browser, page):
    """Limpia los recursos del navegador en el orden correcto"""
    try:
        if page:
            await page.close()
            print("Página cerrada correctamente")
        if context_browser:
            await context_browser.close()
            print("Contexto del navegador cerrado correctamente")
        if browser:
            await browser.close()
            print("Navegador cerrado correctamente")
        await cleanup_playwright_temp()
    except Exception as e:
        print(f"Error al limpiar recursos del navegador: {e}")


async def capturar_saldo_cuenta(page, account):
    """Captura el saldo de la cuenta corriente desde la interfaz web de Banco Estado"""
    try:
        print(f"💰 Iniciando captura de saldo para cuenta {account['rutEmpresa']}...")
        
        # El saldo está disponible inmediatamente después del login
        # Buscar el elemento específico que contiene el saldo
        saldo_encontrado = None
        
        # Selectores específicos para el saldo de Banco Estado
        selectores_saldo = [
            # Selector específico basado en el atributo _ngcontent
            "div[_ngcontent-ng-c2349411678][aria-hidden='true']",
            # Selectores alternativos por si cambia el atributo
            "div[aria-hidden='true']",
            # Selectores más generales
            "div:has-text('$')",
            "[class*='saldo']",
            "[class*='balance']",
            "[class*='disponible']"
        ]
        
        print("🔍 Buscando saldo en la página principal...")
        
        for selector in selectores_saldo:
            try:
                print(f"   Probando selector: {selector}")
                elementos = await page.query_selector_all(selector)
                
                for elemento in elementos:
                    texto = await elemento.text_content()
                    if texto and '$' in texto:
                        # Limpiar el texto y verificar que sea un saldo válido
                        texto_limpio = texto.strip()
                        # Buscar patrones de saldo (ej: $658.356)
                        patron_saldo = r'\$[\d,\.]+(?:,\d{2})?'
                        match = re.search(patron_saldo, texto_limpio.replace(' ', ''))
                        if match:
                            saldo_texto = match.group()
                            print(f"💰 Saldo encontrado con selector '{selector}': {saldo_texto}")
                            saldo_encontrado = saldo_texto
                            break
                
                if saldo_encontrado:
                    break
                    
            except Exception as e:
                print(f"   Error con selector '{selector}': {e}")
                continue
        
        # Si no encontramos con selectores específicos, buscar en todo el contenido
        if not saldo_encontrado:
            print("🔍 Buscando saldo en todo el contenido de la página...")
            try:
                contenido_pagina = await page.content()
                
                # Buscar específicamente el patrón del ejemplo: $658.356
                patrones_saldo = [
                    r'\$[\d,\.]+(?<![\d,\.])',  # Patrón principal para saldos
                    r'Saldo\s*[:\-]?\s*\$[\d,\.]+',
                    r'Disponible\s*[:\-]?\s*\$[\d,\.]+',
                    r'Balance\s*[:\-]?\s*\$[\d,\.]+',
                ]
                
                for patron in patrones_saldo:
                    matches = re.findall(patron, contenido_pagina, re.IGNORECASE)
                    if matches:
                        # Tomar el primer match que parezca un saldo válido
                        for match in matches:
                            # Verificar que el match tenga al menos 3 dígitos (para evitar precios pequeños)
                            numeros = re.findall(r'\d+', match)
                            if numeros and len(''.join(numeros)) >= 3:
                                saldo_encontrado = match
                                print(f"💰 Saldo encontrado en contenido: {saldo_encontrado}")
                                break
                        if saldo_encontrado:
                            break
                            
            except Exception as e:
                print(f"❌ Error buscando saldo en contenido: {e}")
        
        if saldo_encontrado:
            # Normalizar el saldo
            saldo_normalizado = normalizar_saldo(saldo_encontrado)
            if saldo_normalizado is not None:
                print(f"✅ Saldo capturado exitosamente: ${saldo_normalizado:,.2f}")
                return saldo_normalizado
            else:
                print(f"❌ No se pudo normalizar el saldo: {saldo_encontrado}")
        else:
            print("❌ No se encontró información de saldo en la página")
        
        return None
        
    except Exception as e:
        print(f"❌ Error capturando saldo: {str(e)}")
        return None


def normalizar_saldo(saldo_texto):
    """Normaliza el texto del saldo a un número float - Formato chileno (punto como separador de miles)"""
    try:
        # Limpiar el texto: quitar todo excepto números y puntos
        saldo_limpio = re.sub(r'[^\d\.]', '', saldo_texto)
        
        # En Chile, el punto es separador de miles, NO decimales
        # Ejemplos: $620.014 = 620014, $1.234.567 = 1234567
        
        if '.' in saldo_limpio:
            # Quitar todos los puntos (separadores de miles)
            saldo_limpio = saldo_limpio.replace('.', '')
        
        # Convertir a float (sin decimales ya que en Chile no se usan)
        return float(saldo_limpio)
        
    except Exception as e:
        print(f"Error normalizando saldo '{saldo_texto}': {e}")
        return None


def guardar_saldo_estado(account, saldo):
    """Guarda el saldo de Banco Estado en la base de datos"""
    try:
        # Crear identificador único para cada cuenta de Banco Estado
        nombre_cuenta = f"ESTADO_{account['rutEmpresa']}"
        
        print(f"💾 Guardando saldo de {nombre_cuenta}...")
        print(f"   💰 Saldo actual a guardar: ${saldo:,.2f}")
        
        # Inicializar base de datos
        db = SaldoBancosDB()
        
        # Obtener último saldo para comparar
        ultimo_registro = db.obtener_ultimo_saldo(nombre_cuenta)
        if ultimo_registro:
            ultimo_saldo = ultimo_registro['saldo']
            diferencia = abs(saldo - ultimo_saldo)
            print(f"   📊 Último saldo en BD: ${ultimo_saldo:,.2f}")
            print(f"   📈 Diferencia: ${diferencia:,.2f}")
        else:
            print(f"   📝 Primera vez registrando {nombre_cuenta}")
        
        # Guardar saldo usando la nueva lógica (solo si hay cambios)
        guardado_db = db.guardar_saldo(nombre_cuenta, saldo)
        if guardado_db:
            print(f"💾 ✅ Saldo guardado exitosamente en base de datos: ${saldo:,.2f}")
        else:
            print(f"⏭️ ❌ Saldo NO guardado en BD (sin cambios significativos)")
        
        return guardado_db
        
    except Exception as e:
        print(f"❌ Error guardando saldo en base de datos: {str(e)}")
        return False


# --------------------------
# Procesamiento de Cuenta
# --------------------------

async def process_account(account, p):
    """Procesa una cuenta: inicia sesión, extrae información y cierra sesión."""
    browser = None
    context_browser = None
    page = None
    account_transfers = []

    try:
        browser = await p.chromium.launch(headless=False,
                                      args=["--disable-blink-features=AutomationControlled", "--start-maximized"])
        context_browser = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        page = await context_browser.new_page()

        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
            Object.defineProperty(navigator, 'oscpu', { get: () => 'Windows NT 10.0; Win64; x64' });
            Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)

        print("Navegando a la página de login de BancoEstado Empresas...")
        await page.goto(
            "https://www.bancoestado.cl/content/bancoestado-public/cl/es/home/inicio---bancoestado-empresas.html#/login-empresa",
            wait_until="networkidle")
        await page.wait_for_load_state("networkidle")
        
        # Esperar adicional para que los frames se carguen completamente
        print("⏳ Esperando a que los frames se carguen completamente...")
        await asyncio.sleep(10)  # Espera adicional de 10 segundos
        
        # Intentar múltiples veces encontrar el frame
        target_frame = None
        max_attempts = 5
        for attempt in range(max_attempts):
            print(f"🔍 Intento {attempt + 1}/{max_attempts} para encontrar el frame...")
            target_frame = await get_target_frame(page)
            if target_frame:
                break
            print(f"⏳ Frame no encontrado, esperando 5 segundos antes del siguiente intento...")
            await asyncio.sleep(5)
        if not target_frame:
            print("No se encontró el frame de login.")
            return account_transfers

        print("Rellenando el campo RUT de la Empresa...")
        await target_frame.wait_for_selector("input#rutEmpresa", state="visible", timeout=7000)
        await fill_input(target_frame, "input#rutEmpresa", account["rutEmpresa"])

        print("Rellenando el campo RUT de la Persona...")
        await target_frame.wait_for_selector("input#rutPersona", state="visible", timeout=7000)
        await fill_input(target_frame, "input#rutPersona", account["rutPersona"])

        print("Rellenando el campo Contraseña...")
        await target_frame.wait_for_selector("input#idPassword", state="visible", timeout=7000)
        await fill_input(target_frame, "input#idPassword", account["password"])

        print("Haciendo clic en el botón de inicio de sesión...")
        await click_with_retries(page, target_frame, "button.dsd-button.primary")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)

        # *** CAPTURAR SALDO ANTES DE IR A TRANSFERENCIAS ***
        print("\n🏦 === CAPTURANDO SALDO DE LA CUENTA ===")
        saldo_capturado = await capturar_saldo_cuenta(page, account)
        if saldo_capturado:
            # Guardar saldo en base de datos
            guardar_saldo_estado(account, saldo_capturado)
        else:
            print("⚠️ No se pudo capturar el saldo de la cuenta")
        
        print("\n📋 === PROCESANDO TRANSFERENCIAS ===")
        print("Haciendo clic en 'Transferencias'...")
        transferencias_xpath = "//body/be-root/div[@class='app-home']/div[@class='ng-star-inserted']/div[@class='container-home']/div[@class='asd-container-sidebar']/be-menu/asd-menu-sidebar/div[@class='menu-sidebar-home ng-star-inserted']/nav[@class='menu-sidebar-home__content']/ul[@class='link_list']/li[2]/a[1]"
        await page.wait_for_selector(transferencias_xpath, state="visible", timeout=15000)
        await page.click(transferencias_xpath)
        await asyncio.sleep(3)

        print("Haciendo clic en 'Consultar'...")
        consultar_xpath = "//div[@class='asd-container-sidebar']//ul[@id='Transferencias']//div[@class='submenu-link-name'][normalize-space()='Consultar']"
        await page.wait_for_selector(consultar_xpath, state="visible", timeout=15000)
        await page.click(consultar_xpath)
        await asyncio.sleep(3)

        print("Cambiando al iframe de consultas-transferencias...")
        iframes = page.frames
        iframe = next((frame for frame in iframes if "consultas-transferencias-pj-app" in frame.url), None)
        if not iframe:
            print("No se encontró el iframe de consultas-transferencias")
            return account_transfers

        print("Haciendo clic en 'Recibidas'...")
        await iframe.wait_for_selector('li:has-text("Recibidas")', state="visible", timeout=15000)
        await iframe.click('li:has-text("Recibidas")')
        await asyncio.sleep(3)

        print("Calculando rango de fechas...")
        fecha_final = datetime.datetime.now()
        fecha_inicial = fecha_final - datetime.timedelta(days=5)
        
        print("Ingresando fechas...")
        fecha_inicial_str = fecha_inicial.strftime("%d/%m/%Y")
        fecha_final_str = fecha_final.strftime("%d/%m/%Y")
        
        try:
            # Esperar a que el formulario esté disponible
            await iframe.wait_for_selector('form', state="visible", timeout=10000)
            await asyncio.sleep(5)  # Dar más tiempo para que todo cargue
            
            # Intentar ingresar fecha inicial
            try:
                print("Intentando ingresar fecha inicial...")
                # Esperar y hacer clic en el primer campo de fecha
                await iframe.wait_for_selector('dsd-datepicker-only input[type="text"]', state="visible", timeout=10000)
                await iframe.click('dsd-datepicker-only input[type="text"]')
                await asyncio.sleep(2)
                
                # Limpiar y escribir la fecha
                await iframe.fill('dsd-datepicker-only input[type="text"]', "")
                await asyncio.sleep(1)
                await iframe.type('dsd-datepicker-only input[type="text"]', fecha_inicial_str, delay=100)
                await asyncio.sleep(2)
                
                # Presionar Tab para mover el foco al siguiente campo
                await page.keyboard.press('Tab')
                await asyncio.sleep(1)
                
                # Escribir la fecha final directamente
                fecha_final_ddmmyyyy = fecha_final.strftime("%d%m%Y")
                await page.keyboard.type(fecha_final_ddmmyyyy, delay=100)
                await asyncio.sleep(2)
                
                print("Fechas ingresadas exitosamente")
            except Exception as e:
                print(f"Error al ingresar fechas: {e}")
                return account_transfers
            
            await asyncio.sleep(3)  # Esperar a que los cambios se apliquen
            
        except Exception as e:
            print(f"Error general al intentar ingresar fechas: {e}")
            return account_transfers
            
        print("Haciendo clic en el botón 'Consultar'...")
        await iframe.click('button:has-text("Consultar")')
        await asyncio.sleep(5)

        print("Seleccionando 200 registros por página...")
        try:
            # Esperar a que el select esté visible
            await iframe.wait_for_selector('select[name="select"]', state="visible", timeout=10000)
            print("Select encontrado, intentando seleccionar 200 registros...")
            
            # Seleccionar la opción 200
            await iframe.select_option('select[name="select"]', "200")
            print("200 registros seleccionados exitosamente")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error al seleccionar 200 registros: {e}")
            return account_transfers

        print("Extrayendo datos de la tabla...")
        try:
            # Esperar a que la tabla esté visible en el iframe
            await iframe.wait_for_selector("table.table__container", state="visible", timeout=10000)
            await asyncio.sleep(5)  # Dar tiempo extra para que todo cargue
            
            # Extraer todas las transferencias
            account_transfers = await extract_all_transfers(iframe)
            
            # Agregar el RUT de la empresa a cada transferencia
            for transfer in account_transfers:
                transfer["rut_empresa"] = account["rutEmpresa"]
            
            if account_transfers:
                print(f"Se extrajeron {len(account_transfers)} transferencias exitosamente")
                # Generar nombre de archivo basado en el RUT de la empresa
                filename = f"transferencias_{account['rutEmpresa']}.xlsx"
                # Guardar en Excel
                export_to_excel(account_transfers, filename)
            else:
                print("No se encontraron transferencias para extraer")
                
        except Exception as e:
            print(f"Error al extraer datos de la tabla: {e}")
            return account_transfers

        print("🔄 INICIANDO MODO CONTINUO - Manteniendo sesión activa...")
        print("⚠️  NO se cerrará la sesión. Procesando en bucle continuo...")
        
        # BUCLE CONTINUO - Mantener sesión activa y procesar periódicamente
        iteration_count = 0
        while True:
            try:
                iteration_count += 1
                import random
                wait_interval = random.randint(10, 15)  # Intervalo aleatorio entre 10-15 segundos
                
                print(f"\n🔄 === ITERACIÓN #{iteration_count} - {datetime.datetime.now().strftime('%H:%M:%S')} ===")
                print(f"⏱️  Próxima actualización en {wait_interval} segundos...")
                
                # Verificar que la sesión sigue activa
                try:
                    print("🔄 Manteniendo sesión activa sin recargar página...")
                    await page.wait_for_selector("body", state="visible", timeout=5000)
                    print("✅ Sesión activa confirmada")
                except Exception as e:
                    print(f"❌ Sesión perdida: {e}")
                    break
                
                # NUEVO: Hacer clic en el logo de BancoEstado para volver al inicio
                try:
                    print("🏠 Haciendo clic en logo de BancoEstado para volver al inicio...")
                    logo_selector = "path[fill='#fff'][d*='M92.203 20.98c.388-2.149']"
                    await page.wait_for_selector(logo_selector, state="visible", timeout=10000)
                    await page.click(logo_selector)
                    await asyncio.sleep(5)  # Aumentar tiempo de espera
                    print("✅ Click en logo exitoso, volviendo al inicio")
                    
                    # Esperar a que la página principal se cargue completamente
                    print("⏳ Esperando a que la página principal se cargue...")
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await asyncio.sleep(3)
                    print("✅ Página principal cargada")
                    
                except Exception as logo_error:
                    print(f"⚠️  Error al hacer clic en logo: {logo_error}")
                    continue
                
                # REPLICAR TODO EL PROCESO DESDE EL INICIO (después del login)
                
                # 1. CAPTURAR SALDO NUEVAMENTE
                print(f"\n💰 === CAPTURANDO SALDO ACTUALIZADO ===")
                print(f"Iniciando captura de saldo para cuenta {account['rutEmpresa']}...")
                
                try:
                    # Buscar saldo en la página principal
                    print("🔍 Buscando saldo en la página principal...")
                    saldo_selectors = [
                        "div[_ngcontent-ng-c2349411678][aria-hidden='true']",
                        "div.saldo-disponible",
                        "span.saldo-valor",
                        "div[class*='saldo']",
                        "span[class*='saldo']"
                    ]
                    
                    saldo_text = None
                    for selector in saldo_selectors:
                        try:
                            print(f"   Probando selector: {selector}")
                            await page.wait_for_selector(selector, state="visible", timeout=5000)
                            saldo_element = await page.query_selector(selector)
                            if saldo_element:
                                saldo_text = await saldo_element.inner_text()
                                if saldo_text and any(char.isdigit() for char in saldo_text):
                                    print(f"💰 Saldo encontrado con selector '{selector}': {saldo_text}")
                                    break
                        except Exception:
                            continue
                    
                    if saldo_text:
                        # Limpiar y formatear el saldo
                        saldo_limpio = re.sub(r'[^\d,.-]', '', saldo_text)
                        saldo_limpio = saldo_limpio.replace('.', '').replace(',', '.')
                        
                        try:
                            saldo_float = float(saldo_limpio)
                            saldo_formateado = f"${saldo_float:,.2f}"
                            print(f"✅ Saldo capturado exitosamente: {saldo_formateado}")
                            
                            # Guardar saldo en la base de datos
                            print(f"💾 Guardando saldo actualizado de ESTADO_{account['rutEmpresa']}...")
                            print(f"   💰 Saldo actual a guardar: {saldo_formateado}")
                            
                            db = SaldoBancosDB()
                            saved = db.guardar_saldo(f"ESTADO_{account['rutEmpresa']}", saldo_float)
                            
                            if saved:
                                print("✅ ✅ Saldo guardado exitosamente en BD")
                            else:
                                print("⏭️ ❌ Saldo NO guardado en BD (sin cambios significativos)")
                                
                        except ValueError as e:
                            print(f"❌ Error al convertir saldo a número: {e}")
                    else:
                        print("❌ No se pudo encontrar el saldo en la página")
                        
                except Exception as e:
                    print(f"❌ Error al capturar saldo: {e}")
                
                # 2. PROCESAR TRANSFERENCIAS NUEVAMENTE
                print(f"\n📋 === PROCESANDO TRANSFERENCIAS ACTUALIZADAS ===")
                
                try:
                    # 2. REPLICAR EXACTAMENTE EL PROCESO DE TRANSFERENCIAS
                    print(f"\n📋 === PROCESANDO TRANSFERENCIAS ACTUALIZADAS ===")
                    print("Haciendo clic en 'Transferencias'...")
                    # USAR EXACTAMENTE EL MISMO SELECTOR QUE EN EL PROCESO ORIGINAL
                    transferencias_xpath = "//body/be-root/div[@class='app-home']/div[@class='ng-star-inserted']/div[@class='container-home']/div[@class='asd-container-sidebar']/be-menu/asd-menu-sidebar/div[@class='menu-sidebar-home ng-star-inserted']/nav[@class='menu-sidebar-home__content']/ul[@class='link_list']/li[2]/a[1]"
                    
                    # Esperar a que el elemento esté visible y hacer click
                    await page.wait_for_selector(transferencias_xpath, state="visible", timeout=20000)
                    await asyncio.sleep(2)  # Pequeña pausa antes del click
                    await page.click(transferencias_xpath)
                    await asyncio.sleep(3)  # Tiempo para que se expanda el menú
                    print("✅ Click en 'Transferencias' exitoso")

                    # Hacer clic en Consultar - USAR EXACTAMENTE EL MISMO SELECTOR
                    print("Haciendo clic en 'Consultar'...")
                    consultar_xpath = "//div[@class='asd-container-sidebar']//ul[@id='Transferencias']//div[@class='submenu-link-name'][normalize-space()='Consultar']"
                    await page.wait_for_selector(consultar_xpath, state="visible", timeout=20000)
                    await asyncio.sleep(2)  # Pequeña pausa antes del click
                    await page.click(consultar_xpath)
                    await asyncio.sleep(3)  # Tiempo para que cargue la página
                    print("✅ Click en 'Consultar' exitoso")

                    # Cambiar al iframe - USAR EXACTAMENTE EL MISMO MÉTODO
                    print("Cambiando al iframe de consultas-transferencias...")
                    iframes = page.frames
                    iframe = next((frame for frame in iframes if "consultas-transferencias-pj-app" in frame.url), None)
                    if not iframe:
                        print("No se encontró el iframe de consultas-transferencias")
                        continue

                    # Hacer clic en Recibidas - USAR EXACTAMENTE EL MISMO SELECTOR
                    print("Haciendo clic en 'Recibidas'...")
                    await iframe.wait_for_selector('li:has-text("Recibidas")', state="visible", timeout=15000)
                    await iframe.click('li:has-text("Recibidas")')
                    await asyncio.sleep(3)

                    # Ingresar fechas - USAR EXACTAMENTE EL MISMO MÉTODO
                    print("Calculando rango de fechas...")
                    fecha_final = datetime.datetime.now()
                    fecha_inicial = fecha_final - datetime.timedelta(days=5)
                    
                    print("Ingresando fechas...")
                    fecha_inicial_str = fecha_inicial.strftime("%d/%m/%Y")
                    fecha_final_str = fecha_final.strftime("%d/%m/%Y")
                    
                    try:
                        # Esperar a que el formulario esté disponible
                        await iframe.wait_for_selector('form', state="visible", timeout=10000)
                        await asyncio.sleep(5)  # Dar más tiempo para que todo cargue
                        
                        # Intentar ingresar fecha inicial
                        try:
                            print("Intentando ingresar fecha inicial...")
                            # Esperar y hacer clic en el primer campo de fecha
                            await iframe.wait_for_selector('dsd-datepicker-only input[type="text"]', state="visible", timeout=10000)
                            await iframe.click('dsd-datepicker-only input[type="text"]')
                            await asyncio.sleep(2)
                            
                            # Limpiar y escribir la fecha
                            await iframe.fill('dsd-datepicker-only input[type="text"]', "")
                            await asyncio.sleep(1)
                            await iframe.type('dsd-datepicker-only input[type="text"]', fecha_inicial_str, delay=100)
                            await asyncio.sleep(2)
                            
                            # Presionar Tab para mover el foco al siguiente campo
                            await page.keyboard.press('Tab')
                            await asyncio.sleep(1)
                            
                            # Escribir la fecha final directamente
                            fecha_final_ddmmyyyy = fecha_final.strftime("%d%m%Y")
                            await page.keyboard.type(fecha_final_ddmmyyyy, delay=100)
                            await asyncio.sleep(2)
                            
                            print("Fechas ingresadas exitosamente")
                        except Exception as e:
                            print(f"Error al ingresar fechas: {e}")
                            continue
                        
                        await asyncio.sleep(3)  # Esperar a que los cambios se apliquen
                        
                    except Exception as e:
                        print(f"Error general al intentar ingresar fechas: {e}")
                        continue
                        
                    print("Haciendo clic en el botón 'Consultar'...")
                    await iframe.click('button:has-text("Consultar")')
                    await asyncio.sleep(5)

                    print("Seleccionando 200 registros por página...")
                    try:
                        # Esperar a que el select esté visible
                        await iframe.wait_for_selector('select[name="select"]', state="visible", timeout=10000)
                        print("Select encontrado, intentando seleccionar 200 registros...")
                        
                        # Seleccionar la opción 200
                        await iframe.select_option('select[name="select"]', "200")
                        print("200 registros seleccionados exitosamente")
                        await asyncio.sleep(5)
                    except Exception as e:
                        print(f"⚠️  Error al seleccionar 200 registros: {e}")

                    # Extraer datos
                    print("Extrayendo datos de la tabla...")
                    try:
                        await iframe.wait_for_selector("table.table__container", state="visible", timeout=10000)
                        await asyncio.sleep(3)
                        
                        new_transfers = await extract_all_transfers(iframe)
                        
                        if new_transfers:
                            # Agregar RUT de empresa y timestamp
                            for transfer in new_transfers:
                                transfer["rut_empresa"] = account["rutEmpresa"]
                                transfer["timestamp_captura"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            print(f"✅ Extraídas {len(new_transfers)} transferencias en iteración #{iteration_count}")
                            
                            # Guardar solo el archivo principal (eliminamos archivos de iteración)
                            main_filename = f"transferencias_{account['rutEmpresa']}.xlsx"
                            export_to_excel(new_transfers, main_filename)
                            print(f"💾 Archivo principal actualizado: {main_filename}")
                            
                            # Ejecutar estado.py para subir los datos a Supabase
                            print("\n🔄 Iniciando subida de datos a Supabase...")
                            try:
                                # Obtener la ruta absoluta del directorio del script
                                script_dir = os.path.dirname(os.path.abspath(__file__))
                                # Obtener la ruta absoluta de estado.py
                                estado_script = os.path.join(script_dir, "estado.py")
                                
                                # Verificar que el archivo existe
                                if not os.path.exists(estado_script):
                                    print(f"❌ Error: No se encontró el archivo estado.py en: {estado_script}")
                                else:
                                    print(f"🔄 Ejecutando estado.py desde: {estado_script}")
                                    
                                    # Cambiar al directorio del script antes de ejecutar estado.py
                                    original_dir = os.getcwd()
                                    os.chdir(script_dir)
                                    
                                    # Ejecutar estado.py
                                    subprocess.run([sys.executable, estado_script], check=True)
                                    print("✅ Datos subidos a Supabase exitosamente.")
                                    
                                    # Volver al directorio original
                                    os.chdir(original_dir)
                            except subprocess.CalledProcessError as e:
                                print(f"❌ Error al ejecutar estado.py: {e}")
                            except Exception as e:
                                print(f"❌ Error inesperado al subir datos a Supabase: {e}")
                            finally:
                                # Asegurarse de volver al directorio original incluso si hay errores
                                try:
                                    os.chdir(original_dir)
                                except:
                                    pass
                            
                        else:
                            print("ℹ️  No se encontraron transferencias en esta iteración")
                            
                    except Exception as e:
                        print(f"⚠️  Error al extraer datos: {e}")
                        
                except Exception as e:
                    print(f"⚠️  Error en procesamiento de transferencias: {e}")
                    print("🔄 Continuando con la siguiente iteración...")
                    # No cerrar el navegador, solo continuar con la siguiente iteración
                
                # Incrementar contador de iteración
                iteration_count += 1
                
                # Esperar el intervalo antes de la siguiente iteración
                print(f"⏳ Esperando {wait_interval} segundos antes de la siguiente actualización...")
                await asyncio.sleep(wait_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Interrupción manual detectada. Cerrando sesión...")
                break
            except Exception as e:
                print(f"❌ Error en iteración #{iteration_count}: {e}")
                print("🔄 Continuando con la siguiente iteración en 30 segundos...")
                await asyncio.sleep(30)
                iteration_count += 1
        
        # Solo cerrar si salimos del bucle
        print("🔚 Finalizando sesión continua...")
        try:
            await browser.close()
        except Exception as e:
            print(f"Error al cerrar navegador: {e}")
            
        return account_transfers

    except Exception as e:
        print(f"Error al procesar la cuenta {account['rutEmpresa']}: {e}")
        return account_transfers

    finally:
        # Limpiar recursos del navegador
        await cleanup_browser_resources(browser, context_browser, page)

    return account_transfers


# --------------------------
# Función Principal
# --------------------------

async def main():
    # Lista de cuentas a procesar - TODAS LAS EMPRESAS
    accounts = [
        {"rutEmpresa": "774691731", "rutPersona": "156089753", "password": "Kj6mm866"},
        {"rutEmpresa": "777734482", "rutPersona": "156089753", "password": "Kj6mm866"},
        {"rutEmpresa": "77936187K", "rutPersona": "171091349", "password": "Kj6mm866"}
    ]
    
    print("✅ MODO COMPLETO: Procesando TODAS las empresas")
    print("A punto de lanzar Playwright")
    async with async_playwright() as p:
        print("Playwright iniciado correctamente")
        # Procesar solo una cuenta para pruebas
        results = await asyncio.gather(*[process_account(account, p) for account in accounts])

    # Combinar todas las transferencias para el archivo combinado
    aggregated_transfers = []
    for account_transfers in results:
        aggregated_transfers.extend(account_transfers)
    
    # Guardar todas las transferencias en un archivo Excel combinado
    if aggregated_transfers:
        export_to_excel(aggregated_transfers, "transferencias_combinadas.xlsx")
        print(f"Archivo Excel 'transferencias_combinadas.xlsx' guardado exitosamente con {len(aggregated_transfers)} transferencias en total.")
        
        # Ejecutar estado.py para subir los datos a Supabase
        print("\nIniciando subida de datos a Supabase...")
        try:
            # Obtener la ruta absoluta del directorio del script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Obtener la ruta absoluta de estado.py
            estado_script = os.path.join(script_dir, "estado.py")
            
            # Verificar que el archivo existe
            if not os.path.exists(estado_script):
                print(f"Error: No se encontró el archivo estado.py en: {estado_script}")
                return
                
            print(f"Ejecutando estado.py desde: {estado_script}")
            
            # Cambiar al directorio del script antes de ejecutar estado.py
            original_dir = os.getcwd()
            os.chdir(script_dir)
            
            # Ejecutar estado.py
            subprocess.run([sys.executable, estado_script], check=True)
            print("Proceso completado exitosamente.")
            
            # Volver al directorio original
            os.chdir(original_dir)
            
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar estado.py: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        finally:
            # Asegurarse de volver al directorio original incluso si hay errores
            try:
                os.chdir(original_dir)
            except:
                pass


# --------------------------
# Ejecución con Scheduling
# --------------------------

if __name__ == "__main__":
    # Asegurarse de que el directorio de trabajo sea el correcto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    while True:
        asyncio.run(main())
        sleep_interval = 5 * 60  # 5 minutos todo el día
        print(f"Esperando 5 minutos para la siguiente ejecución...")
        time.sleep(sleep_interval)