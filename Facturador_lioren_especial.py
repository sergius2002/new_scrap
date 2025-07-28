#!/usr/bin/env python3
"""
Versión especial del facturador para procesar todas las facturas pendientes del RUT 26870197-4
"""

import os
import requests
import base64
import logging
from datetime import datetime, timedelta
import re
import time
import io
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from supabase import create_client, Client
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style

# Inicializar colorama
colorama.init()

# Cargar las variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración de Lioren
API_TOKEN_ST_CRISTOBAL = os.getenv("API_TOKEN_ST_CRISTOBAL")
API_URL = "https://www.lioren.cl/api/dtes"

# Configuración de Gmail
TOKEN_PATH = os.getenv("TOKEN_PATH")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def obtener_facturas_pendientes_rut_especifico():
    """Obtiene las facturas pendientes del RUT específico de los últimos 3 días"""
    try:
        # Calcular fecha límite (3 días atrás)
        fecha_limite = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        logger.info(f"🔍 Consultando facturas pendientes para RUT 26870197-4 desde {fecha_limite}...")
        
        response = (
            supabase.table("transferencias")
            .select("hash, monto, rut, fecha, empresa, facturación")
            .eq("enviada", 0)
            .eq("rut", "26870197-4")
            .gte("fecha", fecha_limite)
            .execute()
        )

        if hasattr(response, 'error') and response.error:
            logger.error(f"Error al obtener facturas: {response.error}")
            return []

        facturas = response.data
        if facturas:
            logger.info(f"✅ Se encontraron {len(facturas)} facturas pendientes para RUT 26870197-4")
            for factura in facturas:
                logger.info(f"  • Fecha: {factura['fecha']} | Monto: ${factura['monto']:,}")
        else:
            logger.info("❌ No hay facturas pendientes para este RUT")
            
        return facturas
    except Exception as e:
        logger.error(f"Error al obtener facturas: {e}")
        return []

def obtener_datos_faltantes(rut):
    """Obtiene los datos faltantes para un RUT"""
    try:
        response = (
            supabase.table("datos_faltantes")
            .select("rs, email, direccion, comuna")
            .eq("rut", rut)
            .execute()
        )
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error al obtener datos faltantes: {response.error}")
            return {}
        
        datos = response.data
        if datos:
            logger.info(f"✅ Datos encontrados para RUT {rut}")
            return datos[0]
        else:
            logger.warning(f"❌ No se encontraron datos para RUT {rut}")
            return {}
            
    except Exception as e:
        logger.error(f"Error al obtener datos faltantes: {e}")
        return {}

def actualizar_factura_enviada(hash_id):
    """Marca una factura como enviada"""
    try:
        response = (
            supabase.table("transferencias")
            .update({"enviada": 1})
            .eq("hash", hash_id)
            .execute()
        )
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error al actualizar factura {hash_id}: {response.error}")
        else:
            logger.info(f"✅ Factura {hash_id} marcada como enviada")
    except Exception as e:
        logger.error(f"Error al actualizar factura {hash_id}: {e}")

def obtener_servicio_gmail():
    """Obtiene el servicio de Gmail"""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def enviar_factura_email(destinatario, asunto, mensaje, pdf_bytes, pdf_nombre):
    """Envía la factura por email"""
    try:
        service = obtener_servicio_gmail()
        
        mensaje_mime = MIMEMultipart()
        mensaje_mime["to"] = destinatario
        mensaje_mime["subject"] = asunto
        mensaje_mime.attach(MIMEText(mensaje, "plain", "utf-8"))

        if pdf_bytes:
            mime_part = MIMEBase("application", "octet-stream")
            mime_part.set_payload(pdf_bytes)
            encoders.encode_base64(mime_part)
            mime_part.add_header("Content-Disposition", f'attachment; filename="{pdf_nombre}"')
            mensaje_mime.attach(mime_part)

        raw = base64.urlsafe_b64encode(mensaje_mime.as_bytes()).decode("utf-8")
        message = {"raw": raw}
        
        sent_msg = service.users().messages().send(userId="me", body=message).execute()
        logger.info(f"✅ Email enviado. ID: {sent_msg.get('id')}")
        return True
    except Exception as e:
        logger.error(f"❌ Error al enviar email: {e}")
        return False

