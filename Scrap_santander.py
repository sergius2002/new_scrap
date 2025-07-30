################################################################################
# proyecto_completo_minimizado.py
################################################################################

import asyncio  # Para manejar la asincronía
import os       # Para manejar rutas y directorios
import time     # Para time.sleep(300) en un while True
import datetime
import subprocess  # Para ejecutar Santander.py
import random   # Para generar períodos aleatorios
from playwright.async_api import async_playwright, Page, Frame
from dotenv import load_dotenv
from saldo_bancos_db import SaldoBancosDB
import openpyxl

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración de conexión a Supabase y otras variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")
SHEET_URL = os.getenv("SHEET_URL")
CARPETA_ARCHIVOS = os.getenv("CARPETA_ARCHIVOS")
PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR")
TOKEN_PATH = os.getenv("TOKEN_PATH")
API_TOKEN_SAN_CRISTOBAL = os.getenv("API_TOKEN_SAN_CRISTOBAL")
API_TOKEN_ST_CRISTOBAL = os.getenv("API_TOKEN_ST_CRISTOBAL")

# Verificar que CARPETA_ARCHIVOS esté definida
if not CARPETA_ARCHIVOS:
    raise EnvironmentError("La variable de entorno 'CARPETA_ARCHIVOS' no está definida.")

print(f"CARPETA_ARCHIVOS: {CARPETA_ARCHIVOS}")

################################################################################
# Función para leer saldos de archivos Excel de Santander
################################################################################
def leer_saldos_santander(ruta_directorio):
    """
    Lee los saldos de las dos cuentas corrientes de Santander desde los archivos Excel.
    Los saldos están en la celda D13 de cada archivo.
    
    Returns:
        dict: Diccionario con los saldos de cada cuenta
    """
    saldos = {}
    
    # Configuración de archivos y cuentas con nombres descriptivos
    archivos_cuentas = {
        "000091404630.xlsx": "santander_630",
        "000091903610.xlsx": "santander_610"
    }
    
    for archivo, nombre_cuenta in archivos_cuentas.items():
        ruta_archivo = os.path.join(ruta_directorio, archivo)
        
        try:
            if os.path.exists(ruta_archivo):
                # Abrir el archivo Excel
                workbook = openpyxl.load_workbook(ruta_archivo)
                sheet = workbook.active
                
                # Leer el saldo de la celda D13
                saldo_celda = sheet['D13'].value
                
                if saldo_celda is not None:
                    # Convertir a string y limpiar el valor
                    saldo_str = str(saldo_celda).replace('$', '').replace(',', '').replace('.', '').strip()
                    
                    # Convertir a entero (los saldos están en pesos chilenos sin decimales)
                    try:
                        saldo = int(saldo_str)
                        saldos[nombre_cuenta] = saldo
                        print(f"✅ Saldo leído para cuenta {nombre_cuenta}: ${saldo:,}")
                    except ValueError:
                        print(f"❌ Error al convertir saldo para cuenta {nombre_cuenta}: {saldo_str}")
                        saldos[nombre_cuenta] = None
                else:
                    print(f"❌ Celda D13 vacía en archivo {archivo}")
                    saldos[nombre_cuenta] = None
                
                workbook.close()
            else:
                print(f"❌ Archivo no encontrado: {ruta_archivo}")
                saldos[nombre_cuenta] = None
                
        except Exception as e:
            print(f"❌ Error al leer archivo {archivo}: {e}")
            saldos[nombre_cuenta] = None
    
    return saldos

