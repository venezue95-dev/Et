from pyobigram.utils import sizeof_fmt, get_file_size, createID, nice_time
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

# FIXED CONFIGURATION IN CODE
BOT_TOKEN = "8340084935:AAHLn3ftkhaJg9KyDgtL1ely4vo-1DlFyqM"

# ADMINISTRATOR CONFIGURATION
ADMIN_USERNAME = "Eliel_21"
ADMIN_CHAT_ID = 7363341763  # Tu ID
LOG_GROUP_ID = -1004295272245  # ID del grupo para notificaciones de enlaces, archivos y txts

# VARIABLES GLOBALES DE CONTROL
MAINTENANCE_MODE = False
BANNED_USERS = set()
REMOVED_USERS = set()  # Conjunto para usuarios quitados que anula la preconfiguración estática
ACTIVE_PROCESSES = {}  # Diccionario para rastrear procesos activos en tiempo real (descargas, compresiones, preparando, subidas)
ACTIVE_STATUS_CHECKS = set()  # Conjunto para evitar múltiples verificaciones simultáneas de estado
CHANGING_CLOUD_USERS = set()  # Conjunto para usuarios que están en proceso de elegir nube con /cambiar

# CUBA TIMEZONE
try:
    CUBA_TZ = pytz.timezone('America/Havana')
except:
    CUBA_TZ = None

# SEPARATOR FOR USER EVIDENCES
USER_EVIDENCE_MARKER = " "  # Space as separator

# LISTA DISPONIBLE DE NUBES (1 al 7) - Soporta: 'evidence', 'draft' o 'blog'
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
        "moodle_user": "webmaster",
        "moodle_password": "Adminprincipal2216..",
        "zips": 99,
        "uploadtype": "draft",
        "proxy": "",
        "tokenize": 0
    },
    {
        "cloudtype": "moodle",
        "moodle_host": "https://cursos.ucf.edu.cu/",
        "moodle_repo_id": 4,
        "moodle_user": "eliel2216",
        "moodle_password": "Et543210.",
        "zips": 49,
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

# PRE-CONFIGURACIÓN DE USUARIOS
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
# SISTEMA DE CACHÉ PARA OPTIMIZACIÓN
# ==============================

class CloudCache:
    """Sistema de caché para evitar refrescos innecesarios"""
    def __init__(self, ttl_seconds=30):
        self.cache = {}
        self.ttl = ttl_seconds
        self.last_refresh = {}
        self.last_full_refresh = None
    
    def should_refresh(self, cloud_name=None):
        if cloud_name is None:
            if self.last_full_refresh is None:
                return True
            elapsed = (datetime.datetime.now() - self.last_full_refresh).total_seconds()
            return elapsed > self.ttl
        
        if cloud_name not in self.last_refresh:
            return True
        elapsed = (datetime.datetime.now() - self.last_refresh[cloud_name]).total_seconds()
        return elapsed > self.ttl
    
    def update_cache(self, cloud_name, data):
        self.cache[cloud_name] = data
        self.last_refresh[cloud_name] = datetime.datetime.now()
    
    def update_full_cache(self, data):
        self.cache = data.copy()
        self.last_full_refresh = datetime.datetime.now()
    
    def get_cache(self, cloud_name):
        return self.cache.get(cloud_name)
    
    def clear_cache(self):
        self.cache = {}
        self.last_refresh = {}
        self.last_full_refresh = None

cloud_cache = CloudCache(ttl_seconds=30)

def get_cuba_time():
    if CUBA_TZ:
        cuba_time = datetime.datetime.now(CUBA_TZ)
    else:
        cuba_time = datetime.datetime.now()
    return cuba_time

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
    """Formatea bytes a KB, MB o GB automáticamente sin decimales .0 innecesarios"""
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

# ==============================
# FUNCIONES PARA REACCIONES Y STICKERS
# ==============================
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
        payload = {
            "chat_id": chat_id,
            "sticker": sticker_id
        }
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Error al enviar sticker: {e}")

# ==============================
# SISTEMA DE ESTADÍSTICAS EN MEMORIA Y CONTROL DIARIO
# ==============================

class MemoryStats:
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        self.stats = {
            'total_uploads': 0,
            'total_deletes': 0,
            'total_size_uploaded': 0
        }
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
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'daily_size': 0,
                'last_date': current_date,
                'last_activity': format_cuba_datetime()
            }
    
    def log_upload(self, username, filename, file_size, moodle_host):
        try:
            file_size = int(file_size)
        except:
            file_size = 0
        
        self.check_and_update_daily_reset(username)
        
        self.stats['total_uploads'] += 1
        self.stats['total_size_uploaded'] += file_size
        
        self.user_stats[username]['uploads'] += 1
        self.user_stats[username]['total_size'] += file_size
        self.user_stats[username]['daily_size'] += file_size
        self.user_stats[username]['last_activity'] = format_cuba_datetime()
        
        log_entry = {
            'timestamp': format_cuba_datetime(),
            'username': username,
            'filename': filename,
            'file_size_bytes': file_size,
            'file_size_formatted': format_file_size(file_size),
            'moodle_host': moodle_host
        }
        self.upload_logs.append(log_entry)
        
        if len(self.upload_logs) > 300:
            self.upload_logs.pop(0)
        
        return True
    
    def log_delete(self, username, filename, evidence_name, moodle_host):
        self.stats['total_deletes'] += 1
        self.check_and_update_daily_reset(username)
        
        self.user_stats[username]['deletes'] += 1
        self.user_stats[username]['last_activity'] = format_cuba_datetime()
        
        log_entry = {
            'timestamp': format_cuba_datetime(),
            'username': username,
            'filename': filename,
            'evidence_name': evidence_name,
            'moodle_host': moodle_host,
            'type': 'delete'
        }
        self.delete_logs.append(log_entry)
        
        if len(self.delete_logs) > 300:
            self.delete_logs.pop(0)
        
        return True
    
    def log_delete_all(self, username, deleted_evidences, deleted_files, moodle_host):
        self.stats['total_deletes'] += deleted_files
        self.check_and_update_daily_reset(username)
        
        self.user_stats[username]['deletes'] += deleted_files
        self.user_stats[username]['last_activity'] = format_cuba_datetime()
        
        log_entry = {
            'timestamp': format_cuba_datetime(),
            'username': username,
            'action': 'delete_all',
            'deleted_evidences': deleted_evidences,
            'deleted_files': deleted_files,
            'moodle_host': moodle_host,
            'type': 'delete_all'
        }
        self.delete_logs.append(log_entry)
        
        if len(self.delete_logs) > 300:
            self.delete_logs.pop(0)
        
        return True
    
    def get_user_stats(self, username):
        self.check_and_update_daily_reset(username)
        if username in self.user_stats:
            return self.user_stats[username]
        return None
    
    def get_all_stats(self):
        return self.stats
    
    def get_all_users(self):
        return self.user_stats
    
    def get_recent_uploads(self, limit=10):
        return self.upload_logs[-limit:][::-1] if self.upload_logs else []
    
    def get_recent_deletes(self, limit=10):
        return self.delete_logs[-limit:][::-1] if self.delete_logs else []
    
    def has_any_data(self):
        return len(self.upload_logs) > 0 or len(self.delete_logs) > 0
    
    def clear_all_data(self):
        self.reset_stats()
        return "<b>✅ Todos los datos han sido eliminados</b>"

memory_stats = MemoryStats()

def expand_user_groups():
    expanded = {}
    for user_group, config in PRE_CONFIGURATED_USERS.items():
        users = [u.strip() for u in user_group.split(',')]
        for user in users:
            expanded[user] = config.copy()
    return expanded

