from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient, inlineQueryResultArticle
from MoodleClient import MoodleClient
from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
from urllib.parse import unquote
import requests
import S5Crypto
import traceback
import pytz
import threading
import json
import re
import asyncio
from telethon import TelegramClient, events

# ==============================
# CONFIGURACIÓN DEL CANAL Y MOODLE
# ==============================

# Credenciales de Telethon (obtén en my.telegram.org)
API_ID = 20534584  # ¡REEMPLAZA CON TU API ID!
API_HASH = '6d5b13261d2c92a9a00afc1fd613b9df'  # ¡REEMPLAZA CON TU API HASH!

# Canal a escuchar
CANAL_PRIVADO = '@empresaelectricacienfuegos1'
NOMBRE_CANAL = 'Cienfuegos'
ARCHIVO_JSON = 'jsonCienfuegos.json'

# Configuración de Moodle UCF (cursos.ucf.edu.cu)
MOODLE_HOST_UCF = 'https://cursos.ucf.edu.cu/'
MOODLE_USER_UCF = 'julianrene'
MOODLE_PASS_UCF = 'Transfer60*'
MOODLE_REPO_ID_UCF = 4

# Cola de mensajes pendientes
mensajes_pendientes = []
lock_mensajes = threading.Lock()

# Estados de autenticación
auth_sessions = {}
auth_lock = threading.Lock()
listener_threads = {}

# ==============================
# CONFIGURACIÓN EXISTENTE DEL BOT
# ==============================

BOT_TOKEN = "8340084935:AAHLn3ftkhaJg9KyDgtL1ely4vo-1DlFyqM"
ADMIN_USERNAME = "Eliel_21"
ADMIN_CHAT_ID = 7363341763
LOG_GROUP_ID = -1004295272245

MAINTENANCE_MODE = False
BANNED_USERS = set()
REMOVED_USERS = set()
ACTIVE_PROCESSES = {}
ACTIVE_STATUS_CHECKS = set()
CHANGING_CLOUD_USERS = set()

try:
    CUBA_TZ = pytz.timezone('America/Havana')
except:
    CUBA_TZ = None

USER_EVIDENCE_MARKER = " "

