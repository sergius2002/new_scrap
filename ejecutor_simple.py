#!/usr/bin/env python3
"""
Scripts individuales para ejecutar cada scraper por separado
===========================================================

Este archivo contiene funciones simples para ejecutar cada scraper.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_bci():
    """Ejecuta el scraper de BCI"""
    current_dir = Path(__file__).parent.absolute()
    script_path = current_dir / "Scrap_bci.py"
    
    print("🏦 Iniciando Scraper BCI...")
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=str(current_dir), 
                              check=True)
        print("✅ Scraper BCI completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando Scraper BCI: {e}")
        return False

def run_estado():
    """Ejecuta el scraper de Banco Estado"""
    current_dir = Path(__file__).parent.absolute()
    script_path = current_dir / "Scrap_estado.py"
    
    print("🏛️ Iniciando Scraper Banco Estado...")
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=str(current_dir), 
                              check=True)
        print("✅ Scraper Banco Estado completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando Scraper Banco Estado: {e}")
        return False

def run_santander():
    """Ejecuta el scraper de Santander"""
    current_dir = Path(__file__).parent.absolute()
    script_path = current_dir / "Scrap_santander.py"
    
    print("🏪 Iniciando Scraper Santander...")
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=str(current_dir), 
                              check=True)
        print("✅ Scraper Santander completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando Scraper Santander: {e}")
        return False

def run_lioren():
    """Ejecuta el facturador Lioren"""
    current_dir = Path(__file__).parent.absolute()
    script_path = current_dir / "Facturador_lioren.py"
    
    print("📄 Iniciando Facturador Lioren...")
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=str(current_dir), 
                              check=True)
        print("✅ Facturador Lioren completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando Facturador Lioren: {e}")
        return False

def run_all_scrapers():
    """Ejecuta todos los scrapers (sin Lioren)"""
    print("🚀 Ejecutando todos los scrapers...")
    
    results = []
    results.append(("BCI", run_bci()))
    results.append(("Estado", run_estado()))
    results.append(("Santander", run_santander()))
    
    print("\n📊 Resumen de ejecución:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    return all(result[1] for result in results)

def run_everything():
    """Ejecuta todos los scrapers y Lioren"""
    print("🌟 Ejecutando todo (scrapers + Lioren)...")
    
    results = []
    results.append(("BCI", run_bci()))
    results.append(("Estado", run_estado()))
    results.append(("Santander", run_santander()))
    results.append(("Lioren", run_lioren()))
    
    print("\n📊 Resumen de ejecución:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    return all(result[1] for result in results)

if __name__ == "__main__":
    print("🤖 Ejecutor Simple de Scrapers")
    print("="*40)
    print("Funciones disponibles:")
    print("  run_bci() - Ejecutar scraper BCI")
    print("  run_estado() - Ejecutar scraper Estado")
    print("  run_santander() - Ejecutar scraper Santander")
    print("  run_lioren() - Ejecutar facturador Lioren")
    print("  run_all_scrapers() - Ejecutar todos los scrapers")
    print("  run_everything() - Ejecutar todo")
    print("\nEjemplo de uso:")
    print("  python -c \"from ejecutor_simple import run_bci; run_bci()\"")