def procesar_facturas_especial():
    """Procesa todas las facturas pendientes del RUT específico"""
    try:
        facturas = obtener_facturas_pendientes_rut_especifico()
        if not facturas:
            logger.info("No hay facturas pendientes para procesar.")
            return

        fecha_facturacion = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"\n🚀 Procesando {len(facturas)} facturas...")

        # Obtener datos del cliente una sola vez
        datos_cliente = obtener_datos_faltantes("26870197-4")
        if not datos_cliente:
            logger.error("❌ No se pudieron obtener los datos del cliente")
            return

        rs = datos_cliente.get('rs', '')
        email = datos_cliente.get('email', '')
        direccion = datos_cliente.get('direccion', '')
        comuna_db = datos_cliente.get('comuna', 295)
        comuna_value = int(comuna_db) if comuna_db else 295

        for i, factura in enumerate(facturas, 1):
            hash_id = factura['hash']
            monto = factura['monto']
            fecha_detectada = factura['fecha']
            empresa = factura['empresa']

            logger.info(f"\n📋 Procesando factura {i}/{len(facturas)}:")
            logger.info(f"  • Hash: {hash_id}")
            logger.info(f"  • Monto: ${monto:,}")
            logger.info(f"  • Fecha: {fecha_detectada}")
            logger.info(f"  • Empresa: {empresa}")

            # Preparar datos para la API
            data = {
                "emisor": {
                    "tipodoc": "34",
                    "fecha": fecha_facturacion,
                    "email": "sergio.plaza.altamirano@gmail.com",
                    "telefono": "971073454",
                    "observaciones": "Factura exenta generada masivamente - RUT especial"
                },
                "receptor": {
                    "rut": "26870197-4",
                    "rs": rs,
                    "giro": "Edición de programas informáticos",
                    "comuna": comuna_value,
                    "ciudad": 176,
                    "direccion": direccion,
                    "email": email,
                    "telefono": "971073454"
                },
                "detalles": [
                    {
                        "codigo": "001",
                        "nombre": "Activo digital no corpóreo",
                        "cantidad": 1,
                        "precio": monto,
                        "exento": True
                    }
                ],
                "pagos": [
                    {
                        "fecha": fecha_facturacion,
                        "mediopago": 1,
                        "monto": monto,
                        "cobrar": False
                    }
                ],
                "expects": "all"
            }

            headers = {
                "Authorization": f"Bearer {API_TOKEN_ST_CRISTOBAL}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "FacturadorLioren/1.0",
                "Cache-Control": "no-cache"
            }
            
            logger.info(f"📤 Enviando factura a API Lioren...")
            
            response = requests.post(API_URL, json=data, headers=headers)
            
            if response.status_code == 200:
                if response.text.strip():
                    try:
                        response_data = response.json()
                        logger.info(f"✅ Factura emitida exitosamente")
                        
                        # Marcar como enviada
                        actualizar_factura_enviada(hash_id)

                        # Enviar por email
                        pdf_base64 = response_data.get("pdf", None)
                        if pdf_base64:
                            pdf_bytes = base64.b64decode(pdf_base64)
                            pdf_filename = f"{fecha_facturacion.replace('-', '')}_26870197-4_{hash_id[:8]}.pdf"
                            
                            try:
                                monto_int = int(float(monto))
                                formatted_monto = "${:,}".format(monto_int).replace(",", ".")
                            except ValueError:
                                formatted_monto = f"${monto}"

                            asunto_email = "Factura Emitida"
                            cuerpo_email = (
                                f"Estimado/a {rs},\n\n"
                                f"Adjuntamos la factura emitida con fecha {fecha_facturacion} "
                                f"por un monto de {formatted_monto}.\n\n"
                                f"Saludos,\nEquipo SAN CRISTOBAL"
                            )

                            if email and re.match(r"[^@]+@[^@]+\.[^@]+", email):
                                exito = enviar_factura_email(email, asunto_email, cuerpo_email, pdf_bytes, pdf_filename)
                                if exito:
                                    logger.info(f"✅ Email enviado a {email}")
                                else:
                                    logger.warning(f"⚠️ Fallo al enviar email a {email}")
                            else:
                                logger.warning(f"⚠️ Email inválido: {email}")
                        else:
                            logger.warning(f"⚠️ No se recibió PDF")
                    except ValueError as json_error:
                        logger.error(f"❌ Error al parsear respuesta JSON: {json_error}")
                else:
                    logger.error(f"❌ Respuesta vacía del servidor")
            else:
                logger.error(f"❌ Error al emitir factura (status {response.status_code})")
                logger.error(f"Respuesta: {response.text[:500]}...")

            # Pausa entre facturas para no sobrecargar la API
            if i < len(facturas):
                logger.info("⏳ Esperando 2 segundos antes de la siguiente factura...")
                time.sleep(2)

    except Exception as e:
        logger.critical(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 FACTURADOR ESPECIAL - RUT 26870197-4")
    logger.info(f"{'='*60}")
    
    procesar_facturas_especial()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Proceso completado")
    logger.info(f"{'='*60}") 