################################################################################
# Función principal asíncrona
################################################################################
async def run_flow_once():
    """
    Un ciclo completo de:
      1) Abrir el navegador y navegar a la URL de login.
      2) Clic en "Ingresar".
      3) Llenar RUT y clave, y clic en "Aceptar".
      4) Seleccionar empresa.
      5) Clic en "Cuentas Corrientes" -> "Saldos y movimientos".
      6) Descargar primer y segundo Excel con nombres fijos.
      7) Finalizar el flujo sin pausar.
    """
    ############################################################################
    # Variables de configuración
    ############################################################################
    # Obtener el directorio actual del script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Carpeta donde se guardarán los archivos (usando CARPETA_ARCHIVOS)
    ruta_directorio = os.path.join(current_dir, CARPETA_ARCHIVOS)

    # Verificar que la ruta_directorio exista, si no, crearla
    if not os.path.exists(ruta_directorio):
        os.makedirs(ruta_directorio)
        print(f"Directorio creado: {ruta_directorio}")

    # Nombres fijos para cada Excel
    nombre_excel_1 = "000091404630.xlsx"
    nombre_excel_2 = "000091903610.xlsx"

    ############################################################################
    # Iniciar Playwright con Chrome (como scrap_santander_cla)
    ############################################################################
    async with async_playwright() as p:
        # Se usa Chrome y se inicia la ventana minimizada
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-minimized"]
        )

        # Crear un nuevo contexto con un User-Agent real
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        # Inyectar script de stealth para modificar propiedades de navigator
        await context.add_init_script("""
            // Eliminar la propiedad webdriver para evitar la detección de automatización
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Simular plugins instalados
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            // Simular idiomas del navegador
            Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es'] });
        """)

        page = await context.new_page()

        ########################################################################
        # Navegar a la página de login y esperar
        ########################################################################
        await page.goto("https://empresas.officebanking.cl")
        await page.wait_for_timeout(5000)

        ########################################################################
        # Clic en "Ingresar" usando force click
        ########################################################################
        try:
            await page.wait_for_selector("app-login-button:has-text('Ingresar')", timeout=10000)
            await page.wait_for_timeout(1000)
            await page.locator("app-login-button:has-text('Ingresar')").click(force=True)
            print("Clic en 'Ingresar' realizado.")
        except Exception as e:
            print(f"Error haciendo clic en 'Ingresar': {e}")
            await page.screenshot(path="error_ingresar.png")
            await browser.close()
            return

        await page.wait_for_timeout(5000)

        ########################################################################
        # Identificar si el login está en un iframe
        ########################################################################
        frame = None
        for f in page.frames:
            try:
                if await f.query_selector("#userInput"):
                    frame = f
                    print(f"Iframe encontrado para login: {f.name}, URL: {f.url}")
                    break
            except Exception:
                continue

        if not frame:
            frame = page
            print("No se encontró un iframe para login. Usando la página principal.")

        ########################################################################
        # Llenar RUT y clave
        ########################################################################
        try:
            await frame.wait_for_selector("#userInput", timeout=10000)
            await frame.fill("#userInput", "15608975-3")
            print("RUT llenado correctamente.")
        except Exception as e:
            print(f"Error llenando RUT: {e}")

        try:
            await frame.wait_for_selector("#userCodeInput", timeout=5000)
            await frame.fill("#userCodeInput", "Kj6m8.-")
            print("Clave llenada correctamente.")
        except Exception as e:
            print(f"Error llenando clave: {e}")

        ########################################################################
        # Clic en "Aceptar" usando force click
        ########################################################################
        try:
            await frame.wait_for_selector("span:has-text('Aceptar')", timeout=5000)
            await frame.locator("span:has-text('Aceptar')").click(force=True)
            print("Clic en 'Aceptar' realizado.")
        except Exception as e:
            print(f"Error haciendo clic en 'Aceptar': {e}")

        await page.wait_for_timeout(5000)

        ########################################################################
        # Seleccionar empresa
        ########################################################################
        try:
            await page.wait_for_selector("xpath=(//span[contains(.,'Entrar')])[2]", timeout=5000)
            await page.click("xpath=(//span[contains(.,'Entrar')])[2]")
            print("Empresa seleccionada correctamente.")
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Error seleccionando la empresa: {e}")

        ########################################################################
        # Clic en "Cuentas Corrientes"
        ########################################################################
        try:
            await page.wait_for_selector("xpath=(//span[contains(.,'Cuentas Corrientes')])[1]", timeout=5000)
            await page.click("xpath=(//span[contains(.,'Cuentas Corrientes')])[1]")
            print("Clic en 'Cuentas Corrientes' realizado correctamente.")
        except Exception as e:
            print(f"Error haciendo clic en 'Cuentas Corrientes': {e}")

        await page.wait_for_timeout(3000)

        ########################################################################
        # Clic en "Saldos y movimientos"
        ########################################################################
        try:
            await page.wait_for_selector(
                "xpath=(//a[@class='obLink'][contains(.,'Saldos y movimientos')])[2]",
                timeout=5000
            )
            await page.click("xpath=(//a[@class='obLink'][contains(.,'Saldos y movimientos')])[2]")
            print("Clic en 'Saldos y movimientos' realizado correctamente.")
        except Exception as e:
            print(f"Error haciendo clic en 'Saldos y movimientos': {e}")

        await page.wait_for_timeout(3000)

        ########################################################################
        # Acceder al iframe 'derecho' y realizar scroll final
        ########################################################################
        try:
            print("\n>>> Accediendo al iframe 'derecho'...")
            iframe_handle = page.frame(name="derecho")

            if not iframe_handle:
                print("No se encontró el iframe 'derecho'.")
                await browser.close()
                return

            print("Iframe 'derecho' encontrado.")
            await iframe_handle.wait_for_load_state("load")
            print("Contenido del iframe 'derecho' cargado.")

            print("Iniciando scroll hasta el final de la página dentro del iframe 'derecho'...")
            await iframe_handle.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        const distance = 100;
                        const delay = 100;
                        const timer = setInterval(() => {
                            const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
                            window.scrollBy(0, distance);
                            if (scrollTop + clientHeight >= scrollHeight) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, delay);
                    });
                }
            """)
            print("Scroll hasta el final dentro del iframe completado.")
            await iframe_handle.wait_for_timeout(2000)

        except Exception as e:
            print(f"Error accediendo al iframe 'derecho': {e}")
            await browser.close()
            return

        ########################################################################
        # Descargar PRIMER Excel con nombre fijo
        ########################################################################
        try:
            print("\n>>> Interactuando con el iframe 'derecho' para descargar el PRIMER Excel...")
            if not iframe_handle:
                print("Iframe 'derecho' no está disponible.")
                raise Exception("Iframe 'derecho' no encontrado.")

            descargar_xpath = "//section[@id='3']//a[@class='wrapper-descarga-link'][normalize-space()='Descargar']"

            # Hacer hover sobre el botón "Descargar"
            await iframe_handle.hover(descargar_xpath)
            print(f"Hover realizado sobre 'Descargar' usando el XPath: {descargar_xpath}")
            await iframe_handle.wait_for_timeout(1500)

            # Apuntar al enlace "Excel"
            excel_xpath = "(//a[contains(.,'Excel')])[2]"
            await iframe_handle.wait_for_selector(excel_xpath, state="visible", timeout=15000)
            print(f"Enlace 'Excel' visible usando el XPath: {excel_xpath}")

            # Desplazar a la vista y forzar clic para la descarga
            await iframe_handle.locator(excel_xpath).scroll_into_view_if_needed()
            async with page.expect_download() as download_info:
                await iframe_handle.click(excel_xpath, force=True)
            download = await download_info.value

            # Guardar primer archivo con nombre fijo
            ruta_descarga_excel_1 = os.path.join(ruta_directorio, nombre_excel_1)
            await download.save_as(ruta_descarga_excel_1)
            print(f"Descarga del primer Excel completada y guardada en: {ruta_descarga_excel_1}")

            # Verificar tamaño y fecha de modificación del archivo descargado
            file_stat = os.stat(ruta_descarga_excel_1)
            mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            print(f"Archivo {nombre_excel_1} -> Modificado: {mod_time}, Tamaño: {file_stat.st_size} bytes")

        except Exception as e:
            print(f"Error al descargar el primer Excel: {e}")

        ########################################################################
        # Desplazarse al inicio y seleccionar la nueva cuenta
        ########################################################################
        try:
            print("\n>>> Desplazándose al inicio dentro del iframe 'derecho'...")
            await iframe_handle.evaluate("window.scrollTo(0, 0)")
            print("Desplazamiento al inicio completado.")
            await iframe_handle.wait_for_timeout(1000)

            dropdown_button_xpath = "//button[@data-id='cboCuentas']"
            await iframe_handle.wait_for_selector(f"xpath={dropdown_button_xpath}", timeout=5000)
            await iframe_handle.click(f"xpath={dropdown_button_xpath}")
            print("Clic en el dropdown realizado correctamente.")
            await iframe_handle.wait_for_timeout(1000)

            nueva_cuenta_xpath = "//a[span[@class='text' and text()='0-000-9190361-0']]"
            await iframe_handle.wait_for_selector(f"xpath={nueva_cuenta_xpath}", timeout=5000)
            await iframe_handle.click(f"xpath={nueva_cuenta_xpath}")
            print("Nueva cuenta seleccionada correctamente.")
            await iframe_handle.wait_for_timeout(3000)

        except Exception as e:
            print(f"Error al seleccionar la nueva cuenta corriente: {e}")

        ########################################################################
        # Descargar SEGUNDO Excel con nombre fijo
        ########################################################################
        try:
            print("\n>>> Descargando el SEGUNDO Excel de la nueva cuenta...")
            if not iframe_handle:
                print("Iframe 'derecho' no está disponible.")
                raise Exception("Iframe 'derecho' no encontrado.")

            print("Desplazándose hasta el final dentro del iframe 'derecho'...")
            await iframe_handle.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        const distance = 100;
                        const delay = 100;
                        const timer = setInterval(() => {
                            const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
                            window.scrollBy(0, distance);
                            if (scrollTop + clientHeight >= scrollHeight) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, delay);
                    });
                }
            """)
            print("Scroll al final completado.")
            await iframe_handle.wait_for_timeout(2000)

            descargar_button_xpath_2 = "//section[@id='3']//a[@class='wrapper-descarga-link'][normalize-space()='Descargar']"
            await iframe_handle.wait_for_selector(f"xpath={descargar_button_xpath_2}", timeout=5000)
            await iframe_handle.hover(f"xpath={descargar_button_xpath_2}")
            print("Hover realizado sobre el botón 'Descargar' nuevamente.")
            await iframe_handle.wait_for_timeout(1500)

            excel_option_xpath_2 = "(//a[contains(.,'Excel')])[2]"
            print(">>> Esperando descarga del SEGUNDO Excel...")
            async with page.expect_download() as download_info:
                await iframe_handle.click(excel_option_xpath_2, force=True)
            download_2 = await download_info.value
            print(">>> Descarga del segundo Excel detectada.")

            ruta_descarga_excel_2 = os.path.join(ruta_directorio, nombre_excel_2)
            await download_2.save_as(ruta_descarga_excel_2)
            print(f"Descarga del segundo Excel completada y guardada en: {ruta_descarga_excel_2}")

            # Verificar tamaño y fecha de modificación del segundo archivo
            file_stat2 = os.stat(ruta_descarga_excel_2)
            mod_time2 = datetime.datetime.fromtimestamp(file_stat2.st_mtime)
            print(f"Archivo {nombre_excel_2} -> Modificado: {mod_time2}, Tamaño: {file_stat2.st_size} bytes")

        except Exception as e:
            print(f"Error al descargar el segundo Excel: {e}")

        ########################################################################
        # Ciclo continuo de descarga y procesamiento
        ########################################################################
        ciclo_numero = 1
        errores_consecutivos = 0
        max_errores_consecutivos = 3  # Permitir hasta 3 errores consecutivos antes de cerrar
        
        while True:
            try:
                print(f"\n🔄 === CICLO {ciclo_numero} - PROCESANDO ARCHIVOS EXCEL ===")
                
                # Procesar saldos y guardar en base de datos
                try:
                    print("\n>>> Procesando saldos de Santander y guardando en base de datos...")
                    
                    # Inicializar conexión a base de datos
                    db = SaldoBancosDB()
                    
                    # Leer saldos de los archivos Excel descargados
                    saldos = leer_saldos_santander(ruta_directorio)
                    
                    # Procesar cada cuenta como si fuera un banco independiente
                    for nombre_cuenta, saldo_actual in saldos.items():
                        if saldo_actual is not None:
                            try:
                                # Obtener saldo anterior de la base de datos (usando el nombre de cuenta como banco)
                                ultimo_registro = db.obtener_ultimo_saldo(nombre_cuenta)
                                
                                if ultimo_registro is None:
                                    print(f"📝 Primera vez registrando {nombre_cuenta}")
                                    # Guardar saldo inicial
                                    if db.guardar_saldo(nombre_cuenta, saldo_actual):
                                        print(f"✅ Saldo inicial guardado para {nombre_cuenta}: ${saldo_actual:,}")
                                    else:
                                        print(f"❌ Error al guardar saldo inicial para {nombre_cuenta}")
                                else:
                                    # Obtener el saldo anterior del registro
                                    saldo_anterior = ultimo_registro['saldo']
                                    
                                    # Comparar saldos
                                    if saldo_actual != saldo_anterior:
                                        diferencia = saldo_actual - saldo_anterior
                                        print(f"💰 Cambio detectado en {nombre_cuenta}:")
                                        print(f"   Saldo anterior: ${saldo_anterior:,}")
                                        print(f"   Saldo actual: ${saldo_actual:,}")
                                        print(f"   Diferencia: ${diferencia:+,}")
                                        
                                        # Guardar nuevo saldo
                                        if db.guardar_saldo(nombre_cuenta, saldo_actual):
                                            print(f"✅ Nuevo saldo guardado en base de datos")
                                        else:
                                            print(f"❌ Error al guardar nuevo saldo en base de datos")
                                    else:
                                        print(f"📊 Sin cambios en {nombre_cuenta}: ${saldo_actual:,}")
                            
                            except Exception as e:
                                print(f"❌ Error procesando cuenta {nombre_cuenta}: {e}")
                        else:
                            print(f"⚠️ Saldo no disponible para cuenta {nombre_cuenta}")
                    
                    # Mostrar resumen para cada cuenta
                    for nombre_cuenta in saldos.keys():
                        db.mostrar_resumen_banco(nombre_cuenta)
                    
                except Exception as e:
                    print(f"❌ Error en procesamiento de base de datos: {e}")

                # Ejecutar Santander.py después de cada procesamiento exitoso
                try:
                    print("\n>>> Ejecutando Santander.py...")
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    santander_script = os.path.join(script_dir, "Santander.py")
                    print(f"📁 Ejecutando Santander.py desde: {santander_script}")
                    subprocess.run(["python3", santander_script])
                except Exception as e:
                    print(f"❌ Error ejecutando Santander.py: {e}")

                # Generar tiempo de espera aleatorio entre 5-30 segundos
                tiempo_espera_segundos = random.randint(5, 30)
                tiempo_espera_ms = tiempo_espera_segundos * 1000
                print(f"\n✅ Ciclo {ciclo_numero} completado exitosamente. Esperando {tiempo_espera_segundos} segundos para el próximo ciclo...")
                
                # Resetear contador de errores después de un ciclo exitoso
                errores_consecutivos = 0
                
                await page.wait_for_timeout(tiempo_espera_ms)
                
                # Verificar si el navegador sigue abierto
                try:
                    await page.title()
                except Exception as e:
                    print(f"❌ El navegador se cerró inesperadamente: {e}")
                    break
                
                # Refrescar la página para obtener nuevos datos
                print(f"\n🔄 Refrescando página para ciclo {ciclo_numero + 1}...")
                try:
                    # Simplemente refrescar la página actual en lugar de navegar a la principal
                    await page.reload()
                    await page.wait_for_timeout(3000)
                    
                    # Verificar si necesitamos hacer login nuevamente de forma más tolerante
                    session_active = True
                    try:
                        # Buscar elementos que indiquen que estamos logueados
                        # Intentar encontrar el menú de cuentas corrientes
                        await page.wait_for_selector("xpath=(//span[contains(.,'Cuentas Corrientes')])[1]", timeout=10000)
                        print("✅ Sesión activa detectada. Navegando a saldos y movimientos...")
                    except:
                        # Si no encontramos el menú, verificar si hay botón de login
                        try:
                            await page.wait_for_selector("app-login-button:has-text('Ingresar')", timeout=3000)
                            print("⚠️ Sesión cerrada detectada. Necesario hacer login nuevamente.")
                            session_active = False
                        except:
                            # Si tampoco encontramos el botón de login, asumir que la sesión está activa
                            # pero puede haber un problema temporal
                            print("⚠️ Estado de sesión incierto. Intentando navegar...")
                            try:
                                # Intentar navegar directamente a la URL de saldos
                                await page.goto("https://empresas.officebanking.cl")
                                await page.wait_for_timeout(5000)
                                await page.wait_for_selector("xpath=(//span[contains(.,'Cuentas Corrientes')])[1]", timeout=10000)
                                print("✅ Navegación exitosa. Sesión activa.")
                            except:
                                print("❌ No se pudo determinar el estado de la sesión. Cerrando.")
                                session_active = False
                    
                    if not session_active:
                        errores_consecutivos += 1
                        print(f"⚠️ Error de sesión {errores_consecutivos}/{max_errores_consecutivos}")
                        if errores_consecutivos >= max_errores_consecutivos:
                            print("❌ Demasiados errores de sesión consecutivos. Cerrando script.")
                            break
                        else:
                            print("🔄 Continuando con el siguiente ciclo...")
                            ciclo_numero += 1
                            continue
                    else:
                        # Resetear contador de errores si la sesión está activa
                        errores_consecutivos = 0
                        
                    # Navegar a saldos y movimientos
                    try:
                        await page.click("xpath=(//span[contains(.,'Cuentas Corrientes')])[1]")
                        await page.wait_for_timeout(3000)
                        
                        await page.wait_for_selector("xpath=(//a[@class='obLink'][contains(.,'Saldos y movimientos')])[2]", timeout=10000)
                        await page.click("xpath=(//a[@class='obLink'][contains(.,'Saldos y movimientos')])[2]")
                        await page.wait_for_timeout(3000)
                        
                        print("✅ Navegación a saldos y movimientos completada.")
                    except Exception as nav_error:
                        print(f"⚠️ Error navegando a saldos y movimientos: {nav_error}")
                        print("🔄 Intentando continuar con el siguiente ciclo...")
                        # No romper el ciclo, solo continuar
                    
                except Exception as refresh_error:
                    print(f"❌ Error refrescando página: {refresh_error}")
                    print("🔄 Intentando continuar con el siguiente ciclo...")
                    # No romper el ciclo inmediatamente, dar otra oportunidad
                
                ciclo_numero += 1
                
            except KeyboardInterrupt:
                print("\n⚠️ Interrupción por teclado detectada. Cerrando navegador...")
                break
            except Exception as e:
                errores_consecutivos += 1
                print(f"❌ Error en ciclo {ciclo_numero}: {e}")
                print(f"⚠️ Error general {errores_consecutivos}/{max_errores_consecutivos}")
                
                if errores_consecutivos >= max_errores_consecutivos:
                    print("❌ Demasiados errores consecutivos. Cerrando script.")
                    break
                else:
                    print("🔄 Intentando continuar con el siguiente ciclo...")
                    ciclo_numero += 1
                    await page.wait_for_timeout(30000)  # Esperar 30 segundos antes de reintentar
        
        ########################################################################
        # Terminar el flujo
        ########################################################################
        print("\n>>> Finalizando flujo. Cerrando el navegador.")
        await browser.close()

################################################################################
# Ejecutar el flujo continuo
################################################################################
def run_continuous_flow():
    """
    Ejecuta el flujo continuo de Santander manteniendo el navegador abierto.
    El ciclo se ejecuta en períodos aleatorios de 5-30 segundos hasta que se cierre la sesión o el navegador.
    """
    try:
        asyncio.run(run_flow_once())
    except KeyboardInterrupt:
        print("\n⚠️ Script interrumpido por el usuario.")
    except Exception as e:
        print(f"❌ Error en la ejecución del flujo continuo: {e}")

################################################################################
# Punto de entrada
################################################################################
if __name__ == "__main__":
    run_continuous_flow()
