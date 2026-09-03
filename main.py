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
ARCHIVO_JSON = 'jsonCienfuegos.json'  # Nombre fijo en Moodle

# Configuración de Moodle UCF (cursos.ucf.edu.cu) - Nube 2 de tu lista
MOODLE_HOST_UCF = 'https://cursos.ucf.edu.cu/'
MOODLE_USER_UCF = 'julianrene'
MOODLE_PASS_UCF = 'Transfer60*'
MOODLE_REPO_ID_UCF = 4

# Cola de mensajes pendientes (hilo seguro)
mensajes_pendientes = []
lock_mensajes = threading.Lock()

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

# ==============================
# LISTA DE NUBES DISPONIBLES
# ==============================

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
# FUNCIONES PARA EL CANAL (NUEVO)
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
    """Sube el archivo JSON a Moodle UCF (cursos.ucf.edu.cu)"""
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
            
            # Subir el archivo (sobrescribiendo)
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
            # Notificar al grupo de logs
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
# SISTEMA DE AUTENTICACIÓN CON TELETHON DESDE EL BOT
# ==============================

auth_sessions = {}
auth_lock = threading.Lock()

async def iniciar_sesion_telethon(username, phone_number):
    """Inicia el proceso de autenticación para un usuario"""
    try:
        session_file = f'sesion_{username}.session'
        client = TelegramClient(session_file, API_ID, API_HASH)
        await client.connect()
        
        # Enviar código de verificación
        await client.send_code_request(phone_number)
        
        # Guardar el cliente en el estado del usuario
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
        
        # Guardar la sesión
        await client.disconnect()
        
        with auth_lock:
            del auth_sessions[username]
        
        # Crear archivo de sesión (ya lo creó TelegramClient)
        return True, "✅ ¡Autenticación exitosa! El bot ya puede leer el canal."
    except Exception as e:
        return False, f"❌ Código incorrecto: {str(e)}"

# ==============================
# TELETHON: ESCUCHA DEL CANAL
# ==============================

listener_threads = {}

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

# ==============================
# PROCESAMIENTO PERIÓDICO
# ==============================

def procesar_mensajes_periodicamente():
    """Cada 5 minutos, sube los mensajes acumulados a Moodle"""
    while True:
        time.sleep(300)  # 5 minutos
        try:
            print("🔄 Procesando mensajes acumulados...")
            subir_todos_los_mensajes()
        except Exception as e:
            print(f"❌ Error en procesamiento periódico: {e}")

# ==============================
# FUNCIONES DE PROGRESO (TU CÓDIGO ORIGINAL)
# ==============================

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