AVAILABLE_CLOUDS = [
    {
        "cloudtype": "moodle",
        "moodle_host": "https://moodle.instec.cu/",
        "moodle_repo_id": 3,
        "moodle_user": "kevin.cruz",
        "moodle_password": "Kevin10.",
        "zips": 1023,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    {
        "cloudtype": "moodle",
        "moodle_host": "https://cursos.uo.edu.cu/",
        "moodle_repo_id": 4,
        "moodle_user": "mayelin.cabrera",
        "moodle_password": "Mayelin*167.",
        "zips": 99,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    {
        "cloudtype": "moodle",
        "moodle_host": "https://cursos.ucf.edu.cu/",
        "moodle_repo_id": 4,
        "moodle_user": "julianrene",
        "moodle_password": "Transfer60*",
        "zips": 4,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    {
        "cloudtype": "moodle",
        "moodle_host": "https://cursos.fundacion.uh.cu/",
        "moodle_repo_id": 5,
        "moodle_user": "Claudia.btabares@estudiantes.instec.uh.cu",
        "moodle_password": "cbt260706*TM",
        "zips": 11,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    {
        "cloudtype": "moodle",
        "moodle_host": "https://eva.umcc.cu/posgrado/",
        "moodle_repo_id": 5,
        "moodle_user": "daniela.martinez",
        "moodle_password": "Zenia*07",
        "zips": 99,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    {
        "cloudtype": "moodle",
        "moodle_host": "https://eva.umcc.cu/pregrado/",
        "moodle_repo_id": 5,
        "moodle_user": "daniela.martinez",
        "moodle_password": "Zenia*07",
        "zips": 19,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    {
        "cloudtype": "moodle",
        "moodle_host": "https://uvp.ult.edu.cu/",
        "moodle_repo_id": 5,
        "moodle_user": "ariagnaav",
        "moodle_password": "A40*i33",
        "zips": 99,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    }
]

PRE_CONFIGURATED_USERS = {
    "Thali355,Eliel_21,Kev_inn10": AVAILABLE_CLOUDS[0],
    "thu,hola1": AVAILABLE_CLOUDS[1],
    "VanNeiFertio,XD,SchnauzerMinnie": AVAILABLE_CLOUDS[2],
    "hola,usuario2": AVAILABLE_CLOUDS[3],
    "gatitoo_miauu,usuario_nuevo2": AVAILABLE_CLOUDS[4],
    "Satoru_2115,usuario_nuevo4": AVAILABLE_CLOUDS[5],
    "usuario1,usuario2": AVAILABLE_CLOUDS[6]
}

# ==============================
# FUNCIONES DE UTILIDAD
# ==============================

def get_cuba_time():
    if CUBA_TZ:
        return datetime.datetime.now(CUBA_TZ)
    return datetime.datetime.now()

def format_cuba_date(dt=None):
    if dt is None:
        dt = get_cuba_time()
    return dt.strftime("%d/%m/%y")

def format_cuba_datetime(dt=None):
    if dt is None:
        dt = get_cuba_time()
    formatted_date = dt.strftime("%d/%m/%y")
    hour = str(int(dt.strftime("%I")))
    minute_ampm = dt.strftime("%M %p")
    return f"{formatted_date} {hour}:{minute_ampm}"

def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    val = size_bytes / 1024.0
    if val < 1024:
        formatted = f"{val:.1f}"
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        return f"{formatted} KB"
    val /= 1024.0
    if val < 1024:
        formatted = f"{val:.1f}"
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        return f"{formatted} MB"
    val /= 1024.0
    if val < 1024:
        formatted = f"{val:.1f}"
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        return f"{formatted} GB"
    val /= 1024.0
    formatted = f"{val:.1f}"
    if formatted.endswith('.0'):
        formatted = formatted[:-2]
    return f"{formatted} TB"

def send_reaction(chat_id, message_id, emoji="⚡"):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": json.dumps([{"type": "emoji", "emoji": emoji}])
        }
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Error al enviar reacción: {e}")

def send_sticker(chat_id, sticker_id):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendSticker"
        payload = {"chat_id": chat_id, "sticker": sticker_id}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Error al enviar sticker: {e}")

# ==============================
# SISTEMA DE ESTADÍSTICAS
# ==============================

class MemoryStats:
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        self.stats = {'total_uploads': 0, 'total_deletes': 0, 'total_size_uploaded': 0}
        self.user_stats = {}
        self.upload_logs = []
        self.delete_logs = []
    
    def check_and_update_daily_reset(self, username):
        current_date = format_cuba_date()
        if username in self.user_stats:
            if self.user_stats[username].get('last_date') != current_date:
                self.user_stats[username]['daily_size'] = 0
                self.user_stats[username]['last_date'] = current_date
        else:
            self.user_stats[username] = {
                'uploads': 0, 'deletes': 0, 'total_size': 0,
                'daily_size': 0, 'last_date': current_date,
                'last_activity': format_cuba_datetime()
            }
    
    def log_upload(self, username, filename, file_size, moodle_host):
        self.check_and_update_daily_reset(username)
        self.stats['total_uploads'] += 1
        self.stats['total_size_uploaded'] += file_size
        self.user_stats[username]['uploads'] += 1
        self.user_stats[username]['total_size'] += file_size
        self.user_stats[username]['daily_size'] += file_size
        self.user_stats[username]['last_activity'] = format_cuba_datetime()
        self.upload_logs.append({
            'timestamp': format_cuba_datetime(),
            'username': username, 'filename': filename,
            'file_size_bytes': file_size,
            'file_size_formatted': format_file_size(file_size),
            'moodle_host': moodle_host
        })
        if len(self.upload_logs) > 300:
            self.upload_logs.pop(0)
        return True
    
    def get_user_stats(self, username):
        self.check_and_update_daily_reset(username)
        return self.user_stats.get(username)
    
    def get_all_stats(self):
        return self.stats
    
    def get_recent_uploads(self, limit=10):
        return self.upload_logs[-limit:][::-1] if self.upload_logs else []
    
    def has_any_data(self):
        return len(self.upload_logs) > 0 or len(self.delete_logs) > 0

memory_stats = MemoryStats()

# ==============================
# FUNCIONES PARA EL CANAL
# ==============================

def acumular_mensaje(mensaje_texto, fecha_mensaje):
    """Guarda un mensaje en la cola para procesar después"""
    global mensajes_pendientes
    
    texto_limpio = mensaje_texto.strip()
    enlaces = re.findall(r'https?://[^\s]+', texto_limpio)
    texto_sin_enlaces = texto_limpio
    for enlace in enlaces:
        texto_sin_enlaces = texto_sin_enlaces.replace(enlace, '').strip()
    
    with lock_mensajes:
        mensajes_pendientes.append({
            'fecha': fecha_mensaje.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_cuba': format_cuba_datetime(fecha_mensaje),
            'contenido': texto_sin_enlaces,
            'contenido_completo': texto_limpio,
            'enlaces': enlaces
        })
    
    print(f"📥 Mensaje acumulado ({len(mensajes_pendientes)} en cola)")

def subir_json_a_ucf(nombre_archivo):
    """Sube el archivo JSON a Moodle UCF"""
    try:
        client = MoodleClient(
            MOODLE_USER_UCF,
            MOODLE_PASS_UCF,
            MOODLE_HOST_UCF,
            MOODLE_REPO_ID_UCF
        )
        
        if client.login():
            evidencias = client.getEvidences()
            evidencia_nombre = f"{NOMBRE_CANAL}{USER_EVIDENCE_MARKER}canal"
            
            evidencia = None
            for ev in evidencias:
                if ev['name'] == evidencia_nombre:
                    evidencia = ev
                    break
            
            if evidencia is None:
                evidencia = client.createEvidence(evidencia_nombre)
            
            fileid = None
            with open(nombre_archivo, 'rb') as f:
                fileid, _ = client.upload_file(
                    nombre_archivo, 
                    evidencia, 
                    fileid,
                    progressfunc=None
                )
            
            client.saveEvidence(evidencia)
            client.logout()
            return True
        else:
            print("❌ Error de autenticación en UCF")
            return False
            
    except Exception as e:
        print(f"❌ Error al subir a UCF: {e}")
        return False

def subir_todos_los_mensajes():
    """Toma todos los mensajes acumulados y los sube a Moodle UCF"""
    global mensajes_pendientes
    
    with lock_mensajes:
        if not mensajes_pendientes:
            return False
        mensajes_a_subir = mensajes_pendientes.copy()
        mensajes_pendientes = []
    
    try:
        datos = {
            'canal': 'Empresa Eléctrica Cienfuegos',
            'nombre_canal': NOMBRE_CANAL,
            'ultima_actualizacion': format_cuba_datetime(),
            'total_mensajes': len(mensajes_a_subir),
            'mensajes': mensajes_a_subir
        }
        
        with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        exito = subir_json_a_ucf(ARCHIVO_JSON)
        
        if exito:
            print(f"✅ {len(mensajes_a_subir)} mensajes subidos a UCF")
            if LOG_GROUP_ID != 0:
                try:
                    bot = ObigramClient(BOT_TOKEN)
                    mensaje_log = (
                        f"📄 <b>Mensajes del canal procesados</b>\n\n"
                        f"📢 <b>Canal:</b> <b>{NOMBRE_CANAL}</b>\n"
                        f"📊 <b>Mensajes:</b> <b>{len(mensajes_a_subir)}</b>\n"
                        f"📅 <b>Actualización:</b> <b>{datos['ultima_actualizacion']}</b>\n"
                        f"💾 <b>JSON subido a UCF</b>"
                    )
                    bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar: {e}")
            return True
        else:
            with lock_mensajes:
                mensajes_pendientes = mensajes_a_subir + mensajes_pendientes
            return False
            
    except Exception as e:
        print(f"❌ Error al subir mensajes: {e}")
        with lock_mensajes:
            mensajes_pendientes = mensajes_a_subir + mensajes_pendientes
        return False
    finally:
        if os.path.exists(ARCHIVO_JSON):
            try:
                os.unlink(ARCHIVO_JSON)
            except:
                pass

# ==============================
# SISTEMA DE AUTENTICACIÓN CON TELETHON
# ==============================

async def iniciar_sesion_telethon(username, phone_number):
    """Inicia el proceso de autenticación para un usuario"""
    try:
        session_file = f'sesion_{username}.session'
        client = TelegramClient(session_file, API_ID, API_HASH)
        await client.connect()
        
        await client.send_code_request(phone_number)
        
        with auth_lock:
            auth_sessions[username] = {
                'client': client,
                'phone': phone_number,
                'step': 'waiting_code'
            }
        
        return True, "📱 Se ha enviado un código de verificación a tu Telegram. Envíalo con /code <codigo>"
    except Exception as e:
        return False, f"❌ Error al iniciar sesión: {str(e)}"

async def verificar_codigo_telethon(username, code):
    """Verifica el código de autenticación"""
    with auth_lock:
        if username not in auth_sessions:
            return False, "❌ No hay un proceso de autenticación activo. Usa /login primero."
        
        session_data = auth_sessions[username]
        if session_data['step'] != 'waiting_code':
            return False, "❌ No hay un código pendiente de verificar."
        
        client = session_data['client']
    
    try:
        await client.sign_in(session_data['phone'], code)
        await client.disconnect()
        
        with auth_lock:
            del auth_sessions[username]
        
        # Iniciar el listener para este usuario
        iniciar_listener_usuario(username)
        
        return True, "✅ ¡Autenticación exitosa! El bot ya puede leer el canal."
    except Exception as e:
        return False, f"❌ Código incorrecto: {str(e)}"

def iniciar_listener_usuario(username):
    """Inicia el listener del canal para un usuario específico"""
    if username in listener_threads and listener_threads[username].is_alive():
        return
    
    def run_listener():
        asyncio.run(escuchar_canal_usuario(username))
    
    thread = threading.Thread(target=run_listener, daemon=True)
    thread.start()
    listener_threads[username] = thread

async def escuchar_canal_usuario(username):
    """Escucha mensajes del canal usando la sesión del usuario"""
    session_file = f'sesion_{username}.session'
    
    if not os.path.exists(session_file):
        print(f"❌ No hay sesión para {username}")
        return
    
    try:
        client = TelegramClient(session_file, API_ID, API_HASH)
        await client.start()
        
        @client.on(events.NewMessage(chats=CANAL_PRIVADO))
        async def handler(event):
            mensaje = event.message.text
            if not mensaje:
                return
            acumular_mensaje(mensaje, event.message.date)
        
        print(f"🔍 Usuario {username} escuchando canal: {CANAL_PRIVADO}")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Error en listener de {username}: {e}")

def procesar_mensajes_periodicamente():
    """Cada 5 minutos, sube los mensajes acumulados a Moodle"""
    while True:
        time.sleep(300)
        try:
            print("🔄 Procesando mensajes acumulados...")
            subir_todos_los_mensajes()
        except Exception as e:
            print(f"❌ Error en procesamiento periódico: {e}")

# ==============================
# FUNCIONES EXISTENTES DEL BOT
# ==============================

def expand_user_groups():
    expanded = {}
    for user_group, config in PRE_CONFIGURATED_USERS.items():
        users = [u.strip() for u in user_group.split(',')]
        for user in users:
            expanded[user] = config.copy()
    return expanded

def initialize_database(jdb):
    expanded_users = expand_user_groups()
    for username, config in expanded_users.items():
        if username.lower() in {r.lower() for r in REMOVED_USERS}:
            continue
        if jdb.get_user(username) is None:
            jdb.create_user(username)
            user_data = jdb.get_user(username)
            for key, value in config.items():
                user_data[key] = value
            jdb.save_data_user(username, user_data)
    jdb.save()

def update_process(thread_id, username, filename, action, current, total):
    try:
        current = int(current or 0)
        total = int(total or 0)
        percent = (current / total) * 100 if total > 0 else 0
        if percent > 100: percent = 100
        fmt_percent = f"{int(percent)}%" if percent.is_integer() else f"{percent:.1f}%"
        ACTIVE_PROCESSES[thread_id] = {
            'user': username, 'file': filename, 'action': action,
            'percent': fmt_percent, 'last_update': time.time()
        }
    except: pass

def clean_process(thread_id):
    if thread_id in ACTIVE_PROCESSES:
        del ACTIVE_PROCESSES[thread_id]

# ==============================
# FUNCIÓN PRINCIPAL onmessage
# ==============================

def onmessage(update, bot: ObigramClient):
    global MAINTENANCE_MODE, BANNED_USERS, REMOVED_USERS
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        chat_id = update.message.chat.id

        msgText = ''
        try: msgText = update.message.text
        except: pass

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()
        
        expanded_users = expand_user_groups()
        
        has_access = False
        if username:
            if username.lower() == ADMIN_USERNAME.lower():
                has_access = True
            elif username.lower() in {b.lower() for b in BANNED_USERS}:
                bot.sendMessage(chat_id, '<b>🚫 Has sido baneado.</b>', parse_mode='html')
                return
            elif username.lower() in {u.lower() for u in REMOVED_USERS}:
                has_access = False
            else:
                for u in expanded_users.keys():
                    if u.lower() == username.lower():
                        has_access = True
                        break
                if not has_access and jdb.get_user(username) is not None:
                    has_access = True

        if not has_access:
            bot.sendMessage(chat_id, '<b>➲ No tienes acceso.</b>', parse_mode='html')
            return

        if MAINTENANCE_MODE and username.lower() != ADMIN_USERNAME.lower():
            bot.sendMessage(chat_id, "🛠️ <b>¡Sistema en mantenimiento!</b>", parse_mode='html')
            return
        
        initialize_database(jdb)
        user_info = jdb.get_user(username)
        if user_info is None:
            config = AVAILABLE_CLOUDS[0]
            jdb.create_user(username)
            user_info = jdb.get_user(username)
            for key, value in config.items():
                user_info[key] = value
            jdb.save_data_user(username, user_info)
            jdb.save()

        if user_info.get('chat_id') != chat_id:
            user_info['chat_id'] = chat_id
            jdb.save_data_user(username, user_info)
            jdb.save()

        # ============================================
        # COMANDOS DE AUTENTICACIÓN PARA EL CANAL
        # ============================================
        
        if '/login' in msgText:
            parts = msgText.replace('/login', '').strip()
            if not parts:
                bot.sendMessage(chat_id, 
                    "📱 <b>Iniciar sesión con Telethon</b>\n\n"
                    "Envía tu número de teléfono con el comando:\n"
                    "<code>/login +53XXXXXXXXX</code>\n\n"
                    "Ejemplo: <code>/login +53512345678</code>",
                    parse_mode='html')
                return
            
            phone_number = parts.split()[0] if parts else parts
            if not phone_number.startswith('+'):
                phone_number = '+' + phone_number
            
            # Enviar mensaje de "procesando"
            msg = bot.sendMessage(chat_id, "⏳ <b>Iniciando sesión...</b>", parse_mode='html')
            
            exito, mensaje = asyncio.run(iniciar_sesion_telethon(username, phone_number))
            bot.editMessageText(msg, mensaje, parse_mode='html')
            return

        if '/code' in msgText:
            parts = msgText.replace('/code', '').strip()
            if not parts:
                bot.sendMessage(chat_id, 
                    "📱 <b>Verificar código</b>\n\n"
                    "Envía el código que recibiste:\n"
                    "<code>/code 12345</code>",
                    parse_mode='html')
                return
            
            code = parts.split()[0] if parts else parts
            
            msg = bot.sendMessage(chat_id, "⏳ <b>Verificando código...</b>", parse_mode='html')
            exito, mensaje = asyncio.run(verificar_codigo_telethon(username, code))
            bot.editMessageText(msg, mensaje, parse_mode='html')
            return

        if '/status_canal' in msgText:
            session_file = f'sesion_{username}.session'
            if os.path.exists(session_file):
                bot.sendMessage(chat_id, "🟢 <b>Conectado al canal</b>\n✅ La autenticación está activa.", parse_mode='html')
            else:
                bot.sendMessage(chat_id, "🔴 <b>No conectado</b>\n❌ Usa /login para autenticarte.", parse_mode='html')
            return

        if '/logout' in msgText:
            session_file = f'sesion_{username}.session'
            if os.path.exists(session_file):
                try:
                    os.remove(session_file)
                    bot.sendMessage(chat_id, "✅ <b>Sesión cerrada</b>\nLa sesión de Telethon ha sido eliminada.", parse_mode='html')
                except:
                    bot.sendMessage(chat_id, "❌ <b>Error al cerrar sesión</b>", parse_mode='html')
            else:
                bot.sendMessage(chat_id, "ℹ️ <b>No hay sesión activa</b>", parse_mode='html')
            return

        # ============================================
        # COMANDOS EXISTENTES DEL BOT
        # ============================================
        
        if '/start' in msgText:
            if username.lower() == ADMIN_USERNAME.lower():
                start_msg = f"👑 <b>Administrador</b>\n\n👤 @{username}\n☁️ {user_info['moodle_host']}\n⚖️ {user_info['zips']} MB"
            else:
                start_msg = f"👤 @{username}\n☁️ {user_info['moodle_host']}\n⚖️ {user_info['zips']} MB"
            
            bot.sendMessage(chat_id, start_msg, parse_mode='html')
            return

        if '/status' == msgText:
            bot.sendMessage(chat_id, "🟢 <b>Bot funcionando correctamente</b>", parse_mode='html')
            return

        # Respuesta para otros comandos
        bot.sendMessage(chat_id, '<b>➲ Comando no reconocido</b>', parse_mode='html')
            
    except Exception as ex:
        print(f"Error en onmessage: {ex}")
        print(traceback.format_exc())
        try:
            bot.sendMessage(chat_id, f'<b>❌ Error:</b> {str(ex)}', parse_mode='html')
        except:
            pass

# ==============================
# FUNCIÓN PRINCIPAL main
# ==============================

def main():
    # Iniciar el procesador periódico
    procesador_thread = threading.Thread(target=procesar_mensajes_periodicamente, daemon=True)
    procesador_thread.start()
    print("✅ Procesador periódico iniciado (cada 5 minutos)")
    
    # Iniciar el bot principal
    bot = ObigramClient(BOT_TOKEN)
    bot.onMessage(onmessage)
    print("🤖 Bot iniciado. Usa /login +53XXXXXXXXX para autenticarte.")
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error en main: {e}")
        main()