# ==============================
# FUNCIÓN PARA VERIFICAR ESTADO DE UNA NUBE INDIVIDUAL
# ==============================
def check_single_cloud(cloud_config):
    moodle_host = cloud_config.get('moodle_host', '')
    moodle_user = cloud_config.get('moodle_user', '')
    moodle_password = cloud_config.get('moodle_password', '')
    moodle_repo_id = cloud_config.get('moodle_repo_id', '')
    proxy = cloud_config.get('proxy', '')
    
    short_name = moodle_host.replace('https://', '').replace('http://', '').strip('/')
    is_online = False
    try:
        proxy_parsed = ProxyCloud.parse(proxy) if proxy else None
        requests.get(moodle_host, timeout=5, proxies=proxy_parsed, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        
        client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
        if client.login():
            is_online = True
            try:
                client.logout()
            except:
                pass
    except Exception:
        is_online = False
        
    return {
        'host': short_name,
        'url': moodle_host,
        'online': is_online
    }

# ==============================
# TRACKER DE PROCESOS ACTIVOS
# ==============================
def update_process(thread_id, username, filename, action, current, total):
    try:
        current = int(current or 0)
        total = int(total or 0)
        percent = (current / total) * 100 if total > 0 else 0
        if percent > 100: percent = 100
        
        fmt_percent = f"{int(percent)}%" if percent.is_integer() else f"{percent:.1f}%"
        
        ACTIVE_PROCESSES[thread_id] = {
            'user': username,
            'file': filename,
            'action': action,
            'percent': fmt_percent,
            'last_update': time.time()
        }
    except: pass

def clean_process(thread_id):
    if thread_id in ACTIVE_PROCESSES:
        del ACTIVE_PROCESSES[thread_id]

# ==============================
# FUNCIÓN PARA DIVIDIR MENSAJES LARGOS
# ==============================
def send_long_message(bot, chat_id, text, original_message=None, parse_mode='html'):
    MAX_LEN = 4000
    
    if len(text) <= MAX_LEN:
        if original_message:
            bot.editMessageText(original_message, text, parse_mode=parse_mode)
        else:
            bot.sendMessage(chat_id, text, parse_mode=parse_mode)
        return

    lines = text.split('\n')
    current_msg = ""
    messages_to_send = []

    for line in lines:
        if len(current_msg) + len(line) + 1 > MAX_LEN:
            messages_to_send.append(current_msg)
            current_msg = line + '\n'
        else:
            current_msg += line + '\n'
    
    if current_msg:
        messages_to_send.append(current_msg)

    if original_message:
        bot.editMessageText(original_message, messages_to_send[0], parse_mode=parse_mode)
    else:
        bot.sendMessage(chat_id, messages_to_send[0], parse_mode=parse_mode)
        
    for msg_part in messages_to_send[1:]:
        time.sleep(0.5)
        bot.sendMessage(chat_id, msg_part, parse_mode=parse_mode)

def downloadFile(downloader, filename, currentBits, totalBits, speed, time, args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        username = args[3] if len(args) > 3 else "Desconocido"
        if thread.getStore('stop'):
            downloader.stop()
            raise Exception("Tarea detenida por mantenimiento o cancelación")
        
        update_process(thread.id, username, filename, '📥 Descargando', currentBits, totalBits)
        
        downloadingInfo = infos.createDownloading(filename, totalBits, currentBits, speed, time, tid=thread.id)
        bot.editMessageText(message, downloadingInfo, parse_mode='html')
    except Exception as ex: 
        raise ex

def uploadFile(filename, currentBits, totalBits, speed, time, args):
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
        uploadingInfo = infos.createUploading(filename, totalBits, currentBits, speed, time, originalfile, tid=tid_str)
        bot.editMessageText(message, uploadingInfo, parse_mode='html')
    except Exception as ex: 
        raise ex

# =========================================================
# SUBIDA COMPLETA: EVIDENCE, DRAFT Y BLOG
# =========================================================
def processUploadFiles(filename, filesize, files, update, bot, message, thread=None, jdb=None):
    try:
        prep_msg = '<b>⬆️ Preparando para subir ☁ ●●○</b>'
        if thread:
            prep_msg += f"\n\n/cancel_{thread.id}"
        bot.editMessageText(message, prep_msg, parse_mode='html')
        
        username = update.message.sender.username
        if thread:
            if thread.getStore('stop'):
                raise Exception("Tarea detenida por mantenimiento o cancelación")
            update_process(thread.id, username, os.path.basename(str(filename)), '⬆️ Preparando para subir', 0, 100)
            
        evidence = None
        fileid = None
        user_info = jdb.get_user(username)
        proxy = ProxyCloud.parse(user_info['proxy']) if user_info and user_info.get('proxy') else None
        
        # VERIFICACIÓN RÁPIDA DE CONECTIVIDAD
        try:
            test_url = user_info['moodle_host']
            requests.get(test_url, timeout=6, proxies=proxy, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        except requests.exceptions.Timeout:
            if thread and thread.getStore('stop'):
                return None
            clean_host = user_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/') if user_info else "Desconocido"
            filename_fail = os.path.basename(str(filename)) if filename else "Desconocido"
            error_desc = "<b>Tiempo de espera agotado. El servidor tardó demasiado en responder.</b>"
            
            error_msg_user = (
                f"<b>❌ ¡Error de conexión con Moodle (Timeout)!</b>\n\n"
                f"☁️ <b>Nube:</b> <code>{clean_host}</code>\n"
                f"⚠️ <b>Detalle:</b> {error_desc}\n\n"
                f"💡 <i>Usa /status para revisar el estado o /cambiar para elegir otra nube.</i>"
            )
            bot.editMessageText(message, error_msg_user, parse_mode='html')
            
            if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                try:
                    mensaje_log = (
                        f"<b>❌ ¡Error de Conexión (Timeout)!</b>\n\n"
                        f"👤 <b>Usuario:</b> <b>@{username}</b>\n"
                        f"📄 <b>Nombre:</b> <b>{filename_fail}</b>\n"
                        f"☁️ <b>Nube:</b> <code>{clean_host}</code>\n"
                        f"⚠️ <b>Detalle:</b> {error_desc}"
                    )
                    bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar Moodle caída al grupo: {e}")
            return "LOGIN_FAILED"
        except Exception as conn_err:
            if thread and thread.getStore('stop'):
                return None
            clean_host = user_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/') if user_info else "Desconocido"
            filename_fail = os.path.basename(str(filename)) if filename else "Desconocido"
            error_desc = "<b>La plataforma Moodle no responde (Servidor caído o inaccesible).</b>"
            
            error_msg_user = (
                f"<b>❌ ¡Error de conexión con Moodle (Servidor Caído)!</b>\n\n"
                f"☁️ <b>Nube:</b> <code>{clean_host}</code>\n"
                f"⚠️ <b>Detalle:</b> {error_desc}\n\n"
                f"💡 <i>Usa /status para revisar el estado o /cambiar para elegir otra nube.</i>"
            )
            bot.editMessageText(message, error_msg_user, parse_mode='html')
            
            if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                try:
                    mensaje_log = (
                        f"<b>❌ ¡Error de Conexión (Servidor Caído)!</b>\n\n"
                        f"👤 <b>Usuario:</b> <b>@{username}</b>\n"
                        f"📄 <b>Nombre:</b> <b>{filename_fail}</b>\n"
                        f"☁️ <b>Nube:</b> <code>{clean_host}</code>\n"
                        f"⚠️ <b>Detalle:</b> {error_desc}"
                    )
                    bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar Moodle caída al grupo: {e}")
            return "LOGIN_FAILED"
        
        client = MoodleClient(user_info['moodle_user'],
                              user_info['moodle_password'],
                              user_info['moodle_host'],
                              user_info['moodle_repo_id'],
                              proxy=proxy)
        
        if thread and thread.getStore('stop'):
            return None

        loged = client.login()
        if thread and thread.getStore('stop'):
            return None

        if loged:
            upload_type = user_info.get('uploadtype', 'evidence')
            originalfile = filename if len(files) > 1 else ''
            tokenize = user_info.get('tokenize', 0) != 0
            resplist = []

            # 1. MODO DRAFT
            if upload_type == 'draft':
                for f in files:
                    if thread and thread.getStore('stop'):
                        raise Exception("Tarea detenida por mantenimiento o cancelación")
                    resp = None
                    iter = 0
                    while resp is None:
                        if thread and thread.getStore('stop'):
                            raise Exception("Tarea detenida por mantenimiento o cancelación")
                        _, resp = client.upload_file_draft(f, progressfunc=uploadFile, args=(bot, message, originalfile, thread, username), tokenize=tokenize)
                        iter += 1
                        if iter >= 10:
                            break
                    resplist.append(resp)
                    os.unlink(f)
                return resplist

            # 2. MODO BLOG
            elif upload_type == 'blog':
                itemid = None
                uploaded_info = []
                for f in files:
                    if thread and thread.getStore('stop'):
                        raise Exception("Tarea detenida por mantenimiento o cancelación")
                    resp = None
                    iter = 0
                    while resp is None:
                        if thread and thread.getStore('stop'):
                            raise Exception("Tarea detenida por mantenimiento o cancelación")
                        itemid, resp = client.upload_file_blog(f, itemid=itemid, progressfunc=uploadFile, args=(bot, message, originalfile, thread, username), tokenize=tokenize)
                        iter += 1
                        if iter >= 10:
                            break
                    uploaded_info.append(resp)
                    os.unlink(f)
                
                entryid = client.createBlog(os.path.basename(str(filename)), itemid)
                
                for info in uploaded_info:
                    if info:
                        fname = info.get('filename', os.path.basename(str(filename)))
                        ctx_id = info.get('ctx_id', '1')
                        if entryid and client.userdata and 'token' in client.userdata:
                            direct_url = f"{client.path}webservice/pluginfile.php/{ctx_id}/blog/post/{entryid}/{fname}?token={client.userdata['token']}"
                        else:
                            direct_url = f"{client.path}pluginfile.php/{ctx_id}/blog/post/{entryid}/{fname}"
                        
                        if tokenize and client.userdata:
                            direct_url = client.host_tokenize + S5Crypto.encrypt(direct_url) + '/' + client.userdata['s5token']
                        
                        resplist.append({'filename': fname, 'url': direct_url})
                return resplist

            # 3. MODO EVIDENCE
            else:
                evidences = client.getEvidences()
                original_evidname = str(filename).split('.')[0]
                internal_evidname = f"{original_evidname}{USER_EVIDENCE_MARKER}{username}"
                
                for evid in evidences:
                    if evid['name'] == internal_evidname:
                        evidence = evid
                        break
                if evidence is None:
                    evidence = client.createEvidence(internal_evidname)

                for f in files:
                    if thread and thread.getStore('stop'):
                        raise Exception("Tarea detenida por mantenimiento o cancelación")
                    resp = None
                    iter = 0
                    while resp is None:
                        if thread and thread.getStore('stop'):
                            raise Exception("Tarea detenida por mantenimiento o cancelación")
                        fileid, resp = client.upload_file(f, evidence, fileid, progressfunc=uploadFile, args=(bot, message, originalfile, thread, username), tokenize=tokenize)
                        iter += 1
                        if iter >= 10:
                            break
                    resplist.append(resp)
                    os.unlink(f)
                
                if thread and thread.getStore('stop'):
                    raise Exception("Tarea detenida por mantenimiento o cancelación")

                try:
                    client.saveEvidence(evidence)
                except:
                    pass
                return resplist
        else:
            if thread and thread.getStore('stop'):
                return None
            
            clean_host = user_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/') if user_info else "Desconocido"
            filename_fail = os.path.basename(str(filename)) if filename else "Desconocido"
            error_desc = "<b>Error en la autenticación o credenciales incorrectas.</b>"
            error_msg_user = (
                f"<b>❌ ¡Error de Autenticación en Moodle!</b>\n\n"
                f"☁️ <b>Nube:</b> <code>{clean_host}</code>\n"
                f"⚠️ <b>Detalle:</b> {error_desc}"
            )
            bot.editMessageText(message, error_msg_user, parse_mode='html')
            
            if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                try:
                    mensaje_log = (f"<b>❌ ¡Error de Autenticación en Moodle!</b>\n\n"
                                   f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                                   f"<b>📄 Nombre:</b> <b>{filename_fail}</b>\n"
                                   f"<b>☁️ Nube:</b> <code>{clean_host}</code>\n"
                                   f"<b>⚠️ Detalle:</b> {error_desc}")
                    bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar error de página al grupo: {e}")
            return "LOGIN_FAILED"
    except Exception as ex:
        if thread and thread.getStore('stop'):
            try:
                bot.editMessageText(message, '<b>➲ Tarea cancelada ✗ </b>', parse_mode='html')
            except:
                pass
            return None

        error_detail = str(ex) if str(ex) else "Error desconocido en la subida"
        u_info = jdb.get_user(username) if jdb else None
        clean_host = u_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/') if u_info else "Desconocido"
        filename_fail = os.path.basename(str(filename)) if filename else "Desconocido"

        error_msg_user = (
            f"<b>❌ ¡Error en la subida!</b>\n\n"
            f"📄 <b>Nombre:</b> <b>{filename_fail}</b>\n"
            f"☁️ <b>Nube:</b> <code>{clean_host}</code>\n"
            f"⚠️ <b>Detalle:</b> <b>Fallo en la subida del archivo: {error_detail}</b>"
        )
        bot.editMessageText(message, error_msg_user, parse_mode='html')

        if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
            try:
                mensaje_log = (f"<b>❌ ¡Error en la subida!</b>\n\n"
                               f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                               f"<b>📄 Nombre:</b> <b>{filename_fail}</b>\n"
                               f"<b>☁️ Nube:</b> <code>{clean_host}</code>\n"
                               f"<b>⚠️ Detalle:</b> <b>Fallo en la subida del archivo: {error_detail}</b>")
                bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
            except Exception as e:
                print(f"Error al notificar error de subida al grupo: {e}")
        return None

def processFile(update, bot, message, file, thread=None, jdb=None):
    phase = "procesamiento"
    findex = 0
    try:
        if thread and thread.getStore('stop'):
            raise Exception("Tarea detenida por mantenimiento o cancelación")
            
        file_size = get_file_size(file)
        getUser = jdb.get_user(update.message.sender.username)
        max_file_size = 1024 * 1024 * getUser['zips']
        file_upload_count = 0
        client = None
        username = update.message.sender.username
        
        if file_size > max_file_size:
            phase = "compresión"
            compresingInfo = infos.createCompresing(file, file_size, max_file_size)
            if thread:
                compresingInfo = compresingInfo.strip() + f"\n\n/cancel_{thread.id}"
            bot.editMessageText(message, compresingInfo, parse_mode='html')
            
            if thread:
                if thread.getStore('stop'):
                    raise Exception("Tarea detenida por mantenimiento o cancelación")
                update_process(thread.id, username, os.path.basename(file), '🗜️ Comprimiendo', 0, 100)
            
            zipname = str(file).split('.')[0] + createID()
            mult_file = zipfile.MultiFile(zipname, max_file_size)
            zip = zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED)
            
            if thread and thread.getStore('stop'):
                zip.close()
                mult_file.close()
                raise Exception("Tarea detenida por mantenimiento o cancelación")
            
            arcname = os.path.basename(file)
            zinfo = zipfile.ZipInfo.from_file(file, arcname)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            
            with zip.open(zinfo, 'w') as dest, open(file, 'rb') as src:
                while True:
                    if thread and thread.getStore('stop'):
                        dest.close()
                        zip.close()
                        mult_file.close()
                        raise Exception("Tarea detenida por mantenimiento o cancelación")
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dest.write(chunk)
            
            if thread and thread.getStore('stop'):
                zip.close()
                mult_file.close()
                raise Exception("Tarea detenida por mantenimiento o cancelación")
                
            zip.close()
            mult_file.close()
            
            if thread and thread.getStore('stop'):
                raise Exception("Tarea detenida por mantenimiento o cancelación")

            phase = "subida"
            client = processUploadFiles(file, file_size, mult_file.files, update, bot, message, thread=thread, jdb=jdb)
            try:
                os.unlink(file)
            except: pass
            file_upload_count = len(mult_file.files)
        else:
            phase = "subida"
            client = processUploadFiles(file, file_size, [file], update, bot, message, thread=thread, jdb=jdb)
            file_upload_count = 1
        
        if thread and thread.getStore('stop'):
            raise Exception("Tarea detenida por mantenimiento o cancelación")

        files = []
        if client == "LOGIN_FAILED":
            return
            
        if client:
            upload_type = getUser.get('uploadtype', 'evidence')
            
            # --- PARSEO DE ENLACES PARA DRAFT Y BLOG ---
            if upload_type in ['draft', 'blog']:
                for item in client:
                    if item and 'url' in item:
                        url = item['url']
                        if '?forcedownload=1' in url:
                            url = url.replace('?forcedownload=1', '')
                        elif '&forcedownload=1' in url:
                            url = url.replace('&forcedownload=1', '')
                        if '&token=' in url and '?' not in url:
                            url = url.replace('&token=', '?token=', 1)
                        files.append({'name': item.get('filename', os.path.basename(file)), 'directurl': url})
                findex = 0
            
            # --- PARSEO DE ENLACES PARA EVIDENCE ---
            else:
                original_evidname = str(file).split('.')[0]
                visible_evidname = original_evidname
                internal_evidname = f"{original_evidname}{USER_EVIDENCE_MARKER}{username}"
                
                try:
                    proxy = ProxyCloud.parse(getUser['proxy']) if getUser.get('proxy') else None
                    moodle_client = MoodleClient(getUser['moodle_user'],
                                                 getUser['moodle_password'],
                                                 getUser['moodle_host'],
                                                 getUser['moodle_repo_id'],
                                                 proxy=proxy)
                    if moodle_client.login():
                        evidence_index = -1
                        for attempt in range(3):
                            evidences = moodle_client.getEvidences()
                            for idx, ev in enumerate(evidences):
                                if ev['name'] == internal_evidname:
                                    files = ev.get('files', [])
                                    if files:
                                        evidence_index = idx
                                        break
                            if files:
                                break
                            time.sleep(2)
                        
                        if files:
                            for i in range(len(files)):
                                url = files[i]['directurl']
                                if '?forcedownload=1' in url:
                                    url = url.replace('?forcedownload=1', '')
                                elif '&forcedownload=1' in url:
                                    url = url.replace('&forcedownload=1', '')
                                if '&token=' in url and '?' not in url:
                                    url = url.replace('&token=', '?token=', 1)
                                files[i]['directurl'] = url
                        
                        moodle_client.logout()
                        findex = evidence_index if evidence_index != -1 else 0
                except Exception as e:
                    print(f"Error obteniendo índice de evidencia: {e}")
                    findex = 0
            
            if thread and thread.getStore('stop'):
                raise Exception("Tarea detenida por mantenimiento o cancelación")

            bot.deleteMessage(message.chat.id, message.message_id)
            finishInfo = infos.createFinishUploading(file, file_size, max_file_size, file_upload_count, file_upload_count, findex)
            filesInfo = infos.createFileMsg(file, files)
            
            extra_msg = ""
            if getUser:
                host = getUser.get('moodle_host', '').lower()
                if 'fundacion.uh.cu' in host:
                    m_user = getUser.get('moodle_user', '')
                    m_pass = getUser.get('moodle_password', '')
                    extra_msg = f"\n<b>⚠️ Debes iniciar sesión con la cuenta en la plataforma para poder descargar:</b>\n\n<b>👤 Usuario:</b> <code>{m_user}</code>\n<b>🔑 Contraseña:</b> <code>{m_pass}</code>\n"

            bot.sendMessage(message.chat.id, finishInfo + '\n' + extra_msg + '\n' + filesInfo, parse_mode='html')
            
            filename_clean = os.path.basename(file)
            memory_stats.log_upload(
                username=username,
                filename=filename_clean,
                file_size=file_size,
                moodle_host=getUser['moodle_host']
            )

            if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                try:
                    clean_host = getUser['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                    mensaje_log = (f"<b>✅ ¡Subida completada!</b>\n\n"
                                   f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                                   f"<b>📄 Nombre:</b> <b>{filename_clean}</b>\n"
                                   f"<b>⚖️ Peso:</b> <b>{format_file_size(file_size)}</b>\n"
                                   f"<b>☁️ Nube:</b> <code>{clean_host}</code>")
                    bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar subida al grupo: {e}")
            
            if len(files) > 0:
                txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
                send_to_group_flag = False if username.lower() == ADMIN_USERNAME.lower() else True
                sendTxt(txtname, files, update, bot, send_to_group=send_to_group_flag, user_info=getUser)
            
            send_sticker(message.chat.id, "CAACAgEAAxkBAAIoXGqA9r31O2plFhlz_RG3tuYEg-_JAAK6BgACnFgJRDiBixe0VxapPQQ")
        else:
            if not (thread and thread.getStore('stop')):
                clean_host = getUser['moodle_host'].replace('https://', '').replace('http://', '').strip('/') if getUser else "Desconocido"
                bot.editMessageText(message, f"<b>❌ ¡Error de Autenticación en Moodle!</b>\n\n<b>☁️ Nube:</b> <code>{clean_host}</code>", parse_mode='html')
    except Exception as ex:
        if thread and thread.getStore('stop'):
            try:
                bot.editMessageText(message, '<b>➲ Tarea cancelada ✗ </b>', parse_mode='html')
            except: pass
            return

        error_detail = str(ex) if str(ex) else "Error desconocido"
        clean_host = getUser['moodle_host'].replace('https://', '').replace('http://', '').strip('/') if getUser else "Desconocido"
        filename_fail = os.path.basename(file) if file else "Desconocido"
        bot.editMessageText(message, f"<b>❌ ¡Error en la {phase}!</b>\n\n<b>📄 Nombre:</b> <b>{filename_fail}</b>\n<b>☁️ Nube:</b> <code>{clean_host}</code>\n<b>⚠️ Detalle:</b> <b>{error_detail}</b>", parse_mode='html')
    finally:
        if thread:
            clean_process(thread.id)

def ddl(update, bot, message, url, file_name='', thread=None, jdb=None):
    try:
        downloader = Downloader()
        username = update.message.sender.username
        file = None
        retries = 3
        for attempt in range(retries):
            try:
                if thread and thread.getStore('stop'):
                    break
                if attempt > 0:
                    try:
                        bot.editMessageText(message, f"<b>⚠️ Error de conexión, reintentando... (Intento {attempt+1}/{retries})</b>", parse_mode='html')
                    except: pass
                    if thread:
                        update_process(thread.id, username, "Descarga", f'🔄 Reintentando ({attempt+1}/{retries})', 0, 100)
                
                file = downloader.download_url(url, progressfunc=downloadFile, args=(bot, message, thread, username))
                if file:
                    if file.endswith('.unknown') and file_name and '.' in file_name and not file_name.endswith('.unknown'):
                        new_file = os.path.splitext(file)[0] + '_' + file_name
                        try:
                            os.rename(file, new_file)
                            file = new_file
                        except: pass
                    break
            except Exception as ex:
                error_detail = str(ex) if str(ex) else "Error desconocido"
                if attempt == retries - 1:
                    u_info = jdb.get_user(username) if jdb else None
                    clean_host = u_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/') if u_info else "Desconocido"
                    filename_fail = file_name or url.split('/')[-1] or "Desconocido"

                    error_msg_user = (
                        f"<b>❌ ¡Error en la descarga!</b>\n\n"
                        f"<b>📄 Nombre:</b> <b>{filename_fail}</b>\n"
                        f"<b>☁️ Nube:</b> <code>{clean_host}</code>\n"
                        f"<b>⚠️ Detalle:</b> <b>Fallo en la descarga tras {retries} intentos: {error_detail}</b>"
                    )
                    try:
                        bot.editMessageText(message, error_msg_user, parse_mode='html')
                    except: pass
                    
                    if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                        try:
                            mensaje_log = (f"<b>❌ ¡Error en la descarga!</b>\n\n"
                                           f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                                           f"<b>📄 Nombre:</b> <b>{filename_fail}</b>\n"
                                           f"<b>☁️ Nube:</b> <code>{clean_host}</code>\n"
                                           f"<b>⚠️ Detalle:</b> <b>Fallo en la descarga del enlace: {error_detail}</b>")
                            bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                        except Exception as e:
                            print(f"Error al notificar error de descarga al grupo: {e}")
                    raise ex
                time.sleep(3)
        
        if not downloader.stoping:
            if file:
                processFile(update, bot, message, file, thread=thread, jdb=jdb)
            else:
                bot.editMessageText(message, '<b>➥ Error en la descarga ✗</b>', parse_mode='html')
    except Exception as ex:
        if thread and thread.getStore('stop'):
            try:
                bot.editMessageText(message, '<b>➲ Tarea cancelada ✗ </b>', parse_mode='html')
            except: pass
        else:
            print(f"Error en ddl: {ex}")
    finally:
        if thread:
            clean_process(thread.id)

def sendTxt(name, files, update, bot, send_to_group=False, user_info=None):
    txt = open(name, 'w')
    
    for i, f in enumerate(files):
        url = f['directurl']
        
        if '?forcedownload=1' in url:
            url = url.replace('?forcedownload=1', '')
        elif '&forcedownload=1' in url:
            url = url.replace('&forcedownload=1', '')
        
        if '&token=' in url and '?' not in url:
            url = url.replace('&token=', '?token=', 1)
        
        txt.write(url)
        
        if i < len(files) - 1:
            txt.write('\n\n')
    
    txt.close()
    
    bot.sendFile(update.message.chat.id, name)
    
    if send_to_group and LOG_GROUP_ID != 0:
        try:
            bot.sendFile(LOG_GROUP_ID, name)
        except Exception as e:
            print(f"Error enviando txt al grupo: {e}")
            
    os.unlink(name)

def initialize_database(jdb):
    expanded_users = expand_user_groups()
    database_updated = False
    
    for username, config in expanded_users.items():
        if username.lower() in {r.lower() for r in REMOVED_USERS}:
            continue
        existing_user = jdb.get_user(username)
        
        if existing_user is None:
            jdb.create_user(username)
            user_data = jdb.get_user(username)
            for key, value in config.items():
                user_data[key] = value
            jdb.save_data_user(username, user_data)
            database_updated = True
    
    if database_updated:
        jdb.save()

def delete_message_after_delay(bot, chat_id, message_id, delay=8):
    def delete():
        time.sleep(delay)
        try:
            bot.deleteMessage(chat_id, message_id)
        except Exception as e:
            print(f"Error al eliminar mensaje: {e}")
    
    thread = threading.Thread(target=delete)
    thread.daemon = True
    thread.start()

def get_all_cloud_evidences_fast(use_cache=True):
    if use_cache and not cloud_cache.should_refresh():
        cached_data = cloud_cache.get_cache('all_clouds')
        if cached_data:
            return cached_data
    
    all_evidences = []
    
    for user_group, cloud_config in PRE_CONFIGURATED_USERS.items():
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        if use_cache and not cloud_cache.should_refresh(moodle_host):
            cached_evidence = cloud_cache.get_cache(moodle_host)
            if cached_evidence:
                all_evidences.extend(cached_evidence)
                continue
        
        try:
            proxy_parsed = ProxyCloud.parse(proxy) if proxy else None
            requests.get(moodle_host, timeout=5, proxies=proxy_parsed, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
            
            client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
            
            if client.login():
                evidences = client.getEvidences()
                
                for evidence in evidences:
                    evidence_info = {
                        'cloud_name': moodle_host,
                        'cloud_user': moodle_user,
                        'evidence_name': evidence.get('name', 'Sin nombre'),
                        'files_count': len(evidence.get('files', [])),
                        'evidence_data': evidence,
                        'group_users': user_group.split(','),
                        'cloud_config': cloud_config
                    }
                    all_evidences.append(evidence_info)
                
                client.logout()
                if use_cache:
                    cloud_cache.update_cache(moodle_host, [ev for ev in all_evidences if ev['cloud_name'] == moodle_host])
            else:
                print(f"No se pudo conectar a {moodle_host}")
                
        except Exception as e:
            print(f"Error obteniendo evidencias de {moodle_host}: {str(e)}")
    
    if use_cache:
        cloud_cache.update_full_cache(all_evidences)
    
    return all_evidences

def delete_evidence_from_cloud(cloud_config, evidence):
    try:
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        proxy_parsed = ProxyCloud.parse(proxy) if proxy else None
        requests.get(moodle_host, timeout=5, proxies=proxy_parsed, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        
        client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
        
        if client.login():
            all_evidences = client.getEvidences()
            evidence_to_delete = None
            
            for ev in all_evidences:
                if ev.get('id') == evidence.get('id'):
                    evidence_to_delete = ev
                    break
            
            if evidence_to_delete:
                evidence_name = evidence_to_delete.get('name', '')
                files_count = len(evidence_to_delete.get('files', []))
                client.deleteEvidence(evidence_to_delete)
                client.logout()
                cloud_cache.clear_cache()
                return True, evidence_name, files_count
            else:
                client.logout()
                return False, "", 0
        else:
            return False, "", 0
            
    except Exception as e:
        return False, f"Error: {str(e)}", 0

def delete_all_evidences_from_cloud(cloud_config):
    try:
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        proxy_parsed = ProxyCloud.parse(proxy) if proxy else None
        requests.get(moodle_host, timeout=5, proxies=proxy_parsed, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        
        client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
        
        if client.login():
            all_evidences = client.getEvidences()
            deleted_count = 0
            total_files = 0
            
            for evidence in all_evidences:
                try:
                    files_count = len(evidence.get('files', []))
                    client.deleteEvidence(evidence)
                    deleted_count += 1
                    total_files += files_count
                except:
                    pass
            
            client.logout()
            cloud_cache.clear_cache()
            return True, deleted_count, total_files
        else:
            return False, 0, 0
            
    except Exception as e:
        return False, 0, 0

class AdminEvidenceManager:
    def __init__(self):
        self.current_list = []
        self.clouds_dict = {}
        self.last_update = None
    
    def refresh_data(self, force=False):
        if not force and not cloud_cache.should_refresh():
            return len(self.current_list)
        
        try:
            all_evidences = get_all_cloud_evidences_fast(use_cache=True)
            self.clouds_dict = {}
            
            for evidence in all_evidences:
                cloud_name = evidence['cloud_name']
                if cloud_name not in self.clouds_dict:
                    self.clouds_dict[cloud_name] = []
                self.clouds_dict[cloud_name].append(evidence)
            
            self.current_list = []
            cloud_index = 0
            for cloud_name, evidences in self.clouds_dict.items():
                for idx, evidence in enumerate(evidences):
                    self.current_list.append({
                        'cloud_idx': cloud_index,
                        'evid_idx': idx,
                        'cloud_name': cloud_name,
                        'evidence': evidence
                    })
            
            self.last_update = datetime.datetime.now()
            return len(self.current_list)
        except Exception as e:
            print(f"Error refrescando datos: {e}")
            return len(self.current_list)
    
    def get_evidence(self, cloud_idx, evid_idx):
        try:
            if cloud_idx is None or evid_idx is None:
                return None
                
            if cloud_idx < len(self.clouds_dict):
                cloud_name = list(self.clouds_dict.keys())[cloud_idx]
                if evid_idx < len(self.clouds_dict[cloud_name]):
                    return self.clouds_dict[cloud_name][evid_idx]
        except Exception as e:
            print(f"Error obteniendo evidencia: {e}")
        return None
    
    def get_txt_for_evidence(self, cloud_idx, evid_idx):
        evidence = self.get_evidence(cloud_idx, evid_idx)
        if evidence:
            try:
                cloud_config = evidence['cloud_config']
                evidence_data = evidence['evidence_data']
                
                moodle_host = cloud_config.get('moodle_host', '')
                moodle_user = cloud_config.get('moodle_user', '')
                moodle_password = cloud_config.get('moodle_password', '')
                moodle_repo_id = cloud_config.get('moodle_repo_id', '')
                proxy = cloud_config.get('proxy', '')
                
                proxy_parsed = ProxyCloud.parse(proxy) if proxy else None
                requests.get(moodle_host, timeout=5, proxies=proxy_parsed, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
                
                client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
                
                if client.login():
                    all_evidences = client.getEvidences()
                    current_evidence = None
                    
                    for ev in all_evidences:
                        if ev.get('id') == evidence_data.get('id'):
                            current_evidence = ev
                            break
                    
                    if current_evidence:
                        files = current_evidence.get('files', [])
                        
                        for i in range(len(files)):
                            url = files[i]['directurl']
                            if '?forcedownload=1' in url:
                                url = url.replace('?forcedownload=1', '')
                            elif '&forcedownload=1' in url:
                                url = url.replace('&forcedownload=1', '')
                            if '&token=' in url and '?' not in url:
                                url = url.replace('&token=', '?token=', 1)
                            files[i]['directurl'] = url
                        
                        client.logout()
                        return files
                    client.logout()
            except Exception as e:
                print(f"Error obteniendo TXT: {e}")
        return None
    
    def clear_cache(self):
        cloud_cache.clear_cache()
        self.current_list = []
        self.clouds_dict = {}
        self.last_update = None

admin_evidence_manager = AdminEvidenceManager()

def extract_one_param_simple(msgText, prefix):
    try:
        if prefix in msgText:
            parts = msgText.split('_')
            if prefix == '/adm_cloud_':
                return int(parts[2]) if len(parts) > 2 else None
            elif prefix == '/adm_wipe_':
                return int(parts[2]) if len(parts) > 2 else None
    except (ValueError, IndexError):
        return None
    return None

def extract_two_params_simple(msgText, prefix):
    try:
        if prefix in msgText:
            parts = msgText.split('_')
            if len(parts) > 3:
                param1 = int(parts[2])
                param2 = int(parts[3])
                return [param1, param2]
    except (ValueError, IndexError):
        return None
    return None

def show_updated_cloud(bot, message, cloud_idx):
    try:
        admin_evidence_manager.refresh_data(force=True)
        cloud_names = list(admin_evidence_manager.clouds_dict.keys())
        
        if cloud_idx < 0 or cloud_idx >= len(cloud_names):
            show_updated_all_clouds(bot, message)
            return
        
        cloud_name = cloud_names[cloud_idx]
        evidences = admin_evidence_manager.clouds_dict.get(cloud_name, [])
        
        if not evidences:
            short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
            empty_msg = f"""
<b>📭 Nube vacía</b>

<b>✅ Eliminación completa</b>
☁️ <b>Nube:</b> <code>{short_name}</code>

🎉 <b>¡Has eliminado todas las evidencias de esta nube!</b>

🔄 <b>Regresando a todas las nubes...</b>
            """
            bot.editMessageText(message, empty_msg, parse_mode='html')
            time.sleep(1.5)
            show_updated_all_clouds(bot, message)
            return
        
        short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
        
        list_msg = f"""
<b>📋 Nube actualizada</b>
☁️ <b>Nube:</b> <code>{short_name}</code>

"""
        for idx, evidence in enumerate(evidences):
            ev_name = evidence['evidence_name']
            clean_name = ev_name
            user_tags = []
            
            for user in evidence['group_users']:
                marker = f"{USER_EVIDENCE_MARKER}{user}"
                if marker in ev_name:
                    clean_name = ev_name.replace(marker, "").strip()
                    user_tags.append(f"@{user}")
            
            if user_tags:
                user_str = f" ({', '.join(user_tags[:2])})"
                if len(user_tags) > 2:
                    user_str = f" ({', '.join(user_tags[:2])}...)"
            else:
                user_str = ""
            
            list_msg += f"<b>{idx}.</b> <b>{clean_name[:35]}</b>"
            if len(clean_name) > 35:
                list_msg += "..."
            list_msg += f"<b>{user_str}</b>\n"
            list_msg += f"   📁 <b>Archivos:</b> <b>{evidence['files_count']}</b>\n"
            list_msg += f"   👁️ <b>Ver:</b> /adm_show_{cloud_idx}_{idx}\n"
            list_msg += f"   📄 <b>TXT:</b> /adm_fetch_{cloud_idx}_{idx}\n"
            list_msg += f"   🗑️ <b>Borrar:</b> /adm_delete_{cloud_idx}_{idx}\n\n"
        
        total_evidences = len(evidences)
        total_files = sum(e['files_count'] for e in evidences)
        
        list_msg += f"""
🔧 <b>Acciones masivas:</b>
/adm_wipe_{cloud_idx} - <b>Eliminación masiva</b>

📊 <b>Resumen:</b>
• <b>Evidencias:</b> <b>{total_evidences}</b>
• <b>Archivos:</b> <b>{total_files}</b>
        """
        
        send_long_message(bot, message.chat.id, list_msg, original_message=message, parse_mode='html')
        
    except Exception as e:
        error_msg = f"""
<b>❌ Error al actualizar</b>
⚠️ <b>No se pudo mostrar la nube actualizada.</b>
        """
        bot.editMessageText(message, error_msg, parse_mode='html')

def show_updated_all_clouds(bot, message):
    try:
        admin_evidence_manager.refresh_data()
        total_evidences = len(admin_evidence_manager.current_list)
        total_clouds = len(admin_evidence_manager.clouds_dict)
        total_files = 0
        
        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
            for ev in evidences:
                total_files += ev['files_count']
        
        if total_evidences == 0:
            empty_msg = f"""
<b>👑 Todas las nubes actualizadas</b>
📊 <b>Resumen general:</b>
• <b>Nubes:</b> <b>{total_clouds}</b>
• <b>Evidencias totales:</b> <b>0</b>
• <b>Archivos totales:</b> <b>0</b>

<b>✅ Todas las nubes están vacías</b>
            """
            bot.editMessageText(message, empty_msg, parse_mode='html')
            return
        
        menu_msg = f"""
<b>👑 Todas las nubes actualizadas</b>
📊 <b>Resumen general:</b>
• <b>Nubes:</b> <b>{total_clouds}</b>
• <b>Evidencias totales:</b> <b>{total_evidences}</b>
• <b>Archivos totales:</b> <b>{total_files}</b>

📋 <b>Nubes disponibles:</b>"""
        
        cloud_index = 0
        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
            cloud_files = sum(ev['files_count'] for ev in evidences)
            short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
            
            menu_msg += f"\n\n<b>{cloud_index}.</b> <code>{short_name}</code>"
            menu_msg += f"\n   📁 <b>{len(evidences)} evidencias, {cloud_files} archivos</b>"
            menu_msg += f"\n   🔍 /adm_cloud_{cloud_index}"
            
            if len(evidences) > 0:
                menu_msg += f"\n   🗑️ /adm_wipe_{cloud_index}"
            
            cloud_index += 1
        
        if total_evidences > 0:
            menu_msg += f"""

🔧 <b>Opciones masivas:</b>
/adm_nuke - ⚠️ <b>Eliminación masiva</b>
        """
        
        bot.editMessageText(message, menu_msg, parse_mode='html')
        
    except Exception as e:
        bot.editMessageText(message, f'<b>❌ Error al mostrar nubes actualizadas:</b> <b>{str(e)}</b>', parse_mode='html')

def show_loading_progress(bot, message, step, total_steps=3):
    progress_chars = ['○', '◔', '◑', '◕', '●']
    progress = int((step / total_steps) * 4)
    bar = progress_chars[progress] if progress < len(progress_chars) else progress_chars[-1]
    
    loading_msgs = [
        "🔄 <b>Conectando con las nubes...</b>",
        "📊 <b>Procesando datos...</b>",
        "✅ <b>Actualizando información...</b>"
    ]
    
    msg = loading_msgs[step-1] if step <= len(loading_msgs) else f"<b>Procesando... ({step}/{total_steps})</b>"
    bot.editMessageText(message, f"{msg} {bar}", parse_mode='html')

# ==============================
# DISPATCHER GENERAL DE MENSAJES (ONMESSAGE)
# ==============================
def onmessage(update, bot: ObigramClient):
    global MAINTENANCE_MODE, BANNED_USERS, REMOVED_USERS, ACTIVE_PROCESSES, ACTIVE_STATUS_CHECKS, CHANGING_CLOUD_USERS
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
                bot.sendMessage(chat_id, '<b>🚫 Has sido baneado y no puedes usar este bot.</b>', parse_mode='html')
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
            bot.sendMessage(chat_id, '<b>➲ No tienes acceso a este bot ✗</b>', parse_mode='html')
            return

        if MAINTENANCE_MODE and username.lower() != ADMIN_USERNAME.lower():
            bot.sendMessage(chat_id, 
                "🛠️ <b>¡Sistema en mantenimiento temporal!</b>\n\n"
                "⚠️ <b>El bot se encuentra actualmente bajo labores de optimización y mantenimiento.</b>\n"
                "⏳ <b>Por favor, intenta de nuevo más tarde. Disculpa las molestias ocasionadas.</b>", 
                parse_mode='html')
            return
        
        initialize_database(jdb)
        
        user_info = jdb.get_user(username)
        if user_info is None:
            matched_config = None
            for u, cfg in expanded_users.items():
                if u.lower() == username.lower():
                    matched_config = cfg
                    break
            config = matched_config or AVAILABLE_CLOUDS[0]
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

        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_', 2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop', True)
                
                proc_info = ACTIVE_PROCESSES.get(tid, {})
                proc_user = proc_info.get('user', username)
                proc_file = proc_info.get('file', 'Desconocido')
                proc_action = proc_info.get('action', 'Proceso')
                
                clean_process(tid)
                time.sleep(1)
                bot.editMessageText(msg, '<b>➲ Tarea cancelada ✗ </b>', parse_mode='html')
                
                if LOG_GROUP_ID != 0 and proc_user.lower() != ADMIN_USERNAME.lower():
                    try:
                        mensaje_log = (f"<b>❌ ¡Proceso cancelado!</b>\n\n"
                                       f"<b>👤 Usuario:</b> <b>@{proc_user}</b>\n"
                                       f"<b>🛠️ Acción:</b> <b>{proc_action}</b>\n"
                                       f"<b>📄 Nombre:</b> <b>{proc_file}</b>")
                        bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                    except Exception as e:
                        print(f"Error al notificar cancelación al grupo: {e}")

            except Exception as ex:
                print(str(ex))
            return

        message = bot.sendMessage(chat_id, '<b>➲ Procesando ✪ ●●○</b>', parse_mode='html')
        thread.store('msg', message)

        if username.lower() == ADMIN_USERNAME.lower() and msgText.lower().startswith('/add '):
            try:
                parts = msgText.replace('/add', '').strip().split()
                if len(parts) >= 2:
                    users_part = parts[0]
                    cloud_num_part = parts[1]
                    if cloud_num_part.isdigit():
                        cloud_idx = int(cloud_num_part) - 1
                        if 0 <= cloud_idx < len(AVAILABLE_CLOUDS):
                            selected_cloud = AVAILABLE_CLOUDS[cloud_idx]
                            usernames = [u.strip().lstrip('@') for u in users_part.split(',')]
                            usernames = [u for u in usernames if u]
                            
                            if not usernames:
                                bot.editMessageText(message, "<b>❌ Formato incorrecto.</b>\n💡 <b>Uso correcto:</b> /add usuario1,usuario2 1", parse_mode='html')
                                return

                            if any(u.lower() == ADMIN_USERNAME.lower() for u in usernames):
                                bot.editMessageText(message, f'🛡️ <b>Acción denegada:</b> <b>No es posible agregar al usuario administrador (@{ADMIN_USERNAME}).</b>', parse_mode='html')
                                return

                            banned_lower = {b.lower() for b in BANNED_USERS}
                            banned_found = [u for u in usernames if u.lower() in banned_lower]
                            if banned_found:
                                is_plural_banned = len(banned_found) > 1
                                banned_str = ", ".join([f"@{u}" for u in banned_found])
                                if is_plural_banned:
                                    bot.editMessageText(message, f"<b>❌ Los usuarios</b> {banned_str} <b>están baneados y no se pueden agregar.</b>", parse_mode='html')
                                else:
                                    bot.editMessageText(message, f"<b>❌ El usuario</b> {banned_str} <b>está baneado y no se puede agregar.</b>", parse_mode='html')
                                return

                            already_has_access = []
                            for u in usernames:
                                if u.lower() in {r.lower() for r in REMOVED_USERS}:
                                    continue
                                is_in_exp = any(eu.lower() == u.lower() for eu in expanded_users.keys())
                                if is_in_exp or jdb.get_user(u) is not None:
                                    already_has_access.append(u)

                            if already_has_access:
                                is_plural_access = len(already_has_access) > 1
                                access_str = ", ".join([f"@{u}" for u in already_has_access])
                                if is_plural_access:
                                    bot.editMessageText(message, f"<b>❌ Los usuarios</b> {access_str} <b>ya tienen acceso al bot.</b>", parse_mode='html')
                                else:
                                    bot.editMessageText(message, f"<b>❌ El usuario</b> {access_str} <b>ya tiene acceso al bot.</b>", parse_mode='html')
                                return

                            is_plural_users = len(usernames) > 1
                            for u in usernames:
                                REMOVED_USERS = {r for r in REMOVED_USERS if r.lower() != u.lower()}
                                jdb.create_user(u)
                                u_data = jdb.get_user(u)
                                for key, val in selected_cloud.items():
                                    u_data[key] = val
                                jdb.save_data_user(u, u_data)
                            jdb.save()
                            
                            short_host = selected_cloud['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                            users_str = ", ".join([f"@{u}" for u in usernames])
                            
                            if is_plural_users:
                                msg_text = f"<b>✅ ¡Usuarios agregados con éxito!</b>\n\n👥 <b>Usuarios:</b> <b>{users_str}</b>\n☁️ <b>Nube asignada:</b> <code>{short_host}</code>\n⚖️ <b>Límite:</b> <b>{selected_cloud['zips']} MB</b>"
                            else:
                                msg_text = f"<b>✅ ¡Usuario agregado con éxito!</b>\n\n👤 <b>Usuario:</b> <b>{users_str}</b>\n☁️ <b>Nube asignada:</b> <code>{short_host}</code>\n⚖️ <b>Límite:</b> <b>{selected_cloud['zips']} MB</b>"
                            
                            bot.editMessageText(message, msg_text, parse_mode='html')
                            return
                        else:
                            bot.editMessageText(message, f"<b>❌ Número de nube inválido.</b>\n💡 <b>Debe ser un número del 1 al {len(AVAILABLE_CLOUDS)}.</b>", parse_mode='html')
                            return
                    else:
                        bot.editMessageText(message, "<b>❌ Formato incorrecto.</b>\n💡 <b>Uso correcto:</b> /add usuario1,usuario2 1", parse_mode='html')
                        return
                else:
                    bot.editMessageText(message, "<b>❌ Formato incorrecto.</b>\n💡 <b>Uso correcto:</b> /add usuario1,usuario2 1", parse_mode='html')
                    return
            except Exception as e:
                bot.editMessageText(message, f"<b>❌ Error al agregar usuarios:</b> <b>{str(e)}</b>", parse_mode='html')
            return

        if username.lower() == ADMIN_USERNAME.lower() and msgText.lower().startswith('/remove '):
            try:
                users_part = msgText.replace('/remove', '').strip()
                usernames = [u.strip().lstrip('@') for u in users_part.split(',')]
                usernames = [u for u in usernames if u]
                
                if not usernames:
                    bot.editMessageText(message, "<b>❌ Formato incorrecto.</b>\n💡 <b>Uso correcto:</b> /remove usuario1,usuario2", parse_mode='html')
                    return
                
                if any(u.lower() == ADMIN_USERNAME.lower() for u in usernames):
                    bot.editMessageText(message, f"🛡️ <b>Acción denegada:</b> <b>No es posible quitar al usuario administrador (@{ADMIN_USERNAME}).</b>", parse_mode='html')
                    return
                
                removed_users = []
                not_found_users = []
                
                for u in usernames:
                    exists = False
                    is_in_exp = any(eu.lower() == u.lower() for eu in expanded_users.keys())
                    if is_in_exp or jdb.get_user(u) is not None:
                        exists = True
                        REMOVED_USERS.add(u.lower())
                        if u.lower() in {b.lower() for b in BANNED_USERS}:
                            BANNED_USERS = {b for b in BANNED_USERS if b.lower() != u.lower()}
                        try:
                            if hasattr(jdb, 'remove_user'):
                                jdb.remove_user(u)
                            elif hasattr(jdb, 'delete_user'):
                                jdb.delete_user(u)
                            elif hasattr(jdb, 'data') and isinstance(jdb.data, dict) and u in jdb.data:
                                del jdb.data[u]
                            elif hasattr(jdb, 'users') and isinstance(jdb.users, dict) and u in jdb.users:
                                del jdb.users[u]
                        except Exception as e:
                            print(f"Error deleting user from jdb: {e}")
                    
                    if exists:
                        removed_users.append(u)
                    else:
                        not_found_users.append(u)
                
                jdb.save()
                
                is_plural = len(removed_users) > 1
                users_str = ", ".join([f"@{u}" for u in removed_users])
                
                response_text = ""
                if removed_users:
                    if is_plural:
                        response_text += f"<b>✅ ¡Usuarios eliminados con éxito!</b>\n\n👥 <b>Usuarios:</b> <b>{users_str}</b>"
                    else:
                        response_text += f"<b>✅ ¡Usuario eliminado con éxito!</b>\n\n👤 <b>Usuario:</b> <b>{users_str}</b>"
                
                if not_found_users:
                    not_found_str = ", ".join([f"@{u}" for u in not_found_users])
                    response_text += f"\n\n⚠️ <b>No se encontraron en el sistema:</b> <b>{not_found_str}</b>"
                
                bot.editMessageText(message, response_text, parse_mode='html')
                return
            except Exception as e:
                bot.editMessageText(message, f"<b>❌ Error al quitar usuarios:</b> <b>{str(e)}</b>", parse_mode='html')
            return

        if username.lower() == ADMIN_USERNAME.lower() and msgText.lower().startswith('/ban '):
            try:
                targets_part = msgText.replace('/ban', '').strip()
                targets = [u.strip().lstrip('@') for u in targets_part.split(',')]
                targets = [u for u in targets if u]
                
                if not targets:
                    bot.editMessageText(message, "<b>❌ Formato incorrecto.</b>\n💡 <b>Uso correcto:</b> /ban usuario1,usuario2", parse_mode='html')
                    return
                
                if any(t.lower() == ADMIN_USERNAME.lower() for t in targets):
                    bot.editMessageText(message, f'🛡️ <b>Acción denegada:</b> <b>No es posible banear al usuario administrador (@{ADMIN_USERNAME}).</b>', parse_mode='html')
                    return
                
                success_targets = []
                already_banned = []
                not_found = []
                
                banned_lower = {b.lower() for b in BANNED_USERS}
                for target in targets:
                    is_in_exp = any(eu.lower() == target.lower() for eu in expanded_users.keys()) and not any(r.lower() == target.lower() for r in REMOVED_USERS)
                    if not is_in_exp and jdb.get_user(target) is None:
                        not_found.append(target)
                        continue
                    if target.lower() in banned_lower:
                        already_banned.append(target)
                        continue
                    
                    BANNED_USERS.add(target)
                    success_targets.append(target)
                
                is_plural = len(success_targets) > 1
                targets_str = ", ".join([f"@{u}" for u in success_targets])
                
                response_text = ""
                if success_targets:
                    if is_plural:
                        response_text += f"<b>🚫 ¡Usuarios baneados con éxito!</b>\n\n👥 <b>Usuarios:</b> <b>{targets_str}</b>"
                    else:
                        response_text += f"<b>🚫 ¡Usuario baneado con éxito!</b>\n\n👤 <b>Usuario:</b> <b>{targets_str}</b>"
                
                if already_banned:
                    ab_str = ", ".join([f"@{u}" for u in already_banned])
                    response_text += f"\n\nℹ️ <b>Ya se encontraban baneados:</b> <b>{ab_str}</b>"
                
                if not_found:
                    nf_str = ", ".join([f"@{u}" for u in not_found])
                    response_text += f"\n\n❌ <b>No existen en el sistema:</b> <b>{nf_str}</b>"
                
                bot.editMessageText(message, response_text, parse_mode='html')
                return
            except Exception as e:
                bot.editMessageText(message, f"<b>❌ Error al banear usuarios:</b> <b>{str(e)}</b>", parse_mode='html')
            return

        if username.lower() == ADMIN_USERNAME.lower() and msgText.lower().startswith('/unban '):
            try:
                targets_part = msgText.replace('/unban', '').strip()
                targets = [u.strip().lstrip('@') for u in targets_part.split(',')]
                targets = [u for u in targets if u]
                
                if not targets:
                    bot.editMessageText(message, "<b>❌ Formato incorrecto.</b>\n💡 <b>Uso correcto:</b> /unban usuario1,usuario2", parse_mode='html')
                    return
                
                if any(t.lower() == ADMIN_USERNAME.lower() for t in targets):
                    bot.editMessageText(message, f'🛡️ <b>Acción denegada:</b> <b>El usuario administrador (@{ADMIN_USERNAME}) no puede ser objetivo de este comando.</b>', parse_mode='html')
                    return
                
                success_targets = []
                not_banned = []
                not_found = []
                
                banned_lower = {b.lower() for b in BANNED_USERS}
                for target in targets:
                    is_in_exp = any(eu.lower() == target.lower() for eu in expanded_users.keys())
                    if not is_in_exp and jdb.get_user(target) is None:
                        not_found.append(target)
                        continue
                    if target.lower() not in banned_lower:
                        not_banned.append(target)
                        continue
                    
                    BANNED_USERS = {b for b in BANNED_USERS if b.lower() != target.lower()}
                    success_targets.append(target)
                
                is_plural = len(success_targets) > 1
                targets_str = ", ".join([f"@{u}" for u in success_targets])
                
                response_text = ""
                if success_targets:
                    if is_plural:
                        response_text += f"<b>✅ ¡Usuarios desbaneados con éxito!</b>\n\n👥 <b>Usuarios:</b> <b>{targets_str}</b>"
                    else:
                        response_text += f"<b>✅ ¡Usuario desbaneado con éxito!</b>\n\n👤 <b>Usuario:</b> <b>{targets_str}</b>"
                
                if not_banned:
                    nb_str = ", ".join([f"@{u}" for u in not_banned])
                    response_text += f"\n\nℹ️ <b>No estaban baneados:</b> <b>{nb_str}</b>"
                
                if not_found:
                    nf_str = ", ".join([f"@{u}" for u in not_found])
                    response_text += f"\n\n❌ <b>No existen en el sistema:</b> <b>{nf_str}</b>"
                
                bot.editMessageText(message, response_text, parse_mode='html')
                return
            except Exception as e:
                bot.editMessageText(message, f"<b>❌ Error al desbanear usuarios:</b> <b>{str(e)}</b>", parse_mode='html')
            return

        if username in CHANGING_CLOUD_USERS:
            if msgText.strip().isdigit():
                num = int(msgText.strip())
                if 1 <= num <= len(AVAILABLE_CLOUDS):
                    selected_cloud = AVAILABLE_CLOUDS[num - 1]
                    short_name = selected_cloud['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                    old_host = user_info.get('moodle_host', '').replace('https://', '').replace('http://', '').strip('/')
                    
                    if user_info.get('moodle_host') == selected_cloud['moodle_host']:
                        CHANGING_CLOUD_USERS.discard(username)
                        bot.editMessageText(message, f"ℹ️ <b>Ya estás usando esta nube</b>\n\n☁️ <b>Nube actual:</b> <code>{short_name}</code>\n⚖️ <b>Límite:</b> <b>{selected_cloud['zips']} MB</b>\n📁 <b>Tipo:</b> <b>{selected_cloud.get('uploadtype', 'evidence')}</b>", parse_mode='html')
                        return
                    
                    for key, val in selected_cloud.items():
                        user_info[key] = val
                    jdb.save_data_user(username, user_info)
                    jdb.save()
                    CHANGING_CLOUD_USERS.discard(username)
                    
                    bot.editMessageText(message, f"<b>✅ ¡Nube cambiada exitosamente!</b>\n\n☁️ <b>Nueva nube:</b> <code>{short_name}</code>\n⚖️ <b>Límite:</b> <b>{selected_cloud['zips']} MB</b>\n📁 <b>Tipo:</b> <b>{selected_cloud.get('uploadtype', 'evidence')}</b>", parse_mode='html')
                    
                    if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                        try:
                            msg_log = (f"<b>☁️ ¡Cambio de nube!</b>\n\n"
                                       f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                                       f"<b>🔄 Anterior:</b> <code>{old_host}</code>\n"
                                       f"<b>🆕 Nueva:</b> <code>{short_name}</code>\n"
                                       f"<b>⚖️ Límite:</b> <b>{selected_cloud['zips']} MB</b>\n"
                                       f"<b>📁 Tipo:</b> <b>{selected_cloud.get('uploadtype', 'evidence')}</b>")
                            bot.sendMessage(LOG_GROUP_ID, msg_log, parse_mode='html')
                        except Exception as e:
                            print(f"Error al notificar cambio de nube al grupo: {e}")
                    return
                else:
                    bot.editMessageText(message, f"<b>❌ Número inválido. Envía un número del 1 al {len(AVAILABLE_CLOUDS)}.</b>", parse_mode='html')
                    CHANGING_CLOUD_USERS.discard(username)
                    return
            else:
                CHANGING_CLOUD_USERS.discard(username)

        if '/cambiar' in msgText:
            clean_cmd = msgText.replace('/cambiar_', ' ').replace('/cambiar', ' ').strip()
            if clean_cmd.isdigit():
                num = int(clean_cmd)
                if 1 <= num <= len(AVAILABLE_CLOUDS):
                    selected_cloud = AVAILABLE_CLOUDS[num - 1]
                    short_name = selected_cloud['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                    old_host = user_info.get('moodle_host', '').replace('https://', '').replace('http://', '').strip('/')
                    
                    if user_info.get('moodle_host') == selected_cloud['moodle_host']:
                        bot.editMessageText(message, f"ℹ️ <b>Ya estás usando esta nube</b>\n\n☁️ <b>Nube actual:</b> <code>{short_name}</code>\n⚖️ <b>Límite:</b> <b>{selected_cloud['zips']} MB</b>\n📁 <b>Tipo:</b> <b>{selected_cloud.get('uploadtype', 'evidence')}</b>", parse_mode='html')
                        return
                    
                    for key, val in selected_cloud.items():
                        user_info[key] = val
                    jdb.save_data_user(username, user_info)
                    jdb.save()
                    bot.editMessageText(message, f"<b>✅ ¡Nube cambiada exitosamente!</b>\n\n☁️ <b>Nueva nube:</b> <code>{short_name}</code>\n⚖️ <b>Límite:</b> <b>{selected_cloud['zips']} MB</b>\n📁 <b>Tipo:</b> <b>{selected_cloud.get('uploadtype', 'evidence')}</b>", parse_mode='html')
                    
                    if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                        try:
                            msg_log = (f"<b>☁️ ¡Cambio de nube!</b>\n\n"
                                       f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                                       f"<b>🔄 Anterior:</b> <code>{old_host}</code>\n"
                                       f"<b>🆕 Nueva:</b> <code>{short_name}</code>\n"
                                       f"<b>⚖️ Límite:</b> <b>{selected_cloud['zips']} MB</b>\n"
                                       f"<b>📁 Tipo:</b> <b>{selected_cloud.get('uploadtype', 'evidence')}</b>")
                            bot.sendMessage(LOG_GROUP_ID, msg_log, parse_mode='html')
                        except Exception as e:
                            print(f"Error al notificar cambio de nube al grupo: {e}")
                    return
            
            menu_msg = "☁️ <b>Selecciona tu nueva nube</b>\n\n"
            for i, c in enumerate(AVAILABLE_CLOUDS, 1):
                short = c['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                menu_msg += f"<b>{i}.</b> <code>{short}</code>\n   ⚖️ <b>Límite:</b> <b>{c['zips']} MB</b> | <b>Tipo:</b> <b>{c.get('uploadtype', 'evidence')}</b>\n\n"
            menu_msg += f"💡 <b>Envía solo el número</b> (1 al {len(AVAILABLE_CLOUDS)})."
            
            CHANGING_CLOUD_USERS.add(username)
            bot.editMessageText(message, menu_msg, parse_mode='html')
            return

        if '/start' in msgText:
            if username.lower() == ADMIN_USERNAME.lower():
                admin_current_cloud = user_info["moodle_host"].replace('https://', '').replace('http://', '').strip('/')
                start_msg = f"""
👑 <b>Usuario Administrador</b>

👤 <b>Usuario:</b> <b>@{username}</b>
☁️ <b>Nube actual:</b> <code>{admin_current_cloud}</code>
⚖️ <b>Límite:</b> <b>{user_info["zips"]} MB</b>
📁 <b>Tipo de subida:</b> <b>{user_info.get('uploadtype', 'evidence')}</b>
🔧 <b>Rol:</b> <b>Administrador</b>

⚠️ <b>Nota importante:</b>
• <b>Acceso total a todas las nubes</b>
• <b>Gestión de evidencias globales</b>

🎯 <b>Comandos principales:</b>
/admin - <b>Panel de administración</b>
/status - <b>Estado de las nubes 🟢/🔴</b>
/procesos - <b>Procesos en tiempo real 🚀</b>
/mantenimiento - <b>Modo mantenimiento 🛠️</b>
/add - <b>Agregar usuario y nube ➕</b>
/remove - <b>Quitar usuario del bot ➖</b>
/ban - <b>Banear usuario 🚫</b>
/unban - <b>Desbanear usuario ✅</b>

📈 <b>Estadísticas y gestión:</b>
/adm_logs - <b>Logs del sistema</b>
/adm_users - <b>Estadísticas por usuario</b>
/adm_userclouds - <b>Ver nubes y usuarios</b>
/adm_uploads - <b>Últimas subidas</b>
/adm_deletes - <b>Últimas eliminaciones</b>
/adm_cleardata - <b>Limpiar estadísticas</b>

☁️ <b>Gestión de nubes:</b>
/adm_allclouds - <b>Ver todas las nubes</b>
/adm_cloud_X - <b>Nube específica</b>
/adm_show_X_Y - <b>Detalles de evidencia</b>
/adm_fetch_X_Y - <b>Descargar TXT</b>
/adm_delete_X_Y - <b>Eliminar evidencia</b>
/adm_wipe_X - <b>Limpiar nube X</b>
/adm_nuke - <b>Eliminación masiva ⚠️</b>

🔧 <b>Tus comandos personales:</b>
/cambiar - <b>Cambiar de nube (1 al {len(AVAILABLE_CLOUDS)}) 🔄</b>
/files - <b>Ver tus evidencias o archivos</b>
/txt_X - <b>Ver TXT de tu evidencia</b>
/del_X - <b>Eliminar tu evidencia o archivo</b>
/delall - <b>Eliminar todas tus evidencias o archivos</b>
/mystats - <b>Tus estadísticas</b>
                """
            else:
                current_cloud_short = user_info["moodle_host"].replace('https://', '').replace('http://', '').strip('/')
                start_msg = f"""
👤 <b>Usuario Regular</b>

👤 <b>Usuario:</b> <b>@{username}</b>
☁️ <b>Nube actual:</b> <code>{current_cloud_short}</code>
⚖️ <b>Límite:</b> <b>{user_info["zips"]} MB</b>
📁 <b>Tipo de subida:</b> <b>{user_info.get('uploadtype', 'evidence')}</b>

🔧 <b>Tus comandos:</b>
/start - <b>Ver esta información</b>
/cambiar - <b>Cambiar de nube (1 al {len(AVAILABLE_CLOUDS)}) 🔄</b>
/status - <b>Estado de tu nube 🟢/🔴</b>
/files - <b>Ver tus evidencias o archivos</b>
/txt_X - <b>Ver TXT de evidencia X</b>
/del_X - <b>Eliminar evidencia o archivo X</b>
/delall - <b>Eliminar todas tus evidencias o archivos</b>
/mystats - <b>Ver tus estadísticas</b>
                """
            
            bot.editMessageText(message, start_msg, parse_mode='html')
            send_sticker(chat_id, "CAACAgEAAxkBAAIoVGqA9obyhoMJe62uOFPzvoFk6vwpAAK7BgACnFgJROtfXZ-KKr1vPQQ")
            return

        if '/status' == msgText:
            if username in ACTIVE_STATUS_CHECKS:
                bot.editMessageText(message, "<b>⏳ Ya hay una verificación de estado en curso. Por favor, espera a que termine.</b>", parse_mode='html')
                return
            
            ACTIVE_STATUS_CHECKS.add(username)
            try:
                if username.lower() == ADMIN_USERNAME.lower():
                    bot.editMessageText(message, "<b>🔍 Verificando nubes una a una...</b>", parse_mode='html')
                    unique_configs = []
                    checked_hosts = set()
                    for cfg in AVAILABLE_CLOUDS:
                        moodle_host = cfg.get('moodle_host', '')
                        if moodle_host in checked_hosts:
                            continue
                        checked_hosts.add(moodle_host)
                        unique_configs.append(cfg)
                    
                    total_clouds = len(unique_configs)
                    for idx, cfg in enumerate(unique_configs):
                        s = check_single_cloud(cfg)
                        icon = "🟢 En línea" if s['online'] else "🔴 Fuera de línea"
                        clean_url = s['url'].replace('https://', '').replace('http://', '').strip('/')
                        status_msg = f"☁️ <code>{clean_url}</code>\n<b>Estado:</b> <b>{icon}</b>"
                        
                        if idx == 0:
                            bot.editMessageText(message, status_msg, parse_mode='html')
                        else:
                            time.sleep(0.4)
                            bot.sendMessage(chat_id, status_msg, parse_mode='html')
                else:
                    bot.editMessageText(message, "<b>🔍 Verificando estado de tu nube...</b>", parse_mode='html')
                    s = check_single_cloud(user_info)
                    icon = "🟢 En línea" if s['online'] else "🔴 Fuera de línea"
                    clean_url = user_info["moodle_host"].replace('https://', '').replace('http://', '').strip('/')
                    status_msg = f"☁️ <code>{clean_url}</code>\n<b>Estado:</b> <b>{icon}</b>"
                    bot.editMessageText(message, status_msg, parse_mode='html')
            except Exception as e:
                bot.editMessageText(message, f"<b>❌ Error al comprobar el estado de la nube:</b> <b>{str(e)}</b>", parse_mode='html')
            finally:
                ACTIVE_STATUS_CHECKS.discard(username)
            return

        if username.lower() == ADMIN_USERNAME.lower():
            if msgText.startswith('/mantenimiento'):
                if 'on' in msgText.lower():
                    MAINTENANCE_MODE = True
                elif 'off' in msgText.lower():
                    MAINTENANCE_MODE = False
                else:
                    MAINTENANCE_MODE = not MAINTENANCE_MODE
                
                estado = "ACTIVADO 🔴" if MAINTENANCE_MODE else "DESACTIVADO 🟢"
                
                cancel_count = 0
                if MAINTENANCE_MODE:
                    for tid, p in list(ACTIVE_PROCESSES.items()):
                        if p.get('user').lower() == ADMIN_USERNAME.lower():
                            continue
                        try:
                            if hasattr(bot, 'threads') and tid in bot.threads:
                                tcancel = bot.threads[tid]
                                tcancel.store('stop', True)
                                active_msg = tcancel.getStore('msg')
                                if active_msg:
                                    try:
                                        bot.editMessageText(active_msg, '<b>⚠️ Tarea cancelada automáticamente por inicio de mantenimiento del sistema ✗</b>', parse_mode='html')
                                    except:
                                        pass
                            clean_process(tid)
                            cancel_count += 1
                        except:
                            pass
                
                aviso_cancelados = f"\n⚠️ <b>Se cancelaron y notificaron {cancel_count} proceso(s) activo(s) (excepto administrador).</b>" if cancel_count > 0 else ""
                bot.editMessageText(message, f'<b>🛠️ Modo mantenimiento:</b> <b>{estado}</b>{aviso_cancelados}', parse_mode='html')
                return
                
            elif msgText == '/procesos':
                if not ACTIVE_PROCESSES:
                    bot.editMessageText(message, "<b>✅ No hay procesos activos en este momento.</b>", parse_mode='html')
                    return
                
                proc_msg = "🔄 <b>Procesos activos en tiempo real</b>\n\n"
                procesos_borrar = []
                
                for tid, p in ACTIVE_PROCESSES.items():
                    tiempo_activo = int(time.time() - p['last_update'])
                    stalled_warning = " ⚠️ <b>(Posiblemente trabado)</b>" if tiempo_activo > 30 and ('📥 Descargando' in p['action'] or '⬆️ Preparando' in p['action']) else ""
                    
                    if tiempo_activo > 60:
                        procesos_borrar.append(tid)
                        continue
                    
                    proc_msg += f"👤 <b>Usuario:</b> <b>@{p['user']}</b>\n"
                    proc_msg += f"🛠️ <b>Acción:</b> <b>{p['action']}</b>{stalled_warning}\n"
                    proc_msg += f"📄 <b>Nombre:</b> <b>{p['file']}</b>\n"
                    if '🗜️ Comprimiendo' not in p['action'] and '⬆️ Preparando' not in p['action']:
                        proc_msg += f"📊 <b>Progreso:</b> <b>{p['percent']}</b>\n"
                    proc_msg += f"\n"
                
                for tid in procesos_borrar:
                    clean_process(tid)
                
                if len(ACTIVE_PROCESSES) == 0:
                    bot.editMessageText(message, "<b>✅ No hay procesos activos en este momento.</b>", parse_mode='html')
                else:
                    bot.editMessageText(message, proc_msg, parse_mode="html")
                return

        if username.lower() == ADMIN_USERNAME.lower():
            if msgText == '/admin':
                stats = memory_stats.get_all_stats()
                total_size_formatted = format_file_size(stats['total_size_uploaded'])
                current_date = format_cuba_date()
                
                if memory_stats.has_any_data():
                    admin_msg = f"""
👑 <b>Panel de administrador</b>
📅 <b>Fecha:</b> <b>{current_date}</b>

📊 <b>Estadísticas globales:</b>
• <b>Subidas totales:</b> <b>{stats['total_uploads']}</b>
• <b>Eliminaciones totales:</b> <b>{stats['total_deletes']}</b>
• <b>Espacio total subido:</b> <b>{total_size_formatted}</b>
• <b>Nubes configuradas:</b> <b>{len(AVAILABLE_CLOUDS)}</b>

🚀 <b>Comandos rápidos:</b>
/status - <b>Estado de las nubes 🟢/🔴</b>
/procesos - <b>Procesos activos 🚀</b>
/mantenimiento - <b>Activar/Desactivar 🛠️</b>
/add - <b>Agregar usuario y nube ➕</b>
/remove - <b>Quitar usuario del bot ➖</b>
/ban - <b>Banear usuario 🚫</b>
/unban - <b>Desbanear usuario ✅</b>

📈 <b>Estadísticas y usuarios:</b>
/adm_logs - <b>Ver últimos logs</b>
/adm_users - <b>Estadísticas por usuario</b>
/adm_userclouds - <b>Ver nubes y usuarios</b>
/adm_uploads - <b>Últimas subidas</b>
/adm_deletes - <b>Últimas eliminaciones</b>
/adm_cleardata - <b>Limpiar todos los datos</b>

☁️ <b>Gestión de nubes:</b>
/adm_allclouds - <b>Ver todas las nubes</b>
/adm_cloud_X - <b>Nube específica</b>
/adm_show_X_Y - <b>Detalles de evidencia</b>
/adm_fetch_X_Y - <b>Descargar TXT</b>
/adm_delete_X_Y - <b>Eliminar evidencia</b>
/adm_wipe_X - <b>Limpiar nube X</b>
/adm_nuke - <b>Eliminación masiva ⚠️</b>

🔧 <b>Otros:</b>
/start - <b>Información de usuario</b>

🕐 <b>Hora Cuba:</b> <b>{format_cuba_datetime()}</b>
                    """
                else:
                    admin_msg = f"""
👑 <b>Panel de administrador</b>
📅 <b>Fecha:</b> <b>{current_date}</b>

⚠️ <b>No hay datos registrados</b>
<b>Aún no se ha realizado ninguna acción en el bot.</b>

📊 <b>Nubes configuradas:</b> <b>{len(AVAILABLE_CLOUDS)}</b>

🚀 <b>Comandos rápidos:</b>
/status - <b>Estado de las nubes 🟢/🔴</b>
/procesos - <b>Procesos activos 🚀</b>
/mantenimiento - <b>Activar/Desactivar 🛠️</b>
/add - <b>Agregar usuario y nube ➕</b>
/remove - <b>Quitar usuario del bot ➖</b>
/ban - <b>Banear usuario 🚫</b>
/unban - <b>Desbanear usuario ✅</b>

📈 <b>Estadísticas y usuarios:</b>
/adm_logs - <b>Ver últimos logs</b>
/adm_users - <b>Estadísticas por usuario</b>
/adm_userclouds - <b>Ver nubes y usuarios</b>
/adm_uploads - <b>Últimas subidas</b>
/adm_deletes - <b>Últimas eliminaciones</b>

☁️ <b>Gestión de nubes:</b>
/adm_allclouds - <b>Ver todas las nubes</b>
/adm_cloud_X - <b>Ver nube específica</b>
/adm_show_X_Y - <b>Detalles de evidencia</b>
/adm_fetch_X_Y - <b>Descargar TXT</b>

🔧 <b>Otros:</b>
/start - <b>Información de usuario</b>

🕐 <b>Hora Cuba:</b> <b>{format_cuba_datetime()}</b>
                    """
                
                bot.editMessageText(message, admin_msg, parse_mode='html')
                return
            
            elif '/adm_' in msgText:
                if msgText == '/adm_userclouds':
                    try:
                        uclouds_msg = "☁️ <b>Gestión de nubes y usuarios</b>\n\n"
                        
                        for idx, cloud_cfg in enumerate(AVAILABLE_CLOUDS, 1):
                            target_host = cloud_cfg.get('moodle_host', '')
                            zips = cloud_cfg.get('zips', '?')
                            short = target_host.replace('https://', '').replace('http://', '').strip('/')
                            
                            assigned_users = []
                            for u in expanded_users.keys():
                                if u in REMOVED_USERS:
                                    continue
                                u_info = jdb.get_user(u)
                                current_host = u_info.get('moodle_host', '') if u_info else cloud_cfg.get('moodle_host', '')
                                if current_host == target_host:
                                    assigned_users.append(f"@{u.lstrip('@')}")
                            
                            users_str = ", ".join(assigned_users) if assigned_users else "Ninguno"
                            
                            uclouds_msg += f"🌐 <b>Nube {idx}:</b> <code>{short}</code>\n"
                            uclouds_msg += f"⚖️ <b>Límite:</b> <b>{zips} MB</b> | <b>Tipo:</b> <b>{cloud_cfg.get('uploadtype', 'evidence')}</b>\n"
                            uclouds_msg += f"👤 <b>Usuarios:</b> <b>{users_str}</b>\n\n"
                        
                        send_long_message(bot, chat_id, uclouds_msg, original_message=message, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error al obtener nubes y usuarios:</b> <b>{str(e)}</b>', parse_mode='html')
                    return

                elif '/adm_allclouds' in msgText:
                    try:
                        show_loading_progress(bot, message, 1, 3)
                        total_evidences = admin_evidence_manager.refresh_data()
                        show_loading_progress(bot, message, 2, 3)
                        
                        if total_evidences == 0:
                            empty_msg = f"""
<b>👑 Todas las nubes</b>
📊 <b>Resumen general:</b>
• <b>Nubes configuradas:</b> <b>{len(AVAILABLE_CLOUDS)}</b>
• <b>Evidencias totales:</b> <b>0</b>
• <b>Archivos totales:</b> <b>0</b>

<b>✅ Todas las nubes están vacías</b>
                            """
                            bot.editMessageText(message, empty_msg, parse_mode='html')
                            return
                        
                        total_clouds = len(admin_evidence_manager.clouds_dict)
                        total_files = 0
                        
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            for ev in evidences:
                                total_files += ev['files_count']
                        
                        menu_msg = f"""
👑 <b>Gestión de todas las nubes</b>
📊 <b>Resumen general:</b>
• <b>Nubes:</b> <b>{total_clouds}</b>
• <b>Evidencias totales:</b> <b>{total_evidences}</b>
• <b>Archivos totales:</b> <b>{total_files}</b>

📋 <b>Nubes disponibles:</b>"""
                        
                        cloud_index = 0
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            cloud_files = sum(ev['files_count'] for ev in evidences)
                            short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                            
                            menu_msg += f"\n\n<b>{cloud_index}.</b> <code>{short_name}</code>"
                            menu_msg += f"\n   📁 <b>{len(evidences)} evidencias, {cloud_files} archivos</b>"
                            menu_msg += f"\n   🔍 /adm_cloud_{cloud_index}"
                            
                            if len(evidences) > 0:
                                menu_msg += f"\n   🗑️ /adm_wipe_{cloud_index}"
                            
                            cloud_index += 1
                        
                        show_loading_progress(bot, message, 3, 3)
                        
                        if total_evidences > 0:
                            menu_msg += f"""

🔧 <b>OPCIONES MASIVAS:</b>
/adm_nuke - ⚠️ <b>Eliminación masiva</b>

ℹ️ <b>Usa</b> /adm_cloud_X <b>para ver evidencias</b>
                            """
                        else:
                            menu_msg += f"""

<b>✅ Todas las nubes están vacías</b>
                            """
                        
                        bot.editMessageText(message, menu_msg, parse_mode='html')
                        
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
                    return
                
                elif '/adm_cloud_' in msgText:
                    try:
                        cloud_idx = extract_one_param_simple(msgText, '/adm_cloud_')
                        if cloud_idx is None:
                            bot.editMessageText(message, '<b>❌ Formato incorrecto. Use:</b> /adm_cloud_0', parse_mode='html')
                            return
                        
                        admin_evidence_manager.refresh_data()
                        
                        if cloud_idx < 0 or cloud_idx >= len(admin_evidence_manager.clouds_dict):
                            bot.editMessageText(message, f'<b>❌ Índice inválido. Máximo:</b> <b>{len(admin_evidence_manager.clouds_dict)-1}</b>', parse_mode='html')
                            return
                        
                        cloud_name = list(admin_evidence_manager.clouds_dict.keys())[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict[cloud_name]
                        short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                        
                        if not evidences:
                            empty_msg = f"""
<b>📭 NUBE VACÍA</b>
☁️ <code>{short_name}</code>
📊 <b>No hay evidencias en esta nube.</b>
                            """
                            bot.editMessageText(message, empty_msg, parse_mode='html')
                            return
                        
                        list_msg = f"""
<b>📋 EVIDENCIAS DE LA NUBE</b>
☁️ <code>{short_name}</code>

"""
                        for idx, evidence in enumerate(evidences):
                            ev_name = evidence['evidence_name']
                            clean_name = ev_name
                            user_tags = []
                            
                            for user in evidence['group_users']:
                                marker = f"{USER_EVIDENCE_MARKER}{user}"
                                if marker in ev_name:
                                    clean_name = ev_name.replace(marker, "").strip()
                                    user_tags.append(f"@{user}")
                            
                            if user_tags:
                                user_str = f" ({', '.join(user_tags[:2])})"
                                if len(user_tags) > 2:
                                    user_str = f" ({', '.join(user_tags[:2])}...)"
                            else:
                                user_str = ""
                            
                            list_msg += f"<b>{idx}.</b> <b>{clean_name[:35]}</b>"
                            if len(clean_name) > 35:
                                list_msg += "..."
                            list_msg += f"<b>{user_str}</b>\n"
                            list_msg += f"   📁 <b>Archivos:</b> <b>{evidence['files_count']}</b>\n"
                            list_msg += f"   👁️ <b>Ver:</b> /adm_show_{cloud_idx}_{idx}\n"
                            list_msg += f"   📄 <b>TXT:</b> /adm_fetch_{cloud_idx}_{idx}\n"
                            list_msg += f"   🗑️ <b>Borrar:</b> /adm_delete_{cloud_idx}_{idx}\n\n"
                        
                        total_evidences = len(evidences)
                        total_files = sum(e['files_count'] for e in evidences)
                        
                        list_msg += f"""
🔧 <b>ACCIÓN MASIVA:</b>
/adm_wipe_{cloud_idx} - <b>Eliminación masiva</b>

📊 <b>RESUMEN:</b>
• <b>Evidencias:</b> <b>{total_evidences}</b>
• <b>Archivos:</b> <b>{total_files}</b>
                        """
                        
                        send_long_message(bot, message.chat.id, list_msg, original_message=message, parse_mode='html')
                        
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
                    return
                
                elif '/adm_show_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_show_')
                        if params is None:
                            bot.editMessageText(message, '<b>❌ Formato incorrecto. Use:</b> /adm_show_0_1', parse_mode='html')
                            return
                        
                        cloud_idx, evid_idx = params
                        evidence = admin_evidence_manager.get_evidence(cloud_idx, evid_idx)
                        if evidence:
                            ev_name = evidence['evidence_name']
                            cloud_name = evidence['cloud_name']
                            short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                            
                            clean_name = ev_name
                            for user in evidence['group_users']:
                                marker = f"{USER_EVIDENCE_MARKER}{user}"
                                if marker in ev_name:
                                    clean_name = ev_name.replace(marker, "").strip()
                                    break
                            
                            show_msg = f"""
<b>👁️ Detalles de evidencia</b>
📝 <b>Nombre:</b> <b>{clean_name}</b>
📁 <b>Archivos:</b> <b>{evidence['files_count']}</b>
☁️ <b>Nube:</b> <code>{short_name}</code>

🔧 <b>ACCIONES:</b>
📄 /adm_fetch_{cloud_idx}_{evid_idx} - <b>TXT</b>
🗑️ /adm_delete_{cloud_idx}_{evid_idx} - <b>Eliminar</b>
                            """
                            bot.editMessageText(message, show_msg, parse_mode='html')
                        else:
                            bot.editMessageText(message, '<b>❌ No se encontró la evidencia</b>', parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
                    return
                
                elif '/adm_fetch_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_fetch_')
                        if params is None:
                            bot.editMessageText(message, '<b>❌ Formato incorrecto. Use:</b> /adm_fetch_0_1', parse_mode='html')
                            return
                        
                        cloud_idx, evid_idx = params
                        bot.editMessageText(message, '<b>📄 Obteniendo archivo TXT...</b>', parse_mode='html')
                        files = admin_evidence_manager.get_txt_for_evidence(cloud_idx, evid_idx)
                        
                        if files:
                            evidence = admin_evidence_manager.get_evidence(cloud_idx, evid_idx)
                            if evidence:
                                ev_name = evidence['evidence_name']
                                clean_name = ev_name
                                for user in evidence['group_users']:
                                    marker = f"{USER_EVIDENCE_MARKER}{user}"
                                    if marker in ev_name:
                                        clean_name = ev_name.replace(marker, "").strip()
                                        break
                                
                                safe_name = ''.join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).strip()
                                if not safe_name:
                                    safe_name = f"evidencia_{cloud_idx}_{evid_idx}"
                                
                                txtname = f"{safe_name}.txt"
                                txt = open(txtname, 'w')
                                for i, f in enumerate(files):
                                    url = f['directurl']
                                    txt.write(url)
                                    if i < len(files) - 1:
                                        txt.write('\n\n')
                                txt.close()
                                bot.sendFile(chat_id, txtname)
                                os.unlink(txtname)
                                bot.editMessageText(message, f'<b>✅ TXT enviado:</b> <b>{clean_name[:50]}</b>', parse_mode='html')
                            else:
                                bot.editMessageText(message, '<b>❌ No se encontró la evidencia</b>', parse_mode='html')
                        else:
                            bot.editMessageText(message, '<b>❌ No hay archivos en esta evidencia</b>', parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
                    return
                
                elif '/adm_delete_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_delete_')
                        if params is None:
                            bot.editMessageText(message, '<b>❌ Formato incorrecto. Use:</b> /adm_delete_0_1', parse_mode='html')
                            return
                        
                        cloud_idx, evid_idx = params
                        bot.editMessageText(message, '<b>🔍 Verificando datos...</b>', parse_mode='html')
                        
                        admin_evidence_manager.refresh_data()
                        cloud_names = list(admin_evidence_manager.clouds_dict.keys())
                        
                        if cloud_idx < 0 or cloud_idx >= len(cloud_names):
                            bot.editMessageText(message, '<b>❌ Índice de nube inválido</b>', parse_mode='html')
                            show_updated_all_clouds(bot, message)
                            return
                        
                        cloud_name = cloud_names[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict.get(cloud_name, [])
                        
                        if not evidences:
                            bot.editMessageText(message, f'<b>📭 La nube {cloud_idx} ya está vacía</b>', parse_mode='html')
                            show_updated_all_clouds(bot, message)
                            return
                        
                        if evid_idx < 0 or evid_idx >= len(evidences):
                            bot.editMessageText(message, '<b>❌ Índice de evidencia inválido</b>', parse_mode='html')
                            return
                        
                        evidence = evidences[evid_idx]
                        ev_name = evidence['evidence_name']
                        clean_name = ev_name
                        for user in evidence['group_users']:
                            marker = f"{USER_EVIDENCE_MARKER}{user}"
                            if marker in ev_name:
                                clean_name = ev_name.replace(marker, "").strip()
                                break
                        
                        short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                        bot.editMessageText(message, f'<b>🗑️ Eliminando evidencia:</b> <b>{clean_name[:50]}...</b>', parse_mode='html')
                        
                        success, ev_name, files_count = delete_evidence_from_cloud(
                            evidence['cloud_config'], 
                            evidence['evidence_data']
                        )
                        
                        if success:
                            admin_evidence_manager.refresh_data(force=True)
                            cloud_names = list(admin_evidence_manager.clouds_dict.keys())
                            
                            if cloud_idx < len(cloud_names):
                                current_evidences = admin_evidence_manager.clouds_dict.get(cloud_names[cloud_idx], [])
                                if current_evidences:
                                    result_msg = f"""
<b>✅ Eliminación exitosa</b>
🗑️ <b>Evidencia:</b> <b>{clean_name[:50]}</b>
📁 <b>Archivos eliminados:</b> <b>{files_count}</b>
☁️ <b>Nube:</b> <code>{short_name}</code>
                                    """
                                    bot.editMessageText(message, result_msg, parse_mode='html')
                                    time.sleep(1)
                                    show_updated_cloud(bot, message, cloud_idx)
                                else:
                                    result_msg = f"""
<b>✅ Eliminación completa</b>
🗑️ <b>Última evidencia eliminada</b>
📁 <b>Archivos borrados:</b> <b>{files_count}</b>
                                    """
                                    bot.editMessageText(message, result_msg, parse_mode='html')
                                    time.sleep(1)
                                    show_updated_all_clouds(bot, message)
                            else:
                                show_updated_all_clouds(bot, message)
                        else:
                            bot.editMessageText(message, f'<b>❌ Error al eliminar:</b> <b>{clean_name}</b>', parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
                    return
                
                elif '/adm_wipe_' in msgText:
                    try:
                        cloud_idx = extract_one_param_simple(msgText, '/adm_wipe_')
                        if cloud_idx is None:
                            bot.editMessageText(message, '<b>❌ Formato incorrecto. Use:</b> /adm_wipe_0', parse_mode='html')
                            return
                        
                        if cloud_idx < 0 or cloud_idx >= len(admin_evidence_manager.clouds_dict):
                            bot.editMessageText(message, f'<b>❌ Índice inválido. Máximo:</b> <b>{len(admin_evidence_manager.clouds_dict)-1}</b>', parse_mode='html')
                            return
                        
                        cloud_name = list(admin_evidence_manager.clouds_dict.keys())[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict[cloud_name]
                        
                        if not evidences:
                            bot.editMessageText(message, f'<b>📭 La nube {cloud_idx} ya está vacía</b>', parse_mode='html')
                            return
                        
                        short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                        bot.editMessageText(message, f'<b>💣 Limpiando nube</b> <code>{short_name}</code>...', parse_mode='html')
                        
                        cloud_config = None
                        for cfg in AVAILABLE_CLOUDS:
                            if cfg.get('moodle_host') == cloud_name:
                                cloud_config = cfg
                                break
                        
                        if cloud_config:
                            success, deleted_count, total_files = delete_all_evidences_from_cloud(cloud_config)
                            if success:
                                admin_evidence_manager.refresh_data(force=True)
                                result_msg = f"""
<b>💥 Limpieza exitosa</b>
✅ <b>Nube:</b> <code>{short_name}</code>
✅ <b>Evidencias:</b> <b>{deleted_count}</b>
✅ <b>Archivos:</b> <b>{total_files}</b>
                                """
                                bot.editMessageText(message, result_msg, parse_mode='html')
                                time.sleep(1)
                                show_updated_all_clouds(bot, message)
                            else:
                                bot.editMessageText(message, f'<b>❌ Error al limpiar</b> <code>{short_name}</code>', parse_mode='html')
                        else:
                            bot.editMessageText(message, '<b>❌ No se encontró configuración</b>', parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
                    return
                
                elif '/adm_nuke' in msgText:
                    try:
                        total_evidences = len(admin_evidence_manager.current_list)
                        if total_evidences == 0:
                            bot.editMessageText(message, '<b>📭 No hay evidencias para eliminar</b>', parse_mode='html')
                            return
                        
                        bot.editMessageText(message, '<b>💣💣💣 Eliminación masiva...</b>', parse_mode='html')
                        results = []
                        deleted_total = 0
                        files_total = 0
                        
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            cloud_config = None
                            for cfg in AVAILABLE_CLOUDS:
                                if cfg.get('moodle_host') == cloud_name:
                                    cloud_config = cfg
                                    break
                            
                            if cloud_config:
                                success, deleted_count, total_files = delete_all_evidences_from_cloud(cloud_config)
                                short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                                if success:
                                    deleted_total += deleted_count
                                    files_total += total_files
                                    results.append(f"✅ <code>{short_name}</code>: <b>{deleted_count} ev., {total_files} arch.</b>")
                                else:
                                    results.append(f"❌ <code>{short_name}</code>: <b>Error</b>")
                        
                        admin_evidence_manager.refresh_data(force=True)
                        final_msg = f"""
💥 <b>Eliminación masiva completada</b>
📊 <b>Evidencias:</b> <b>{deleted_total}</b>
📁 <b>Archivos:</b> <b>{files_total}</b>
"""
                        for result in results:
                            final_msg += f"\n{result}"
                        bot.editMessageText(message, final_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
                    return
                
                elif '/adm_logs' in msgText:
                    try:
                        if not memory_stats.has_any_data():
                            bot.editMessageText(message, "<b>⚠️ No hay datos registrados.</b>", parse_mode='html')
                            return
                        
                        limit = 300
                        if '_' in msgText:
                            try:
                                limit = int(msgText.split('_')[2])
                            except: pass
                        
                        uploads = memory_stats.get_recent_uploads(limit)
                        deletes = memory_stats.get_recent_deletes(limit)
                        
                        logs_msg = "📋 <b>Últimos logs</b>\n\n"
                        if uploads:
                            logs_msg += "⬆️ <b>Subidas:</b>\n"
                            for log in uploads:
                                logs_msg += f"• <b>{log['timestamp']}</b> - <b>@{log['username']}</b>: <b>{log['filename']}</b> (<b>{log['file_size_formatted']}</b>)\n"
                            logs_msg += "\n"
                        if deletes:
                            logs_msg += "🗑️ <b>Eliminaciones:</b>\n"
                            for log in deletes:
                                if log['type'] == 'delete_all':
                                    logs_msg += f"• <b>{log['timestamp']}</b> - <b>@{log['username']}</b>: <b>Eliminación masiva ({log.get('deleted_evidences', 1)} ev.)</b>\n"
                                else:
                                    logs_msg += f"• <b>{log['timestamp']}</b> - <b>@{log['username']}</b>: <b>{log['filename']}</b>\n"
                        
                        if len(logs_msg) > 4000:
                            logs_msg = logs_msg[:4000] + "\n\n⚠️ <b>Truncado</b>"
                        bot.editMessageText(message, logs_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"<b>❌ Error al obtener logs:</b> <b>{str(e)}</b>", parse_mode='html')
                    return
                
                elif '/adm_users' in msgText:
                    try:
                        users = memory_stats.get_all_users()
                        if not users:
                            bot.editMessageText(message, "<b>⚠️ No hay usuarios registrados.</b>", parse_mode='html')
                            return
                        
                        users_msg = "👥 <b>Estadísticas por usuario</b>\n\n"
                        for user, data in sorted(users.items(), key=lambda x: x[1]['uploads'], reverse=True):
                            total_size_formatted = format_file_size(data['total_size'])
                            users_msg += f"👤 <b>Usuario:</b> <b>@{user}</b>\n   📤 <b>Subidas:</b> <b>{data['uploads']}</b>\n   🗑️ <b>Eliminaciones:</b> <b>{data['deletes']}</b>\n   💾 <b>Espacio:</b> <b>{total_size_formatted}</b>\n\n"
                        
                        if len(users_msg) > 4000:
                            users_msg = users_msg[:4000] + "\n\n⚠️ <b>Truncado</b>"
                        bot.editMessageText(message, users_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"<b>❌ Error al obtener usuarios:</b> <b>{str(e)}</b>", parse_mode='html')
                    return
                
                elif '/adm_uploads' in msgText:
                    try:
                        uploads = memory_stats.get_recent_uploads(15)
                        if not uploads:
                            bot.editMessageText(message, "<b>⚠️ No hay subidas registradas.</b>", parse_mode='html')
                            return
                        
                        uploads_msg = "📤 <b>Últimas subidas</b>\n\n"
                        for i, log in enumerate(uploads, 1):
                            uploads_msg += f"<b>{i}.</b> <b>{log['filename']}</b>\n   👤 <b>@{log['username']}</b> | 📏 <b>{log['file_size_formatted']}</b>\n\n"
                        bot.editMessageText(message, uploads_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"<b>❌ Error al obtener subidas:</b> <b>{str(e)}</b>", parse_mode='html')
                    return
                
                elif '/adm_deletes' in msgText:
                    try:
                        deletes = memory_stats.get_recent_deletes(15)
                        if not deletes:
                            bot.editMessageText(message, "<b>⚠️ No hay eliminaciones registradas.</b>", parse_mode='html')
                            return
                        
                        deletes_msg = "🗑️ <b>Últimas eliminaciones</b>\n\n"
                        for i, log in enumerate(deletes, 1):
                            if log['type'] == 'delete_all':
                                deletes_msg += f"<b>{i}.</b> <b>Eliminación masiva</b>\n   👤 <b>@{log['username']}</b> (<b>{log.get('deleted_evidences', 1)} ev.</b>)\n\n"
                            else:
                                deletes_msg += f"<b>{i}.</b> <b>{log['filename']}</b>\n   👤 <b>@{log['username']}</b>\n\n"
                        bot.editMessageText(message, deletes_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"<b>❌ Error al obtener eliminaciones:</b> <b>{str(e)}</b>", parse_mode='html')
                    return
                
                elif '/adm_cleardata' in msgText:
                    try:
                        if not memory_stats.has_any_data():
                            bot.editMessageText(message, "<b>⚠️ No hay datos para limpiar.</b>", parse_mode='html')
                            return
                        result = memory_stats.clear_all_data()
                        bot.editMessageText(message, f"<b>{result}</b>", parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"<b>❌ Error al limpiar datos:</b> <b>{str(e)}</b>", parse_mode='html')
                    return
        
        # ============================================
        # COMANDOS REGULARES DE USUARIO
        # ============================================
        
        if '/mystats' in msgText:
            user_stats = memory_stats.get_user_stats(username)
            if user_stats:
                total_size_formatted = format_file_size(user_stats['total_size'])
                daily_size_formatted = format_file_size(user_stats.get('daily_size', 0))
                stats_msg = f"""
📊 <b>Tus estadísticas</b>
👤 <b>Usuario:</b> <b>@{username}</b>
📤 <b>Subidas:</b> <b>{user_stats['uploads']}</b>
🗑️ <b>Eliminaciones:</b> <b>{user_stats['deletes']}</b>
💾 <b>Espacio usado hoy:</b> <b>{daily_size_formatted} / 1 GB</b>
💾 <b>Espacio histórico:</b> <b>{total_size_formatted}</b>
📅 <b>Última actividad:</b> <b>{user_stats['last_activity']}</b>
                """
            else:
                stats_msg = f"""
📊 <b>Tus estadísticas</b>
👤 <b>Usuario:</b> <b>@{username}</b>
📤 <b>Subidas:</b> <b>0</b>
🗑️ <b>Eliminaciones:</b> <b>0</b>
💾 <b>Espacio usado hoy:</b> <b>0 B / 1 GB</b>

ℹ️ <b>Aún no tienes actividad registrada.</b>
                """
            bot.editMessageText(message, stats_msg, parse_mode='html')
            return
        
        # =========================================================
        # COMANDO /files (SOPORTE TOTAL: EVIDENCE, DRAFT Y BLOG)
        # =========================================================
        elif '/files' == msgText:
            proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
            try:
                requests.get(user_info['moodle_host'], timeout=5, proxies=proxy, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
            except:
                bot.editMessageText(message, f'<b>❌ La nube <code>{user_info["moodle_host"]}</code> no responde o está caída.</b>', parse_mode='html')
                return

            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'], proxy=proxy)
            loged = client.login()
            if loged:
                upload_type = user_info.get('uploadtype', 'evidence')
                
                # 1. LISTADO MODO DRAFT
                if upload_type == 'draft':
                    try:
                        draft_files = client.getFiles()
                        visible_files = [f for f in draft_files if f.get('type') != 'folder' and (f.get('filename') or f.get('fullname'))]
                        if len(visible_files) > 0:
                            files_msg = "📁 <b>Tus archivos en Borrador (Draft)</b>\n\n"
                            for idx, item in enumerate(visible_files):
                                fname = item.get('filename') or item.get('fullname') or 'Archivo'
                                fsize = format_file_size(int(item.get('filesize', 0))) if item.get('filesize') else ""
                                files_msg += f"• <b>{fname}</b> [ <b>{fsize}</b> ]\n  /del_{idx}\n\n"
                            files_msg += f"<b>Total:</b> <b>{len(visible_files)} archivo(s)</b>"
                            bot.editMessageText(message, files_msg, parse_mode='html')
                        else:
                            bot.editMessageText(message, '<b>📭 No hay archivos guardados en borrador</b>', parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error obteniendo archivos draft:</b> <b>{str(e)}</b>', parse_mode='html')
                    client.logout()
                    return

                # 2. LISTADO MODO BLOG
                elif upload_type == 'blog':
                    try:
                        blog_entries = client.getBlogs()
                        if len(blog_entries) > 0:
                            files_msg = "📰 <b>Tus publicaciones de Blog</b>\n\n"
                            for idx, item in enumerate(blog_entries):
                                files_msg += f"• <b>{item['name']}</b>\n  /del_{idx}\n\n"
                            files_msg += f"<b>Total:</b> <b>{len(blog_entries)} publicación(es)</b>"
                            bot.editMessageText(message, files_msg, parse_mode='html')
                        else:
                            bot.editMessageText(message, '<b>📭 No hay blogs registrados</b>', parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'<b>❌ Error obteniendo blogs:</b> <b>{str(e)}</b>', parse_mode='html')
                    client.logout()
                    return

                # 3. LISTADO MODO EVIDENCE
                all_evidences = client.getEvidences()
                visible_list = []
                search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                
                for ev in all_evidences:
                    if ev['name'].endswith(search_pattern):
                        clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                        file_count = len(ev['files']) if 'files' in ev else 0
                        visible_list.append({
                            'name': clean_name,
                            'file_count': file_count,
                            'original': ev
                        })
                
                if len(visible_list) > 0:
                    files_msg = "📁 <b>Tus evidencias</b>\n\n"
                    for idx, item in enumerate(visible_list):
                        files_msg += f"• <b>{item['name']}</b> [ <b>{item['file_count']}</b> ]\n  /txt_{idx} | /del_{idx}\n\n"
                    files_msg += f"<b>Total:</b> <b>{len(visible_list)} evidencia(s)</b>"
                    bot.editMessageText(message, files_msg, parse_mode='html')
                else:
                    bot.editMessageText(message, '<b>📭 No hay evidencias disponibles</b>', parse_mode='html')
                client.logout()
            else:
                bot.editMessageText(message, '<b>➲ Error y causas🧐</b>\n1-<b>Revise su cuenta</b>\n2-<b>Servidor deshabilitado:</b> <b>'+client.path+'</b>', parse_mode='html')
                
        elif '/txt_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'], proxy=proxy)
                loged = client.login()
                if loged:
                    all_evidences = client.getEvidences()
                    visible_list = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                            visible_list.append({
                                'clean_name': clean_name,
                                'original': ev
                            })
                    
                    if findex < 0 or findex >= len(visible_list):
                        bot.editMessageText(message, '<b>❌ Índice inválido. Use </b>/files<b> para ver la lista.</b>', parse_mode='html')
                        client.logout()
                        return
                    
                    evindex = visible_list[findex]['original']
                    clean_name = visible_list[findex]['clean_name']
                    txtname = clean_name + '.txt'
                    sendTxt(txtname, evindex['files'], update, bot, user_info=user_info)
                    client.logout()
                    bot.editMessageText(message, '<b>📄 TXT aquí</b>', parse_mode='html')
                else:
                    bot.editMessageText(message, '<b>➲ Error y causas🧐</b>\n1-<b>Revise su cuenta</b>\n2-<b>Servidor deshabilitado:</b> <b>'+client.path+'</b>', parse_mode='html')
            except ValueError:
                bot.editMessageText(message, '<b>❌ Formato incorrecto. Use:</b> /txt_0', parse_mode='html')
            except Exception as e:
                bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
             
        # =========================================================
        # COMANDO /del_ (BORRADO INDIVIDUAL EN DRAFT, BLOG Y EVIDENCE)
        # =========================================================
        elif '/del_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
                loged = client.login()
                if loged:
                    upload_type = user_info.get('uploadtype', 'evidence')
                    
                    # 1. BORRADO EN DRAFT
                    if upload_type == 'draft':
                        draft_files = client.getFiles()
                        visible_files = [f for f in draft_files if f.get('type') != 'folder' and (f.get('filename') or f.get('fullname'))]
                        if findex < 0 or findex >= len(visible_files):
                            bot.editMessageText(message, '<b>❌ Índice inválido. Use </b>/files<b> para ver la lista.</b>', parse_mode='html')
                            client.logout()
                            return
                        
                        target_file = visible_files[findex]
                        file_name = target_file.get('filename') or target_file.get('fullname')
                        client.delteFile(file_name)
                        client.logout()
                        
                        memory_stats.log_delete(username=username, filename=file_name, evidence_name="Draft", moodle_host=user_info['moodle_host'])
                        bot.editMessageText(message, f"🗑️ <b>Archivo borrado con éxito:</b> <b>{file_name}</b>", parse_mode='html')
                        return

                    # 2. BORRADO EN BLOG
                    elif upload_type == 'blog':
                        blog_entries = client.getBlogs()
                        if findex < 0 or findex >= len(blog_entries):
                            bot.editMessageText(message, '<b>❌ Índice inválido. Use </b>/files<b> para ver la lista.</b>', parse_mode='html')
                            client.logout()
                            return
                        
                        target_blog = blog_entries[findex]
                        client.deleteBlog(target_blog['id'])
                        client.logout()
                        
                        memory_stats.log_delete(username=username, filename=target_blog['name'], evidence_name="Blog Entry", moodle_host=user_info['moodle_host'])
                        bot.editMessageText(message, f"🗑️ <b>Entrada de blog borrada con éxito:</b> <b>{target_blog['name']}</b>", parse_mode='html')
                        return

                    # 3. BORRADO EN EVIDENCE
                    all_evidences = client.getEvidences()
                    visible_list = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                            visible_list.append({
                                'clean_name': clean_name,
                                'original': ev
                            })
                    
                    if findex < 0 or findex >= len(visible_list):
                        bot.editMessageText(message, '<b>❌ Índice inválido. Use </b>/files<b> para ver la lista.</b>', parse_mode='html')
                        client.logout()
                        return
                    
                    evfile = visible_list[findex]['original']
                    evidence_clean_name = visible_list[findex]['clean_name']
                    file_count = len(evfile['files']) if 'files' in evfile else 0
                    
                    client.deleteEvidence(evfile)
                    all_evidences = client.getEvidences()
                    
                    updated_visible_list = []
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                            updated_visible_list.append({
                                'clean_name': clean_name,
                                'original': ev
                            })
                    
                    client.logout()
                    memory_stats.log_delete(
                        username=username,
                        filename=f"{evidence_clean_name} ({file_count} archivos)",
                        evidence_name=evidence_clean_name,
                        moodle_host=user_info['moodle_host']
                    )

                    if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                        try:
                            clean_host = user_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                            msg_log = (f"<b>🗑️ ¡Evidencia eliminada!</b>\n\n"
                                       f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                                       f"<b>📄 Evidencia:</b> <b>{evidence_clean_name}</b>\n"
                                       f"<b>📁 Archivos:</b> <b>{file_count}</b>\n"
                                       f"<b>☁️ Nube:</b> <code>{clean_host}</code>")
                            bot.sendMessage(LOG_GROUP_ID, msg_log, parse_mode='html')
                        except Exception as e:
                            print(f"Error al notificar eliminación al grupo: {e}")
                    
                    confirmation_msg = f"🗑️ <b>Evidencia eliminada:</b> <b>{evidence_clean_name}</b>\n📁 <b>Archivos borrados:</b> <b>{file_count}</b>\n"
                    if len(updated_visible_list) > 0:
                        confirmation_msg += "📋 <b>Tus evidencias actualizadas:</b>\n\n"
                        for idx, item in enumerate(updated_visible_list):
                            clean_name = item['clean_name']
                            item_file_count = len(item['original']['files']) if 'files' in item['original'] else 0
                            confirmation_msg += f"• <b>{clean_name}</b> [ <b>{item_file_count}</b> ]\n  /txt_{idx} | /del_{idx}\n\n"
                        bot.editMessageText(message, confirmation_msg, parse_mode='html')
                    else:
                        confirmation_msg += "<b>📭 No hay evidencias disponibles</b>"
                        bot.editMessageText(message, confirmation_msg, parse_mode='html')
                else:
                    bot.editMessageText(message, '<b>➲ Error y causas🧐</b>\n1-<b>Revise su cuenta</b>\n2-<b>Servidor deshabilitado:</b> <b>'+client.path+'</b>', parse_mode='html')
            except ValueError:
                bot.editMessageText(message, '<b>❌ Formato incorrecto. Use:</b> /del_0', parse_mode='html')
            except Exception as e:
                bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(e)}</b>', parse_mode='html')
                
        # =========================================================
        # COMANDO /delall (BORRADO MASIVO EN DRAFT, BLOG Y EVIDENCE)
        # =========================================================
        elif '/delall' in msgText:
            try:
                proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
                loged = client.login()
                if loged:
                    upload_type = user_info.get('uploadtype', 'evidence')
                    
                    # 1. VACIAR DRAFT
                    if upload_type == 'draft':
                        draft_files = client.getFiles()
                        visible_files = [f for f in draft_files if f.get('type') != 'folder' and (f.get('filename') or f.get('fullname'))]
                        if not visible_files:
                            bot.editMessageText(message, '<b>📭 No hay archivos para eliminar en el borrador</b>', parse_mode='html')
                            client.logout()
                            return
                        
                        deleted_count = 0
                        for f in visible_files:
                            fname = f.get('filename') or f.get('fullname')
                            try:
                                client.delteFile(fname)
                                deleted_count += 1
                            except: pass
                        
                        client.logout()
                        memory_stats.log_delete_all(username=username, deleted_evidences=0, deleted_files=deleted_count, moodle_host=user_info['moodle_host'])
                        bot.editMessageText(message, f"🗑️ <b>Borrador vaciado</b>\n\n• <b>Archivos borrados:</b> <b>{deleted_count}</b>", parse_mode='html')
                        return

                    # 2. VACIAR BLOGS
                    elif upload_type == 'blog':
                        blog_entries = client.getBlogs()
                        if not blog_entries:
                            bot.editMessageText(message, '<b>📭 No hay entradas de blog para eliminar</b>', parse_mode='html')
                            client.logout()
                            return
                        
                        deleted_count = 0
                        for b in blog_entries:
                            try:
                                client.deleteBlog(b['id'])
                                deleted_count += 1
                            except: pass
                        
                        client.logout()
                        memory_stats.log_delete_all(username=username, deleted_evidences=deleted_count, deleted_files=deleted_count, moodle_host=user_info['moodle_host'])
                        bot.editMessageText(message, f"🗑️ <b>Publicaciones de blog eliminadas</b>\n\n• <b>Entradas borradas:</b> <b>{deleted_count}</b>", parse_mode='html')
                        return

                    # 3. VACIAR EVIDENCE
                    all_evidences = client.getEvidences()
                    user_evidences = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            user_evidences.append(ev)
                    
                    if not user_evidences:
                        bot.editMessageText(message, '<b>📭 No hay evidencias disponibles</b>', parse_mode='html')
                        client.logout()
                        return
                    
                    total_evidences = len(user_evidences)
                    total_files = sum(len(ev.get('files', [])) for ev in user_evidences)
                    
                    for item in user_evidences:
                        try:
                            client.deleteEvidence(item)
                        except: pass
                    
                    client.logout()
                    memory_stats.log_delete_all(
                        username=username, 
                        deleted_evidences=total_evidences, 
                        deleted_files=total_files,
                        moodle_host=user_info['moodle_host']
                    )

                    if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                        try:
                            clean_host = user_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                            msg_log = (f"<b>🗑️💥 ¡Eliminación masiva!</b>\n\n"
                                       f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                                       f"<b>📊 Evidencias borradas:</b> <b>{total_evidences}</b>\n"
                                       f"<b>📁 Archivos borrados:</b> <b>{total_files}</b>\n"
                                       f"<b>☁️ Nube:</b> <code>{clean_host}</code>")
                            bot.sendMessage(LOG_GROUP_ID, msg_log, parse_mode='html')
                        except Exception as e:
                            print(f"Error al notificar eliminación masiva al grupo: {e}")
                    
                    deletion_msg = f"🗑️ <b>Eliminación masiva completada</b>\n\n• <b>Evidencias eliminadas:</b> <b>{total_evidences}</b>\n• <b>Archivos borrados:</b> <b>{total_files}</b>\n\n<b>✅ ¡Todas tus evidencias han sido eliminadas!</b>"
                    bot.editMessageText(message, deletion_msg, parse_mode='html')
                else:
                    bot.editMessageText(message, '<b>➲ Error y causas🧐</b>\n1-<b>Revise su cuenta</b>\n2-<b>Servidor deshabilitado:</b> <b>'+client.path+'</b>', parse_mode='html')
            except Exception as ex:
                bot.editMessageText(message, f'<b>❌ Error:</b> <b>{str(ex)}</b>', parse_mode='html')
                
        elif 'http' in msgText:
            url = msgText
            file_size = 0
            filename = url.split('/')[-1] or "Desconocido"
            
            try:
                headers = {}
                if user_info['proxy']:
                    proxy_dict = ProxyCloud.parse(user_info['proxy'])
                    if 'http' in proxy_dict:
                        headers.update({'Proxy': proxy_dict['http']})
                
                response = requests.head(url, allow_redirects=True, timeout=5, headers=headers)
                file_size = int(response.headers.get('content-length', 0))
                
                cd = response.headers.get('content-disposition')
                if cd and 'filename=' in cd:
                    filename = cd.split('filename=')[1].strip('"\'')
                else:
                    filename = unquote(filename)
            except: pass

            # --- VERIFICACIÓN DE LÍMITE DIARIO DE 1 GB (EXCEPTO ADMIN) ---
            if username.lower() != ADMIN_USERNAME.lower():
                memory_stats.check_and_update_daily_reset(username)
                user_st = memory_stats.get_user_stats(username)
                current_daily_size = user_st['daily_size'] if user_st else 0
                MAX_DAILY_LIMIT = 1024 * 1024 * 1024  # 1 GB
                
                if current_daily_size + file_size > MAX_DAILY_LIMIT:
                    send_reaction(chat_id, update.message.message_id, "💩")
                    if current_daily_size == 0:
                        limit_msg = (
                            f"<b>🚫 Límite diario excedido</b>\n\n"
                            f"<b>Estimado usuario @{username}, el archivo que intenta procesar pesa {format_file_size(file_size)}, "
                            f"lo cual excede el límite diario permitido de 1 GB. "
                            f"No es posible procesar este archivo.</b>"
                        )
                        group_limit_msg = (
                            f"<b>🚫 ¡Límite diario excedido!</b>\n\n"
                            f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                            f"<b>⚖️ Archivo:</b> <b>{format_file_size(file_size)}</b>\n"
                            f"<b>⚠️ Detalle:</b> <b>Supera el límite de 1 GB diario</b>"
                        )
                    else:
                        limit_msg = (
                            f"<b>🚫 Límite diario alcanzado</b>\n\n"
                            f"<b>Estimado usuario @{username}, ya ha consumido {format_file_size(current_daily_size)} de su cuota diaria de 1 GB. "
                            f"Intentar procesar este archivo de {format_file_size(file_size)} excedería su límite permitido. "
                            f"Su cuota se restablecerá automáticamente al cambiar el día.</b>"
                        )
                        group_limit_msg = (
                            f"<b>🚫 ¡Cuota diaria superada!</b>\n\n"
                            f"<b>👤 Usuario:</b> <b>@{username}</b>\n"
                            f"<b>📊 Consumo previo:</b> <b>{format_file_size(current_daily_size)}</b>\n"
                            f"<b>⚖️ Archivo intentado:</b> <b>{format_file_size(file_size)}</b>\n"
                            f"<b>⚠️ Detalle:</b> <b>La suma excede el límite de 1 GB diario</b>"
                        )

                    bot.editMessageText(message, limit_msg, parse_mode='html')
                    send_sticker(chat_id, "CAACAgEAAxkBAAIoWmqA9ruIyyqZw_C2PTIr47iOS-6MAAK9BgACnFgJRF49GlLpEVF9PQQ")
                    
                    if LOG_GROUP_ID != 0:
                        try:
                            bot.sendMessage(LOG_GROUP_ID, group_limit_msg, parse_mode='html')
                        except Exception as e:
                            print(f"Error al notificar bloqueo por límite diario al grupo: {e}")
                    return
            
            # Reacción con rayo para enlace aceptado
            send_reaction(chat_id, update.message.message_id, "⚡")

            if LOG_GROUP_ID != 0 and username.lower() != ADMIN_USERNAME.lower():
                try:
                    clean_host = user_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                    tamano_formateado = format_file_size(file_size) if file_size > 0 else "Desconocido"
                    mensaje_log = (f"<b>🔔 ¡Nuevo enlace recibido!</b>\n\n👤 <b>Usuario:</b> <b>@{username}</b>\n📄 <b>Nombre:</b> <b>{filename}</b>\n⚖️ <b>Peso:</b> <b>{tamano_formateado}</b>\n🔗 <b>Enlace:</b> <code>{url}</code>\n☁️ <b>Nube:</b> <code>{clean_host}</code>")
                    bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar enlace: {e}")
            
            ddl(update, bot, message, url, file_name=filename, thread=thread, jdb=jdb)
        else:
            bot.editMessageText(message, '<b>➲ No se pudo procesar ✗ </b>', parse_mode='html')
            
    except Exception as ex:
        print(f"Error general onmessage: {str(ex)}")
        print(traceback.format_exc())

def main():
    bot = ObigramClient(BOT_TOKEN)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()