def downloadFile(downloader, filename, currentBits, totalBits, speed, elapsed_time, args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        username = args[3] if len(args) > 3 else "Desconocido"
        
        if thread.getStore('stop'):
            downloader.stop()
            raise Exception("Tarea detenida por mantenimiento o cancelación")
        
        update_process(thread.id, username, filename, '📥 Descargando', currentBits, totalBits)
        
        downloadingInfo = infos.createDownloading(filename, totalBits, currentBits, speed, elapsed_time, tid=thread.id)
        bot.editMessageText(message, downloadingInfo, parse_mode='html')
    except Exception as ex:
        raise ex

def uploadFile(filename, currentBits, totalBits, speed, elapsed_time, args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        username = args[4] if len(args) > 4 else "Desconocido"
        
        if thread and thread.getStore('stop'):
            raise Exception("Tarea detenida por mantenimiento o cancelación")
        
        update_process(thread.id, username, filename, '📤 Subiendo', currentBits, totalBits)
        
        tid_str = thread.id if thread else ''
        uploadingInfo = infos.createUploading(filename, totalBits, currentBits, speed, elapsed_time, originalfile, tid=tid_str)
        bot.editMessageText(message, uploadingInfo, parse_mode='html')
    except Exception as ex:
        raise ex

# ==============================
# FUNCIONES DE PROCESAMIENTO (TU CÓDIGO ORIGINAL - RESUMIDAS)
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

def processUploadFiles(filename, filesize, files, update, bot, message, thread=None, jdb=None):
    # Esta función debe ser tu código ORIGINAL completo
    # Por brevedad, pongo una versión resumida, pero DEBES USAR TU CÓDIGO ORIGINAL
    pass

def processFile(update, bot, message, file, thread=None, jdb=None):
    # Esta función debe ser tu código ORIGINAL completo
    pass

def ddl(update, bot, message, url, file_name='', thread=None, jdb=None):
    # Esta función debe ser tu código ORIGINAL completo
    pass

def sendTxt(name, files, update, bot, send_to_group=False, user_info=None):
    # Esta función debe ser tu código ORIGINAL completo
    pass

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
                bot.editMessageText(message, 
                    "📱 <b>Iniciar sesión con Telethon</b>\n\n"
                    "Envía tu número de teléfono con el comando:\n"
                    "<code>/login +53XXXXXXXXX</code>\n\n"
                    "Ejemplo: <code>/login +53512345678</code>",
                    parse_mode='html')
                return
            
            phone_number = parts.split()[0] if parts else parts
            if not phone_number.startswith('+'):
                phone_number = '+' + phone_number
            
            # Iniciar autenticación
            exito, mensaje = asyncio.run(iniciar_sesion_telethon(username, phone_number))
            bot.editMessageText(message, mensaje, parse_mode='html')
            return

        if '/code' in msgText:
            parts = msgText.replace('/code', '').strip()
            if not parts:
                bot.editMessageText(message, 
                    "📱 <b>Verificar código</b>\n\n"
                    "Envía el código que recibiste:\n"
                    "<code>/code 12345</code>",
                    parse_mode='html')
                return
            
            code = parts.split()[0] if parts else parts
            exito, mensaje = asyncio.run(verificar_codigo_telethon(username, code))
            bot.editMessageText(message, mensaje, parse_mode='html')
            
            # Si fue exitoso, iniciar la escucha del canal
            if exito:
                iniciar_listener_usuario(username)
            return

        if '/status_canal' in msgText:
            session_file = f'sesion_{username}.session'
            if os.path.exists(session_file):
                bot.editMessageText(message, "🟢 <b>Conectado al canal</b>\n✅ La autenticación está activa.", parse_mode='html')
            else:
                bot.editMessageText(message, "🔴 <b>No conectado</b>\n❌ Usa /login para autenticarte.", parse_mode='html')
            return

        if '/logout' in msgText:
            session_file = f'sesion_{username}.session'
            if os.path.exists(session_file):
                try:
                    os.remove(session_file)
                    bot.editMessageText(message, "✅ <b>Sesión cerrada</b>\nLa sesión de Telethon ha sido eliminada.", parse_mode='html')
                except:
                    bot.editMessageText(message, "❌ <b>Error al cerrar sesión</b>", parse_mode='html')
            else:
                bot.editMessageText(message, "ℹ️ <b>No hay sesión activa</b>", parse_mode='html')
            return

        # ============================================
        # COMANDOS DE USUARIO (TU CÓDIGO ORIGINAL)
        # ============================================

        if '/start' in msgText:
            if username.lower() == ADMIN_USERNAME.lower():
                start_msg = f"""
👑 <b>Usuario Administrador</b>

👤 <b>Usuario:</b> <b>@{username}</b>
☁️ <b>Nube actual:</b> <code>{user_info['moodle_host']}</code>
⚖️ <b>Límite:</b> <b>{user_info['zips']} MB</b>

📱 <b>Autenticación con Telethon:</b>
/login +53XXXXXXXXX - <b>Iniciar sesión</b>
/code 12345 - <b>Verificar código</b>
/status_canal - <b>Estado de conexión</b>
/logout - <b>Cerrar sesión</b>

🔧 <b>Comandos principales:</b>
/admin - <b>Panel de administración</b>
/status - <b>Estado de las nubes 🟢/🔴</b>
/procesos - <b>Procesos en tiempo real 🚀</b>
"""
            else:
                start_msg = f"""
👤 <b>Usuario Regular</b>

👤 <b>Usuario:</b> <b>@{username}</b>
☁️ <b>Nube actual:</b> <code>{user_info['moodle_host']}</code>
⚖️ <b>Límite:</b> <b>{user_info['zips']} MB</b>

📱 <b>Autenticación con Telethon:</b>
/login +53XXXXXXXXX - <b>Iniciar sesión</b>
/code 12345 - <b>Verificar código</b>
/status_canal - <b>Estado de conexión</b>
/logout - <b>Cerrar sesión</b>

🔧 <b>Tus comandos:</b>
/start - <b>Ver esta información</b>
/cambiar - <b>Cambiar de nube 🔄</b>
/status - <b>Estado de tu nube 🟢/🔴</b>
/files - <b>Ver tus evidencias</b>
/txt_X - <b>Ver TXT de evidencia X</b>
/del_X - <b>Eliminar evidencia X</b>
/delall - <b>Eliminar tus evidencias</b>
/mystats - <b>Ver tus estadísticas</b>
                """
            
            bot.editMessageText(message, start_msg, parse_mode='html')
            send_sticker(chat_id, "CAACAgEAAxkBAAIoVGqA9obyhoMJe62uOFPzvoFk6vwpAAK7BgACnFgJROtfXZ-KKr1vPQQ")
            return

        # ============================================
        # PROCESAR ENLACES (TU CÓDIGO ORIGINAL)
        # ============================================

        if 'http' in msgText:
            url = msgText
            file_size = 0
            filename = url.split('/')[-1] or "Desconocido"
            
            # ... (tu código original para procesar enlaces) ...
            bot.editMessageText(message, f'<b>📥 Procesando enlace: {filename}</b>', parse_mode='html')
            ddl(update, bot, message, url, file_name='', thread=thread, jdb=jdb)
            return

        # ============================================
        # RESPUESTA POR DEFECTO
        # ============================================

        bot.editMessageText(message, '<b>➲ Comando no reconocido. Usa /start para ver los comandos disponibles.</b>', parse_mode='html')
            
    except Exception as ex:
        print(f"Error en onmessage: {ex}")
        print(traceback.format_exc())

# ==============================
# FUNCIÓN PRINCIPAL main
# ==============================

def main():
    # ====== BOT PRINCIPAL ======
    bot = ObigramClient(BOT_TOKEN)
    bot.onMessage(onmessage)
    
    # ====== PROCESADOR PERIÓDICO ======
    procesador_thread = threading.Thread(target=procesar_mensajes_periodicamente, daemon=True)
    procesador_thread.start()
    print("✅ Procesador periódico iniciado (cada 5 minutos)")
    
    print("🤖 Bot iniciado. Usa /login +53XXXXXXXXX para autenticarte.")
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error en main: {e}")
        main()