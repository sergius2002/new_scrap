"""
Módulo para manejar operaciones de base de datos relacionadas con saldos bancarios
"""

import os
import sys
from datetime import datetime, date
from decimal import Decimal

# Agregar el directorio src al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.supabase_client import SupabaseClient
from utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

class SaldoBancosDB:
    """Clase para manejar operaciones de la tabla saldo_bancos"""
    
    def __init__(self):
        """Inicializar cliente de Supabase"""
        self.supabase_client = SupabaseClient()
        
    def obtener_ultimo_saldo(self, banco):
        """
        Obtiene el último saldo registrado para un banco específico
        
        Args:
            banco (str): Nombre del banco (ej: 'BCI')
            
        Returns:
            dict: Último registro de saldo o None si no existe
        """
        try:
            # Usar el cliente Supabase directamente para consultas más complejas
            result = self.supabase_client.client.table("saldo_bancos")\
                .select("*")\
                .eq("banco", banco)\
                .order("fecha_captura", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"✅ Último saldo encontrado para {banco}: ${result.data[0]['saldo']}")
                return result.data[0]
            else:
                logger.info(f"ℹ️ No hay registros previos para {banco}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo último saldo para {banco}: {str(e)}")
            return None
    
    def verificar_saldo_hoy(self, banco):
        """
        Verifica si ya existe un registro de saldo para el banco en el día actual
        
        Args:
            banco (str): Nombre del banco
            
        Returns:
            bool: True si ya existe un registro hoy, False en caso contrario
        """
        try:
            fecha_hoy = date.today().isoformat()
            fecha_inicio = f"{fecha_hoy}T00:00:00"
            fecha_fin = f"{fecha_hoy}T23:59:59"
            
            # Consultar registros del día actual
            result = self.supabase_client.client.table("saldo_bancos")\
                .select("*")\
                .eq("banco", banco)\
                .gte("fecha_captura", fecha_inicio)\
                .lte("fecha_captura", fecha_fin)\
                .execute()
            
            existe_hoy = result.data and len(result.data) > 0
            
            if existe_hoy:
                logger.info(f"ℹ️ Ya existe un registro de {banco} para hoy: ${result.data[0]['saldo']}")
            else:
                logger.info(f"ℹ️ No hay registros de {banco} para hoy")
                
            return existe_hoy
            
        except Exception as e:
            logger.error(f"❌ Error verificando saldo de hoy para {banco}: {str(e)}")
            return False
    
    def guardar_saldo(self, banco, saldo, forzar=False):
        """
        Guarda un nuevo saldo en la base de datos solo si es diferente al último registrado
        o si se fuerza el guardado
        
        Args:
            banco (str): Nombre del banco
            saldo (float): Saldo a guardar
            forzar (bool): Si True, guarda sin verificar diferencias
            
        Returns:
            bool: True si se guardó exitosamente, False en caso contrario
        """
        try:
            # Convertir saldo a Decimal para mayor precisión
            saldo_decimal = Decimal(str(saldo))
            
            # Si no se fuerza, verificar si ya existe un registro hoy
            if not forzar and self.verificar_saldo_hoy(banco):
                logger.info(f"⏭️ Ya existe un registro de {banco} para hoy. No se guardará.")
                return False
            
            # Obtener último saldo para comparar
            ultimo_registro = self.obtener_ultimo_saldo(banco)
            
            if not forzar and ultimo_registro:
                ultimo_saldo = Decimal(str(ultimo_registro['saldo']))
                
                # Comparar saldos (considerar diferencias mínimas por redondeo)
                diferencia = abs(saldo_decimal - ultimo_saldo)
                
                if diferencia < Decimal('0.01'):  # Diferencia menor a 1 centavo
                    logger.info(f"⏭️ El saldo de {banco} no ha cambiado (${saldo_decimal}). No se guardará.")
                    return False
                else:
                    logger.info(f"💰 Saldo de {banco} cambió: ${ultimo_saldo} → ${saldo_decimal}")
            
            # Preparar datos para insertar
            data = {
                "banco": banco,
                "saldo": float(saldo_decimal),
                "fecha_captura": datetime.now().isoformat()
            }
            
            # Insertar en la base de datos
            result = self.supabase_client.insert_data("saldo_bancos", data)
            
            if result:
                logger.info(f"✅ Saldo de {banco} guardado exitosamente: ${saldo_decimal}")
                return True
            else:
                logger.error(f"❌ Error guardando saldo de {banco}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error guardando saldo de {banco}: {str(e)}")
            return False
    
    def obtener_historial_saldos(self, banco, limite=10):
        """
        Obtiene el historial de saldos para un banco
        
        Args:
            banco (str): Nombre del banco
            limite (int): Número máximo de registros a obtener
            
        Returns:
            list: Lista de registros de saldos ordenados por fecha (más reciente primero)
        """
        try:
            result = self.supabase_client.client.table("saldo_bancos")\
                .select("*")\
                .eq("banco", banco)\
                .order("fecha_captura", desc=True)\
                .limit(limite)\
                .execute()
            
            if result.data:
                logger.info(f"📊 Obtenidos {len(result.data)} registros de historial para {banco}")
                return result.data
            else:
                logger.info(f"ℹ️ No hay historial disponible para {banco}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de {banco}: {str(e)}")
            return []
    
    def mostrar_resumen_banco(self, banco):
        """
        Muestra un resumen del estado actual y historial de un banco
        
        Args:
            banco (str): Nombre del banco
        """
        try:
            print(f"\n📊 === RESUMEN DE SALDOS - {banco.upper()} ===")
            
            # Obtener último saldo
            ultimo = self.obtener_ultimo_saldo(banco)
            if ultimo:
                fecha_ultimo = datetime.fromisoformat(ultimo['fecha_captura'].replace('Z', '+00:00'))
                print(f"💰 Último saldo: ${ultimo['saldo']:,.2f}")
                print(f"🕐 Fecha captura: {fecha_ultimo.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("ℹ️ No hay registros disponibles")
                return
            
            # Obtener historial reciente
            historial = self.obtener_historial_saldos(banco, 5)
            if len(historial) > 1:
                print(f"📈 Registros recientes: {len(historial)}")
                
                # Calcular tendencia
                primer_saldo = Decimal(str(historial[-1]['saldo']))
                ultimo_saldo = Decimal(str(historial[0]['saldo']))
                diferencia = ultimo_saldo - primer_saldo
                
                print(f"📊 Primer saldo del período: ${primer_saldo:,.2f}")
                print(f"📊 Diferencia: ${diferencia:,.2f}")
                
                if diferencia > 0:
                    print(f"📈 Tendencia: Incremento de ${diferencia:,.2f}")
                elif diferencia < 0:
                    print(f"📉 Tendencia: Disminución de ${abs(diferencia):,.2f}")
                else:
                    print(f"➡️ Tendencia: Sin cambios")
            
            print(f"========================\n")
            
        except Exception as e:
            logger.error(f"❌ Error mostrando resumen de {banco}: {str(e)}")


# Función de conveniencia para uso directo
def guardar_saldo_bci(saldo, forzar=False):
    """
    Función de conveniencia para guardar saldo de BCI
    
    Args:
        saldo (float): Saldo a guardar
        forzar (bool): Si True, guarda sin verificar diferencias
        
    Returns:
        bool: True si se guardó exitosamente
    """
    db = SaldoBancosDB()
    return db.guardar_saldo("BCI", saldo, forzar)


def obtener_ultimo_saldo_bci():
    """
    Función de conveniencia para obtener último saldo de BCI
    
    Returns:
        dict: Último registro de saldo o None
    """
    db = SaldoBancosDB()
    return db.obtener_ultimo_saldo("BCI")


def mostrar_resumen_bci():
    """
    Función de conveniencia para mostrar resumen de BCI
    """
    db = SaldoBancosDB()
    return db.mostrar_resumen_banco("BCI")


if __name__ == "__main__":
    # Prueba básica del módulo
    print("🧪 Probando módulo saldo_bancos_db...")
    
    db = SaldoBancosDB()
    
    # Mostrar resumen actual
    db.mostrar_resumen_banco("BCI")
    
    print("✅ Módulo saldo_bancos_db funcionando correctamente")