#!/usr/bin/env python3
"""
Script para probar detección de bots en bot.sannysoft.com
"""

import asyncio
import random
import os
import sys
from playwright.async_api import async_playwright
import uuid

# Importar la clase BrowserProfile del scraper principal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Scrap_bci import BrowserProfile

async def test_bot_detection():
    """Prueba la detección de bots en bot.sannysoft.com"""
    
    print("🤖 Iniciando prueba de detección de bots...")
    print("📅 Fecha y hora de inicio:", asyncio.get_event_loop().time())
    
    browser_profile = BrowserProfile()
    
    async with async_playwright() as p:
        try:
            # Configurar navegador con el mismo perfil que usamos para BCI
            browser, context = await browser_profile.setup_context(p)
            page = await context.new_page()
            
            print("🌐 Navegando a bot.sannysoft.com...")
            await page.goto("https://bot.sannysoft.com/", timeout=30000)
            
            # Esperar a que cargue completamente
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            print("📊 Analizando resultados de detección...")
            
            # Obtener todos los resultados de las pruebas
            results = await page.evaluate("""
                () => {
                    const results = {};
                    const rows = document.querySelectorAll('tr');
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            const testName = cells[0].textContent.trim();
                            const result = cells[1].textContent.trim();
                            if (testName && result) {
                                results[testName] = result;
                            }
                        }
                    });
                    
                    return results;
                }
            """)
            
            print("\n" + "="*60)
            print("🔍 RESULTADOS DE DETECCIÓN DE BOTS")
            print("="*60)
            
            # Mostrar resultados organizados
            failed_tests = []
            passed_tests = []
            
            for test_name, result in results.items():
                if "failed" in result.lower() or "present" in result.lower():
                    failed_tests.append((test_name, result))
                    print(f"❌ {test_name}: {result}")
                else:
                    passed_tests.append((test_name, result))
                    print(f"✅ {test_name}: {result}")
            
            print("\n" + "="*60)
            print(f"📈 RESUMEN:")
            print(f"✅ Pruebas pasadas: {len(passed_tests)}")
            print(f"❌ Pruebas fallidas: {len(failed_tests)}")
            print(f"📊 Total: {len(results)}")
            
            if failed_tests:
                print(f"\n🚨 PRUEBAS FALLIDAS CRÍTICAS:")
                for test_name, result in failed_tests:
                    print(f"   • {test_name}: {result}")
            
            # Tomar screenshot para análisis
            screenshot_path = "bot_detection_test.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n📸 Screenshot guardado como: {screenshot_path}")
            
            # Esperar un poco para que puedas ver los resultados
            print("\n⏳ Esperando 10 segundos para revisar resultados...")
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ Error durante la prueba: {str(e)}")
        finally:
            try:
                await browser.close()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(test_bot_detection()) 