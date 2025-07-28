#!/usr/bin/env python3
"""
Sistema de rotación de proxies para evitar bloqueos de IP
"""

import asyncio
import aiohttp
import random
import time
from typing import List, Dict, Optional
import logging

class ProxyRotator:
    def __init__(self):
        self.proxies = []
        self.current_proxy = None
        self.last_rotation = 0
        self.rotation_interval = 300  # 5 minutos
        self.max_failures = 3
        
    async def fetch_free_proxies(self) -> List[Dict]:
        """Obtiene lista de proxies gratuitos"""
        proxy_sources = [
            "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        ]
        
        all_proxies = []
        
        for source in proxy_sources:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(source, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            proxies = self.parse_proxy_list(content)
                            all_proxies.extend(proxies)
                            print(f"✅ Obtenidos {len(proxies)} proxies de {source}")
            except Exception as e:
                print(f"⚠️ Error obteniendo proxies de {source}: {e}")
        
        return all_proxies
    
    def parse_proxy_list(self, content: str) -> List[Dict]:
        """Parsea la lista de proxies"""
        proxies = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                try:
                    host, port = line.split(':')
                    proxies.append({
                        'host': host.strip(),
                        'port': int(port.strip()),
                        'protocol': 'http',
                        'failures': 0,
                        'last_used': 0
                    })
                except:
                    continue
        
        return proxies
    
    async def test_proxy(self, proxy: Dict) -> bool:
        """Prueba si un proxy funciona"""
        try:
            proxy_url = f"http://{proxy['host']}:{proxy['port']}"
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    'https://httpbin.org/ip',
                    proxy=proxy_url
                ) as response:
                    if response.status == 200:
                        return True
        except:
            pass
        return False
    
    async def get_working_proxies(self, max_proxies: int = 10) -> List[Dict]:
        """Obtiene solo proxies que funcionan"""
        print("🔍 Obteniendo lista de proxies...")
        all_proxies = await self.fetch_free_proxies()
        
        if not all_proxies:
            print("❌ No se pudieron obtener proxies")
            return []
        
        print(f"🧪 Probando {min(len(all_proxies), 20)} proxies...")
        working_proxies = []
        
        # Probar solo los primeros 20 para no tardar mucho
        test_proxies = all_proxies[:20]
        
        tasks = [self.test_proxy(proxy) for proxy in test_proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if result is True:
                working_proxies.append(test_proxies[i])
                print(f"✅ Proxy funcionando: {test_proxies[i]['host']}:{test_proxies[i]['port']}")
                
                if len(working_proxies) >= max_proxies:
                    break
        
        print(f"🎯 Proxies funcionando: {len(working_proxies)}")
        return working_proxies
    
    def get_next_proxy(self) -> Optional[Dict]:
        """Obtiene el siguiente proxy para usar"""
        current_time = time.time()
        
        # Rotar cada 5 minutos o si no hay proxy actual
        if (self.current_proxy is None or 
            current_time - self.last_rotation > self.rotation_interval):
            
            if self.proxies:
                # Filtrar proxies que han fallado mucho
                available_proxies = [p for p in self.proxies if p['failures'] < self.max_failures]
                
                if available_proxies:
                    self.current_proxy = random.choice(available_proxies)
                    self.last_rotation = current_time
                    print(f"🔄 Rotando a nuevo proxy: {self.current_proxy['host']}:{self.current_proxy['port']}")
                else:
                    print("⚠️ No hay proxies disponibles, usando conexión directa")
                    self.current_proxy = None
        
        return self.current_proxy
    
    def mark_proxy_failed(self, proxy: Dict):
        """Marca un proxy como fallido"""
        if proxy in self.proxies:
            proxy['failures'] += 1
            print(f"❌ Proxy falló: {proxy['host']}:{proxy['port']} (fallos: {proxy['failures']})")
            
            if proxy['failures'] >= self.max_failures:
                print(f"🚫 Proxy removido por muchos fallos: {proxy['host']}:{proxy['port']}")
    
    async def initialize(self):
        """Inicializa el rotador de proxies"""
        print("🚀 Inicializando rotador de proxies...")
        self.proxies = await self.get_working_proxies()
        
        if self.proxies:
            print(f"✅ Rotador inicializado con {len(self.proxies)} proxies")
        else:
            print("⚠️ No se pudieron obtener proxies, usando conexión directa")

# Instancia global
proxy_rotator = ProxyRotator()

async def get_proxy_for_playwright() -> Optional[str]:
    """Obtiene proxy formateado para Playwright"""
    proxy = proxy_rotator.get_next_proxy()
    if proxy:
        return f"http://{proxy['host']}:{proxy['port']}"
    return None

def mark_current_proxy_failed():
    """Marca el proxy actual como fallido"""
    if proxy_rotator.current_proxy:
        proxy_rotator.mark_proxy_failed(proxy_rotator.current_proxy)
        proxy_rotator.current_proxy = None  # Forzar rotación 