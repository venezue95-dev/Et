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
import random
import pytz
import threading

# FIXED CONFIGURATION IN CODE
BOT_TOKEN = "8340084935:AAHLn3ftkhaJg9KyDgtL1ely4vo-1DlFyqM"

# ADMINISTRATOR CONFIGURATION
ADMIN_USERNAME = "Eliel_21"
ADMIN_CHAT_ID = 7363341763  # Tu ID
LOG_GROUP_ID = -1004295272245  # ID del grupo para notificaciones de enlaces, archivos y txts

# VARIABLES GLOBALES DE CONTROL
MAINTENANCE_MODE = False
BANNED_USERS = set()
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

# LISTA DISPONIBLE DE NUBES (1 al 7)
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
        "moodle_user": "ray910210",
        "moodle_password": "RaymonD*007",
        "zips": 99,
        "uploadtype": "evidence",
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
        "moodle_host": "https://aula.uclv.edu.cu/",
        "moodle_repo_id": 4,
        "moodle_user": "lircarrasco",
        "moodle_password": "jarofo-234",
        "zips": 300,
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
    "usuario_uclv1,usuario_uclv2": AVAILABLE_CLOUDS[6]
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
        """Determina si debe refrescar los datos"""
        if cloud_name is None:
            # Para refresco completo
            if self.last_full_refresh is None:
                return True
            elapsed = (datetime.datetime.now() - self.last_full_refresh).total_seconds()
            return elapsed > self.ttl
        
        # Para nube específica
        if cloud_name not in self.last_refresh:
            return True
        elapsed = (datetime.datetime.now() - self.last_refresh[cloud_name]).total_seconds()
        return elapsed > self.ttl
    
    def update_cache(self, cloud_name, data):
        """Actualiza la caché para una nube específica"""
        self.cache[cloud_name] = data
        self.last_refresh[cloud_name] = datetime.datetime.now()
    
    def update_full_cache(self, data):
        """Actualiza caché completa"""
        self.cache = data.copy()
        self.last_full_refresh = datetime.datetime.now()
    
    def get_cache(self, cloud_name):
        """Obtiene datos de caché"""
        return self.cache.get(cloud_name)
    
    def clear_cache(self):
        """Limpia toda la caché"""
        self.cache = {}
        self.last_refresh = {}
        self.last_full_refresh = None

cloud_cache = CloudCache(ttl_seconds=30)  # 30 segundos de caché

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
    return dt.strftime("%d/%m/%y %I:%M %p")

def format_file_size(size_bytes):
    """Formatea bytes a KB, MB o GB automáticamente"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

# ==============================
# SISTEMA DE ESTADÍSTICAS EN MEMORIA
# ==============================

class MemoryStats:
    """Sistema de estadísticas en memoria (sin archivos)"""
    
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        """Reinicia todas las estadísticas"""
        self.stats = {
            'total_uploads': 0,
            'total_deletes': 0,
            'total_size_uploaded': 0
        }
        self.user_stats = {}
        self.upload_logs = []
        self.delete_logs = []
    
    def log_upload(self, username, filename, file_size, moodle_host):
        """Registra una subida exitosa"""
        try:
            file_size = int(file_size)
        except:
            file_size = 0
        
        self.stats['total_uploads'] += 1
        self.stats['total_size_uploaded'] += file_size
        
        if username not in self.user_stats:
            self.user_stats[username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'last_activity': format_cuba_datetime()
            }
        
        self.user_stats[username]['uploads'] += 1
        self.user_stats[username]['total_size'] += file_size
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
        """Registra una eliminación individual"""
        self.stats['total_deletes'] += 1
        
        if username not in self.user_stats:
            self.user_stats[username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'last_activity': format_cuba_datetime()
            }
        
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
        """Registra eliminación masiva"""
        self.stats['total_deletes'] += deleted_files
        
        if username not in self.user_stats:
            self.user_stats[username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'last_activity': format_cuba_datetime()
            }
        
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
        """Obtiene estadísticas de un usuario"""
        if username in self.user_stats:
            return self.user_stats[username]
        return None
    
    def get_all_stats(self):
        """Obtiene todas las estadísticas globales"""
        return self.stats
    
    def get_all_users(self):
        """Obtiene todos los usuarios"""
        return self.user_stats
    
    def get_recent_uploads(self, limit=10):
        """Obtiene subidas recientes"""
        return self.upload_logs[-limit:][::-1] if self.upload_logs else []
    
    def get_recent_deletes(self, limit=10):
        """Obtiene eliminaciones recientes"""
        return self.delete_logs[-limit:][::-1] if self.delete_logs else []
    
    def has_any_data(self):
        """Verifica si hay datos"""
        return len(self.upload_logs) > 0 or len(self.delete_logs) > 0
    
    def clear_all_data(self):
        """Limpia todos los datos"""
        self.reset_stats()
        return "✅ Todos los datos han sido eliminados"

memory_stats = MemoryStats()

def get_random_large_file_message():
    """Retorna un mensaje chistoso aleatorio para archivos grandes"""
    messages = [
        "¡Uy! Este archivo pesa más que mis ganas de trabajar los lunes 📦",
        "¿Seguro que no estás subiendo toda la temporada de tu serie favorita? 🎬",
        "Archivo detectado: XXL. Mi bandeja de entrada necesita hacer dieta 🍔",
        "¡500MB alert! Esto es más grande que mi capacidad de decisión en un restaurante 🍕",
        "Tu archivo necesita su propio código postal para viajar por internet 📮",
        "Vaya, con este peso hasta el bot necesita ir al gimnasio 💪",
        "¡Archivo XXL detectado! Preparando equipo de escalada para subirlo 🧗",
        "Este archivo es tan grande que necesita su propia habitación en la nube ☁️",
        "¿Esto es un archivo o un elefante digital disfrazado? 🐘",
        "¡Alerta de megabyte! Tu archivo podría tener su propia órbita 🛰️",
        "Archivo pesado detectado: activando modo grúa industrial 🏗️",
        "Este archivo hace que mi servidor sude bytes 💦",
        "¡Tamaño máximo superado! Necesitaré un café extra para esto ☕",
        "Tu archivo es más grande que mi lista de excusas para no hacer ejercicio 🏃",
        "Detectado: Archivo XXL. Preparando refuerzos estructurales 🏗️",
        "¡Vaya! Este archivo es tan grande que necesita pasaporte para viajar 🌍",
        "Con este peso, hasta la nube digital va a necesitar paraguas ☂️",
        "¡500MB detectados! ¿Traes la biblioteca de Alejandría en un ZIP? 📚",
        "Tu archivo tiene más MB que yo tengo neuronas después del café 🧠",
        "¡Alerta! Archivo de tamaño épico detectado. Activando modo Hulk 💚",
        "Este archivo es más pesado que mis remordimientos del lunes 🎭",
        "¡Uy! Con este tamaño hasta internet va a sudar la gota gorda 💧",
        "¿Seguro que no estás subiendo un elefante en formato MP4? 🐘📹",
        "Archivo XXL: Mi conexión acaba de pedir aumento de sueldo 💰",
        "¡500MB! Hasta los píxeles están haciendo dieta en este archivo 🥗"
    ]
    return random.choice(messages)

def expand_user_groups():
    """Convierte 'usuario1,usuario2':config a 'usuario1':config, 'usuario2':config"""
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
        proxy_parsed = ProxyCloud.parse(proxy)
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
# TRACKER DE PROCESOS ACTIVOS (PROFESIONAL Y PRECISO)
# ==============================
def update_process(thread_id, username, filename, action, current, total):
    try:
        current = int(current or 0)
        total = int(total or 0)
        percent = (current / total) * 100 if total > 0 else 0
        if percent > 100: percent = 100
        
        ACTIVE_PROCESSES[thread_id] = {
            'user': username,
            'file': filename,
            'action': action,
            'percent': f"{percent:.1f}%",
            'last_update': time.time()
        }
    except: pass

def clean_process(thread_id):
    if thread_id in ACTIVE_PROCESSES:
        del ACTIVE_PROCESSES[thread_id]

# ==============================
# FUNCIÓN PARA DIVIDIR MENSAJES LARGOS
# ==============================
def send_long_message(bot, chat_id, text, original_message=None, parse_mode=None):
    """Divide mensajes largos por saltos de línea para respetar el límite de Telegram"""
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
        time.sleep(0.5)  # Breve pausa para evitar flood
        bot.sendMessage(chat_id, msg_part, parse_mode=parse_mode)

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        username = args[3] if len(args) > 3 else "Desconocido"
        if thread.getStore('stop'):
            downloader.stop()
            raise Exception("Tarea detenida por mantenimiento o cancelación")
        
        update_process(thread.id, username, filename, '📥 Descargando', currentBits, totalBits)
        
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: 
        raise ex

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        username = args[4] if len(args) > 4 else "Desconocido"
        
        if thread and thread.getStore('stop'):
            raise Exception("Tarea detenida por mantenimiento o cancelación")
        
        update_process(thread.id, username, filename, '📤 Subiendo', currentBits, totalBits)
        
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: 
        raise ex

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'⬆️ Preparando Para Subir ☁ ●●○')
        username = update.message.sender.username
        if thread:
            if thread.getStore('stop'):
                raise Exception("Tarea detenida por mantenimiento o cancelación")
            update_process(thread.id, username, os.path.basename(str(filename)), '⬆️ Preparando Para Subir', 0, 100)
            
        evidence = None
        fileid = None
        user_info = jdb.get_user(username)
        proxy = ProxyCloud.parse(user_info['proxy'])
        
        client = MoodleClient(user_info['moodle_user'],
                              user_info['moodle_password'],
                              user_info['moodle_host'],
                              user_info['moodle_repo_id'],
                              proxy=proxy)
        loged = client.login()
        if loged:
            evidences = client.getEvidences()
            
            original_evidname = str(filename).split('.')[0]
            visible_evidname = original_evidname
            internal_evidname = f"{original_evidname}{USER_EVIDENCE_MARKER}{username}"
            
            for evid in evidences:
                if evid['name'] == internal_evidname:
                    evidence = evid
                    break
            if evidence is None:
                evidence = client.createEvidence(internal_evidname)

            originalfile = ''
            if len(files)>1:
                originalfile = filename
            draftlist = []
            for f in files:
                if thread and thread.getStore('stop'):
                    raise Exception("Tarea detenida por mantenimiento o cancelación")
                f_size = get_file_size(f)
                resp = None
                iter = 0
                tokenize = False
                if user_info['tokenize']!=0:
                   tokenize = True
                while resp is None:
                    if thread and thread.getStore('stop'):
                        raise Exception("Tarea detenida por mantenimiento o cancelación")
                    fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread,username),tokenize=tokenize)
                    draftlist.append(resp)
                    iter += 1
                    if iter>=10:
                        break
                os.unlink(f)
            try:
                client.saveEvidence(evidence)
            except:pass
            return draftlist
        else:
            bot.editMessageText(message,'➥ Error En La Página ✗')
            return None
    except Exception as ex:
        bot.editMessageText(message,'➥ Error ✗\n' + str(ex))
        return None

def processFile(update,bot,message,file,thread=None,jdb=None):
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
            compresingInfo = infos.createCompresing(file,file_size,max_file_size)
            bot.editMessageText(message,compresingInfo)
            
            # Registrar estado de compresión en procesos activos (sin porcentaje)
            if thread:
                if thread.getStore('stop'):
                    raise Exception("Tarea detenida por mantenimiento o cancelación")
                update_process(thread.id, username, os.path.basename(file), '🗜️ Comprimiendo', 0, 100)
            
            zipname = str(file).split('.')[0] + createID()
            mult_file = zipfile.MultiFile(zipname,max_file_size)
            zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
            zip.write(file)
            zip.close()
            mult_file.close()
            client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,thread=thread,jdb=jdb)
            try:
                os.unlink(file)
            except:pass
            file_upload_count = len(mult_file.files)
        else:
            client = processUploadFiles(file,file_size,[file],update,bot,message,thread=thread,jdb=jdb)
            file_upload_count = 1
        
        visible_evidname = ''
        files = []
        if client:
            original_evidname = str(file).split('.')[0]
            visible_evidname = original_evidname
            internal_evidname = f"{original_evidname}{USER_EVIDENCE_MARKER}{username}"
            
            txtname = visible_evidname + '.txt'
            try:
                proxy = ProxyCloud.parse(getUser['proxy'])
                moodle_client = MoodleClient(getUser['moodle_user'],
                                             getUser['moodle_password'],
                                             getUser['moodle_host'],
                                             getUser['moodle_repo_id'],
                                             proxy=proxy)
                if moodle_client.login():
                    evidences = moodle_client.getEvidences()
                    
                    evidence_index = -1
                    for idx, ev in enumerate(evidences):
                        if ev['name'] == internal_evidname:
                            files = ev['files']
                            for i in range(len(files)):
                                url = files[i]['directurl']
                                if '?forcedownload=1' in url:
                                    url = url.replace('?forcedownload=1', '')
                                elif '&forcedownload=1' in url:
                                    url = url.replace('&forcedownload=1', '')
                                if '&token=' in url and '?' not in url:
                                    url = url.replace('&token=', '?token=', 1)
                                files[i]['directurl'] = url
                            evidence_index = idx
                            break
                    
                    moodle_client.logout()
                    
                    findex = evidence_index if evidence_index != -1 else len(evidences) - 1
            except Exception as e:
                print(f"Error obteniendo índice de evidencia: {e}")
                findex = 0
            
            bot.deleteMessage(message.chat.id,message.message_id)
            finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
            filesInfo = infos.createFileMsg(file,files)
            bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
            
            filename_clean = os.path.basename(file)
            memory_stats.log_upload(
                username=username,
                filename=filename_clean,
                file_size=file_size,
                moodle_host=getUser['moodle_host']
            )
            
            # --- NOTIFICAR AL GRUPO DE LOGS SI EXISTE ---
            if LOG_GROUP_ID != 0:
                try:
                    clean_host = getUser['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                    mensaje_log = (f"✅ <b>¡Subida Completada!</b>\n"
                                   f"👤 Usuario: @{username}\n"
                                   f"📄 Archivo: <code>{filename_clean}</code>\n"
                                   f"⚖️ Peso: {format_file_size(file_size)}\n"
                                   f"☁️ Nube: <code>{clean_host}</code>")
                    bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar subida al grupo: {e}")
            
            if len(files)>0:
                txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
                sendTxt(txtname, files, update, bot, send_to_group=True)
        else:
            bot.editMessageText(message,'➥ Error en la página ✗')
    except Exception as ex:
        print(f"Proceso detenido o error: {ex}")
    finally:
        if thread:
            clean_process(thread.id)

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
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
                        bot.editMessageText(message, f"⚠️ Error de conexión, reintentando... (Intento {attempt+1}/{retries})")
                    except: pass
                    if thread:
                        update_process(thread.id, username, "Descarga", f'🔄 Reintentando ({attempt+1}/{retries})', 0, 100)
                
                file = downloader.download_url(url, progressfunc=downloadFile, args=(bot,message,thread,username))
                if file:
                    break
            except Exception as ex:
                if attempt == retries - 1:
                    try:
                        bot.editMessageText(message, f"❌ Error en la descarga tras {retries} intentos fallidos ✗")
                    except: pass
                    raise ex
                time.sleep(3)
        
        if not downloader.stoping:
            if file:
                processFile(update,bot,message,file,thread=thread,jdb=jdb)
            else:
                try:
                    bot.editMessageText(message,'➥ Error en la descarga ✗')
                except:
                    bot.editMessageText(message,'➥ Error en la descarga ✗')
    except Exception as ex:
        print(f"Error en ddl: {ex}")
    finally:
        if thread:
            clean_process(thread.id)

def sendTxt(name, files, update, bot, send_to_group=False):
    txt = open(name,'w')
    
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
    
    # Enviar al usuario en privado
    bot.sendFile(update.message.chat.id, name)
    
    # Enviar también al grupo de logs si está configurado
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
    """Elimina un mensaje después de un retraso específico"""
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
    """
    Obtiene todas las evidencias de todas las nubes preconfiguradas (versión optimizada)
    """
    # Verificar caché primero
    if use_cache and not cloud_cache.should_refresh():
        cached_data = cloud_cache.get_cache('all_clouds')
        if cached_data:
            return cached_data
    
    all_evidences = []
    
    for user_group, cloud_config in PRE_CONFIGURATED_USERS.items():
        # Extraer la configuración de la nube
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        # Verificar caché para esta nube específica
        if use_cache and not cloud_cache.should_refresh(moodle_host):
            cached_evidence = cloud_cache.get_cache(moodle_host)
            if cached_evidence:
                all_evidences.extend(cached_evidence)
                continue
        
        try:
            # Conectar a la nube con timeout
            proxy_parsed = ProxyCloud.parse(proxy)
            client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
            
            if client.login():
                # Obtener todas las evidencias de esta nube
                evidences = client.getEvidences()
                
                # Procesar cada evidencia
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
                # Actualizar caché
                if use_cache:
                    cloud_cache.update_cache(moodle_host, [ev for ev in all_evidences if ev['cloud_name'] == moodle_host])
            else:
                print(f"No se pudo conectar a {moodle_host}")
                
        except Exception as e:
            print(f"Error obteniendo evidencias de {moodle_host}: {str(e)}")
    
    # Actualizar caché completa
    if use_cache:
        cloud_cache.update_full_cache(all_evidences)
    
    return all_evidences

def delete_evidence_from_cloud(cloud_config, evidence):
    """
    Elimina una evidencia específica de una nube
    """
    try:
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        proxy_parsed = ProxyCloud.parse(proxy)
        client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
        
        if client.login():
            # Buscar la evidencia exacta
            all_evidences = client.getEvidences()
            evidence_to_delete = None
            
            for ev in all_evidences:
                if ev.get('id') == evidence.get('id'):
                    evidence_to_delete = ev
                    break
            
            if evidence_to_delete:
                evidence_name = evidence_to_delete.get('name', '')
                files_count = len(evidence_to_delete.get('files', []))
                # Eliminar la evidencia
                client.deleteEvidence(evidence_to_delete)
                client.logout()
                # Invalidar caché
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
    """
    Elimina todas las evidencias de una nube específica
    """
    try:
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        proxy_parsed = ProxyCloud.parse(proxy)
        client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
        
        if client.login():
            # Obtener todas las evidencias
            all_evidences = client.getEvidences()
            deleted_count = 0
            total_files = 0
            
            # Eliminar cada evidencia
            for evidence in all_evidences:
                try:
                    files_count = len(evidence.get('files', []))
                    client.deleteEvidence(evidence)
                    deleted_count += 1
                    total_files += files_count
                except:
                    pass
            
            client.logout()
            # Invalidar caché
            cloud_cache.clear_cache()
            return True, deleted_count, total_files
        else:
            return False, 0, 0
            
    except Exception as e:
        return False, 0, 0

class AdminEvidenceManager:
    """Gestor de evidencias para administrador"""
    
    def __init__(self):
        self.current_list = []
        self.clouds_dict = {}
        self.last_update = None
    
    def refresh_data(self, force=False):
        """Actualiza los datos de evidencias (con caché)"""
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
            
            # Crear lista plana para acceso rápido
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
        """Obtiene una evidencia específica"""
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
        """Obtiene el TXT de una evidencia"""
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
                
                proxy_parsed = ProxyCloud.parse(proxy)
                client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
                
                if client.login():
                    # Buscar la evidencia actualizada
                    all_evidences = client.getEvidences()
                    current_evidence = None
                    
                    for ev in all_evidences:
                        if ev.get('id') == evidence_data.get('id'):
                            current_evidence = ev
                            break
                    
                    if current_evidence:
                        files = current_evidence.get('files', [])
                        
                        # Preparar URLs
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
        """Limpia la caché del manager"""
        cloud_cache.clear_cache()
        self.current_list = []
        self.clouds_dict = {}
        self.last_update = None

admin_evidence_manager = AdminEvidenceManager()

# ==============================
# FUNCIONES SIMPLES PARA EXTRACCIÓN DE PARÁMETROS
# ==============================

def extract_one_param_simple(msgText, prefix):
    """
    Extrae un parámetro de forma simple usando split
    """
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
    """
    Extrae dos parámetros de forma simple usando split
    """
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
    """Muestra la lista actualizada de una nube después de eliminar"""
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
📭 NUBE VACÍA
────────────────────────

✅ ELIMINACIÓN COMPLETA
☁️ {short_name}

🎉 ¡Has eliminado todas las evidencias de esta nube!

🔄 Regresando a todas las nubes...
────────────────────────
            """
            bot.editMessageText(message, empty_msg)
            time.sleep(1.5)
            show_updated_all_clouds(bot, message)
            return
        
        short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
        
        list_msg = f"""
📋 NUBE ACTUALIZADA
☁️ {short_name}
────────────────────────

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
            
            list_msg += f"{idx}. {clean_name[:35]}"
            if len(clean_name) > 35:
                list_msg += "..."
            list_msg += f"{user_str}\n"
            list_msg += f"   📁 {evidence['files_count']} archivos\n"
            list_msg += f"   👁️ /adm_show_{cloud_idx}_{idx}\n"
            list_msg += f"   📄 /adm_fetch_{cloud_idx}_{idx}\n"
            list_msg += f"   🗑️ /adm_delete_{cloud_idx}_{idx}\n\n"
        
        total_evidences = len(evidences)
        total_files = sum(e['files_count'] for e in evidences)
        
        list_msg += f"""
────────────────────────
🔧 ACCIONES MASIVAS:
/adm_wipe_{cloud_idx} - Eliminar TODO

📊 RESUMEN:
• Evidencias: {total_evidences}
• Archivos: {total_files}
────────────────────────
        """
        
        send_long_message(bot, message.chat.id, list_msg, original_message=message)
        
    except Exception as e:
        error_msg = f"""
❌ ERROR AL ACTUALIZAR
────────────────────────
⚠️ No se pudo mostrar la nube actualizada.
────────────────────────
        """
        bot.editMessageText(message, error_msg)

def show_updated_all_clouds(bot, message):
    """Muestra todas las nubes actualizadas después de una eliminación masiva"""
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
👑 TODAS LAS NUBES ACTUALIZADAS
────────────────────────
📊 RESUMEN GENERAL:
• Nubes: {total_clouds}
• Evidencias totales: 0
• Archivos totales: 0
────────────────────────
✅ Todas las nubes están vacías
            """
            bot.editMessageText(message, empty_msg)
            return
        
        menu_msg = f"""
👑 TODAS LAS NUBES ACTUALIZADAS
────────────────────────
📊 RESUMEN GENERAL:
• Nubes: {total_clouds}
• Evidencias totales: {total_evidences}
• Archivos totales: {total_files}

📋 NUBES DISPONIBLES:"""
        
        cloud_index = 0
        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
            cloud_files = sum(ev['files_count'] for ev in evidences)
            short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
            
            menu_msg += f"\n\n{cloud_index}. {short_name}"
            menu_msg += f"\n   📁 {len(evidences)} evidencias, {cloud_files} archivos"
            menu_msg += f"\n   🔍 /adm_cloud_{cloud_index}"
            
            if len(evidences) > 0:
                menu_msg += f"\n   🗑️ /adm_wipe_{cloud_index}"
            
            cloud_index += 1
        
        if total_evidences > 0:
            menu_msg += f"""

────────────────────────
🔧 OPCIONES MASIVAS:
/adm_nuke - ⚠️ Eliminar TODO
────────────────────────
        """
        
        bot.editMessageText(message, menu_msg)
        
    except Exception as e:
        bot.editMessageText(message, f'❌ Error al mostrar nubes actualizadas: {str(e)}')

def show_loading_progress(bot, message, step, total_steps=3):
    progress_chars = ['○', '◔', '◑', '◕', '●']
    progress = int((step / total_steps) * 4)
    bar = progress_chars[progress] if progress < len(progress_chars) else progress_chars[-1]
    
    loading_msgs = [
        "🔄 Conectando con las nubes...",
        "📊 Procesando datos...",
        "✅ Actualizando información..."
    ]
    
    msg = loading_msgs[step-1] if step <= len(loading_msgs) else f"Procesando... ({step}/{total_steps})"
    bot.editMessageText(message, f"{msg} {bar}")

# ==============================
# FUNCIÓN PRINCIPAL ONMESSAGE
# ==============================

def onmessage(update,bot:ObigramClient):
    global MAINTENANCE_MODE, BANNED_USERS, ACTIVE_PROCESSES, ACTIVE_STATUS_CHECKS, CHANGING_CLOUD_USERS
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        chat_id = update.message.chat.id

        msgText = ''
        try: msgText = update.message.text
        except:pass

        # === CONTROL DE ACCESO (MANTENIMIENTO Y BANEO) ===
        if username in BANNED_USERS and username != ADMIN_USERNAME:
            bot.sendMessage(chat_id, '🚫 Has sido baneado y no puedes usar este bot.')
            return
            
        if MAINTENANCE_MODE and username != ADMIN_USERNAME:
            bot.sendMessage(chat_id, 
                "🛠️ <b>¡SISTEMA EN MANTENIMIENTO TEMPORAL!</b>\n\n"
                "⚠️ El bot se encuentra actualmente bajo labores de optimización y mantenimiento.\n"
                "⏳ Por favor, intenta de nuevo más tarde. Disculpa las molestias ocasionadas.", 
                parse_mode='html')
            return

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()
        
        expanded_users = expand_user_groups()
        
        if username not in expanded_users and jdb.get_user(username) is None:
            bot.sendMessage(chat_id,'➲ No tienes acceso a este bot ✗')
            return
        
        initialize_database(jdb)
        
        user_info = jdb.get_user(username)
        if user_info is None:
            config = expanded_users.get(username, AVAILABLE_CLOUDS[0])
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
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                clean_process(tid)
                time.sleep(3)
                bot.editMessageText(msg,'➲ Tarea Cancelada ✗ ')
            except Exception as ex:
                print(str(ex))
            return

        message = bot.sendMessage(chat_id,'➲ Procesando ✪ ●●○')
        thread.store('msg',message)

        # ============================================
        # COMANDO /add PARA ADMINISTRADOR
        # ============================================
        if username == ADMIN_USERNAME and msgText.startswith('/add '):
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
                                bot.editMessageText(message, "❌ No se especificó ningún usuario válido.")
                                return

                            # 1. Verificar si alguno está baneado
                            banned_found = [u for u in usernames if u in BANNED_USERS]
                            if banned_found:
                                is_plural_banned = len(banned_found) > 1
                                banned_str = ", ".join([f"@{u}" for u in banned_found])
                                if is_plural_banned:
                                    bot.editMessageText(message, f"❌ Los usuarios {banned_str} están baneados y no se pueden agregar.")
                                else:
                                    bot.editMessageText(message, f"❌ El usuario {banned_str} está baneado y no se puede agregar.")
                                return

                            # 2. Verificar si ya tienen acceso
                            already_has_access = []
                            for u in usernames:
                                if u in expanded_users or jdb.get_user(u) is not None:
                                    already_has_access.append(u)

                            if already_has_access:
                                is_plural_access = len(already_has_access) > 1
                                access_str = ", ".join([f"@{u}" for u in already_has_access])
                                if is_plural_access:
                                    bot.editMessageText(message, f"❌ Los usuarios {access_str} ya tienen acceso al bot.")
                                else:
                                    bot.editMessageText(message, f"❌ El usuario {access_str} ya tiene acceso al bot.")
                                return

                            # 3. Agregar con singular o plural según corresponda
                            is_plural_users = len(usernames) > 1
                            for u in usernames:
                                jdb.create_user(u)
                                u_data = jdb.get_user(u)
                                for key, val in selected_cloud.items():
                                    u_data[key] = val
                                jdb.save_data_user(u, u_data)
                            jdb.save()
                            
                            short_host = selected_cloud['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                            users_str = ", ".join([f"@{u}" for u in usernames])
                            
                            if is_plural_users:
                                msg_text = f"✅ <b>¡Usuarios agregados con éxito!</b>\n\n👥 Usuarios: <code>{users_str}</code>\n☁️ Nube asignada: <code>{short_host}</code>\n⚖️ Límite: <code>{selected_cloud['zips']} MB</code>"
                            else:
                                msg_text = f"✅ <b>¡Usuario agregado con éxito!</b>\n\n👤 Usuario: <code>{users_str}</code>\n☁️ Nube asignada: <code>{short_host}</code>\n⚖️ Límite: <code>{selected_cloud['zips']} MB</code>"
                            
                            bot.editMessageText(message, msg_text, parse_mode='html')
                            return
                        else:
                            bot.editMessageText(message, "❌ Número de nube inválido. Debe ser del 1 al 7.")
                            return
                    else:
                        bot.editMessageText(message, "❌ Formato incorrecto. Use: <code>/add usuario1,usuario2 1</code>", parse_mode='html')
                        return
                else:
                    bot.editMessageText(message, "❌ Formato incorrecto. Use: <code>/add usuario1,usuario2 1</code>", parse_mode='html')
                    return
            except Exception as e:
                bot.editMessageText(message, f"❌ Error al agregar usuarios: {str(e)}")
            return

        # ============================================
        # FLUJO DE CAMBIO DE NUBE CON /cambiar Y NÚMERO
        # ============================================
        if username in CHANGING_CLOUD_USERS:
            if msgText.strip().isdigit():
                num = int(msgText.strip())
                if 1 <= num <= len(AVAILABLE_CLOUDS):
                    selected_cloud = AVAILABLE_CLOUDS[num - 1]
                    short_name = selected_cloud['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                    
                    if user_info.get('moodle_host') == selected_cloud['moodle_host']:
                        CHANGING_CLOUD_USERS.discard(username)
                        bot.editMessageText(message, f"ℹ️ <b>Ya estás usando esta nube</b>\n\n☁️ Nube actual: <code>{short_name}</code>\n⚖️ Límite: <code>{selected_cloud['zips']} MB</code>", parse_mode='html')
                        return
                    
                    for key, val in selected_cloud.items():
                        user_info[key] = val
                    jdb.save_data_user(username, user_info)
                    jdb.save()
                    CHANGING_CLOUD_USERS.discard(username)
                    
                    bot.editMessageText(message, f"✅ <b>¡Nube cambiada exitosamente!</b>\n\n☁️ Nueva nube: <code>{short_name}</code>\n⚖️ Límite: <code>{selected_cloud['zips']} MB</code>", parse_mode='html')
                    return
                else:
                    bot.editMessageText(message, "❌ Número inválido. Envía un número del 1 al 7.")
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
                    
                    if user_info.get('moodle_host') == selected_cloud['moodle_host']:
                        bot.editMessageText(message, f"ℹ️ <b>Ya estás usando esta nube</b>\n\n☁️ Nube actual: <code>{short_name}</code>\n⚖️ Límite: <code>{selected_cloud['zips']} MB</code>", parse_mode='html')
                        return
                    
                    for key, val in selected_cloud.items():
                        user_info[key] = val
                    jdb.save_data_user(username, user_info)
                    jdb.save()
                    bot.editMessageText(message, f"✅ <b>¡Nube cambiada exitosamente!</b>\n\n☁️ Nueva nube: <code>{short_name}</code>\n⚖️ Límite: <code>{selected_cloud['zips']} MB</code>", parse_mode='html')
                    return
            
            menu_msg = "☁️ <b>SELECCIONA TU NUEVA NUBE</b>\n────────────────────────\n\n"
            for i, c in enumerate(AVAILABLE_CLOUDS, 1):
                short = c['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                menu_msg += f"<b>{i}.</b> <code>{short}</code>\n   ⚖️ Límite: {c['zips']} MB\n\n"
            menu_msg += "────────────────────────\n💡 <b>Envía solo el número</b> (1 al 7)."
            
            CHANGING_CLOUD_USERS.add(username)
            bot.editMessageText(message, menu_msg, parse_mode='html')
            return

        # ============================================
        # COMANDO /start MEJORADO
        # ============================================
        if '/start' in msgText:
            if username == ADMIN_USERNAME:
                admin_current_cloud = user_info["moodle_host"].replace('https://', '').replace('http://', '').strip('/')
                start_msg = f"""
👑 <b>USUARIO ADMINISTRADOR</b>

👤 Usuario: @{username}
☁️ Nube actual: <code>{admin_current_cloud}</code>
⚖️ Límite: {user_info["zips"]} MB
🔧 Rol: Administrador

⚠️ <b>NOTA IMPORTANTE:</b>
• Acceso total a todas las nubes
• Gestión de evidencias globales

🎯 <b>COMANDOS PRINCIPALES:</b>
/admin - Panel de administración
/status - Estado de las nubes 🟢/🔴
/procesos - Procesos en tiempo real 🚀
/mantenimiento - Modo mantenimiento 🛠️
/add - Agregar usuario y nube ➕
/ban - Banear usuario 🚫
/unban - Desbanear usuario ✅

📈 <b>ESTADÍSTICAS Y GESTIÓN:</b>
/adm_logs - Logs del sistema
/adm_users - Estadísticas por usuario
/adm_userclouds - Ver nubes y usuarios ☁️
/adm_uploads - Últimas subidas
/adm_deletes - Últimas eliminaciones
/adm_cleardata - Limpiar estadísticas

☁️ <b>GESTIÓN DE NUBES:</b>
/adm_allclouds - Ver todas las nubes
/adm_cloud_X - Nube específica
/adm_show_X_Y - Detalles de evidencia
/adm_fetch_X_Y - Descargar TXT
/adm_delete_X_Y - Eliminar evidencia
/adm_wipe_X - Limpiar nube X
/adm_nuke - Eliminar TODO ⚠️

🔧 <b>TUS COMANDOS PERSONALES:</b>
/cambiar - Cambiar de nube (1 al 7) 🔄
/files - Ver tus evidencias
/txt_X - Ver TXT de tu evidencia
/del_X - Eliminar tu evidencia
/delall - Eliminar tus evidencias
/mystats - Tus estadísticas
                """
            else:
                current_cloud_short = user_info["moodle_host"].replace('https://', '').replace('http://', '').strip('/')
                start_msg = f"""
👤 <b>USUARIO REGULAR</b>

👤 Usuario: @{username}
☁️ Nube actual: <code>{current_cloud_short}</code>
⚖️ Límite: {user_info["zips"]} MB
📁 Evidence: Activado

🔧 <b>TUS COMANDOS:</b>
/start - Ver esta información
/cambiar - Cambiar de nube (1 al 7) 🔄
/status - Estado de tu nube 🟢/🔴
/files - Ver tus evidencias
/txt_X - Ver TXT de evidencia X
/del_X - Eliminar evidencia X
/delall - Eliminar tus evidencias
/mystats - Ver tus estadísticas
                """
            
            bot.editMessageText(message, start_msg, parse_mode='html')
            return

        # ============================================
        # COMANDO /status (SIMPLIFICADO Y SIN PREVIEWS)
        # ============================================
        if '/status' == msgText:
            if username in ACTIVE_STATUS_CHECKS:
                bot.editMessageText(message, "⏳ Ya hay una verificación de estado en curso. Por favor, espera a que termine.")
                return
            
            ACTIVE_STATUS_CHECKS.add(username)
            try:
                if username == ADMIN_USERNAME:
                    bot.editMessageText(message, "🔍 Verificando nubes una a una...")
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
                        status_msg = f"☁️ <code>{clean_url}</code>\nEstado: {icon}"
                        
                        if idx == 0:
                            bot.editMessageText(message, status_msg, parse_mode='html')
                        else:
                            time.sleep(0.4)
                            bot.sendMessage(chat_id, status_msg, parse_mode='html')
                else:
                    bot.editMessageText(message, "🔍 Verificando estado de tu nube...")
                    s = check_single_cloud(user_info)
                    icon = "🟢 En línea" if s['online'] else "🔴 Fuera de línea"
                    clean_url = user_info["moodle_host"].replace('https://', '').replace('http://', '').strip('/')
                    status_msg = f"☁️ <code>{clean_url}</code>\nEstado: {icon}"
                    bot.editMessageText(message, status_msg, parse_mode='html')
            except Exception as e:
                bot.editMessageText(message, f"❌ Error al comprobar el estado de la nube: {str(e)}")
            finally:
                ACTIVE_STATUS_CHECKS.discard(username)
            return

        # === COMANDOS EXCLUSIVOS ADMIN ===
        if username == ADMIN_USERNAME:
            if msgText.startswith('/ban '):
                target = msgText.replace('/ban ', '').replace('@', '').strip()
                
                if target == ADMIN_USERNAME:
                    bot.editMessageText(message, f'🛡️ <b>Acción denegada:</b> No es posible banear al usuario administrador (@{ADMIN_USERNAME}).', parse_mode='html')
                    return
                
                if target not in expanded_users and jdb.get_user(target) is None:
                    bot.editMessageText(message, f'❌ El usuario @{target} no existe en la base de datos ni en los grupos preconfigurados.')
                    return
                
                if target in BANNED_USERS:
                    bot.editMessageText(message, f'ℹ️ El usuario @{target} ya se encuentra baneado en el sistema.')
                    return
                
                BANNED_USERS.add(target)
                bot.editMessageText(message, f'🚫 El usuario @{target} ha sido baneado exitosamente.')
                return
                
            elif msgText.startswith('/unban '):
                target = msgText.replace('/unban ', '').replace('@', '').strip()
                
                if target == ADMIN_USERNAME:
                    bot.editMessageText(message, f'🛡️ <b>Acción denegada:</b> El usuario administrador (@{ADMIN_USERNAME}) no puede ser objetivo de este comando.', parse_mode='html')
                    return
                
                if target not in expanded_users and jdb.get_user(target) is None:
                    bot.editMessageText(message, f'❌ El usuario @{target} no existe en el sistema.')
                    return
                
                if target not in BANNED_USERS:
                    bot.editMessageText(message, f'ℹ️ El usuario @{target} no está baneado actualmente.')
                    return
                
                BANNED_USERS.discard(target)
                bot.editMessageText(message, f'✅ El usuario @{target} ha sido desbaneado exitosamente.')
                return
                
            elif msgText.startswith('/mantenimiento'):
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
                        if p.get('user') == ADMIN_USERNAME:
                            continue
                        try:
                            if hasattr(bot, 'threads') and tid in bot.threads:
                                tcancel = bot.threads[tid]
                                tcancel.store('stop', True)
                                active_msg = tcancel.getStore('msg')
                                if active_msg:
                                    try:
                                        bot.editMessageText(active_msg, '⚠️ Tarea cancelada automáticamente por inicio de mantenimiento del sistema ✗')
                                    except:
                                        pass
                            clean_process(tid)
                            cancel_count += 1
                        except:
                            pass
                
                aviso_cancelados = f"\n⚠️ Se cancelaron y notificaron {cancel_count} proceso(s) activo(s) (excepto administrador)." if cancel_count > 0 else ""
                bot.editMessageText(message, f'🛠️ Modo mantenimiento: {estado}{aviso_cancelados}')
                return
                
            elif msgText == '/procesos':
                if not ACTIVE_PROCESSES:
                    bot.editMessageText(message, "✅ No hay subidas, compresiones o descargas activas en este momento.")
                    return
                
                proc_msg = "🔄 <b>PROCESOS ACTIVOS EN TIEMPO REAL</b>\n────────────────────────\n\n"
                procesos_borrar = []
                
                for tid, p in ACTIVE_PROCESSES.items():
                    tiempo_activo = int(time.time() - p['last_update'])
                    stalled_warning = " ⚠️ (Posiblemente trabado)" if tiempo_activo > 30 and ('📥 Descargando' in p['action'] or '⬆️ Preparando' in p['action']) else ""
                    
                    if tiempo_activo > 60:
                        procesos_borrar.append(tid)
                        continue
                    
                    proc_msg += f"👤 <b>@{p['user']}</b>\n"
                    proc_msg += f"🛠️ Acción: {p['action']}{stalled_warning}\n"
                    proc_msg += f"📄 Archivo: <code>{p['file']}</code>\n"
                    if '🗜️ Comprimiendo' not in p['action'] and '⬆️ Preparando' not in p['action']:
                        proc_msg += f"📊 Progreso: {p['percent']}\n"
                    proc_msg += f"\n"
                
                for tid in procesos_borrar:
                    clean_process(tid)
                
                if len(ACTIVE_PROCESSES) == 0:
                    bot.editMessageText(message, "✅ No hay procesos activos en este momento.")
                else:
                    bot.editMessageText(message, proc_msg, parse_mode="html")
                return

        
        # ============================================
        # COMANDOS DE ADMINISTRADOR (PANEL Y NUBES)
        # ============================================
        if username == ADMIN_USERNAME:
            if msgText == '/admin':
                stats = memory_stats.get_all_stats()
                total_size_formatted = format_file_size(stats['total_size_uploaded'])
                current_date = format_cuba_date()
                
                if memory_stats.has_any_data():
                    admin_msg = f"""
👑 <b>PANEL DE ADMINISTRADOR</b>
📅 {current_date}
────────────────────────
📊 <b>ESTADÍSTICAS GLOBALES:</b>
• Subidas totales: {stats['total_uploads']}
• Eliminaciones totales: {stats['total_deletes']}
• Espacio total subido: {total_size_formatted}
• Nubes configuradas: {len(AVAILABLE_CLOUDS)}

🚀 <b>COMANDOS RÁPIDOS:</b>
/status - Estado de las nubes 🟢/🔴
/procesos - Procesos activos 🚀
/mantenimiento - Activar/Desactivar 🛠️
/add - Agregar usuario y nube ➕
/ban - Banear usuario 🚫
/unban - Desbanear usuario ✅

📈 <b>ESTADÍSTICAS Y USUARIOS:</b>
/adm_logs - Ver últimos logs
/adm_users - Estadísticas por usuario
/adm_userclouds - Ver nubes y usuarios ☁️
/adm_uploads - Últimas subidas
/adm_deletes - Últimas eliminaciones
/adm_cleardata - Limpiar todos los datos

☁️ <b>GESTIÓN DE NUBES:</b>
/adm_allclouds - Ver todas las nubes
/adm_cloud_X - Ver nube específica
/adm_show_X_Y - Detalles de evidencia
/adm_fetch_X_Y - Descargar TXT
/adm_delete_X_Y - Eliminar evidencia
/adm_wipe_X - Limpiar nube X
/adm_nuke - Eliminar TODO ⚠️

🔧 <b>OTROS:</b>
/start - Información de usuario
────────────────────────
🕐 Hora Cuba: {format_cuba_datetime()}
                    """
                else:
                    admin_msg = f"""
👑 <b>PANEL DE ADMINISTRADOR</b>
📅 {current_date}
────────────────────────
⚠️ <b>NO HAY DATOS REGISTRADOS</b>
Aún no se ha realizado ninguna acción en el bot.

📊 Nubes configuradas: {len(AVAILABLE_CLOUDS)}

🚀 <b>COMANDOS RÁPIDOS:</b>
/status - Estado de las nubes 🟢/🔴
/procesos - Procesos activos 🚀
/mantenimiento - Activar/Desactivar 🛠️
/add - Agregar usuario y nube ➕
/ban - Banear usuario 🚫
/unban - Desbanear usuario ✅

📈 <b>ESTADÍSTICAS Y USUARIOS:</b>
/adm_logs - Ver últimos logs
/adm_users - Estadísticas por usuario
/adm_userclouds - Ver nubes y usuarios ☁️
/adm_uploads - Últimas subidas
/adm_deletes - Últimas eliminaciones

☁️ <b>GESTIÓN DE NUBES:</b>
/adm_allclouds - Ver todas las nubes
/adm_cloud_X - Ver nube específica
/adm_show_X_Y - Detalles de evidencia
/adm_fetch_X_Y - Descargar TXT

🔧 <b>OTROS:</b>
/start - Información de usuario
────────────────────────
🕐 Hora Cuba: {format_cuba_datetime()}
                    """
                
                bot.editMessageText(message, admin_msg, parse_mode='html')
                return
            
            elif '/adm_' in msgText:
                if msgText == '/adm_userclouds':
                    try:
                        uclouds_msg = "☁️ <b>GESTIÓN DE NUBES Y USUARIOS</b>\n────────────────────────\n\n"
                        
                        # Recorrer de forma fija las AVAILABLE_CLOUDS para mantener siempre el orden del 1 al 7 y consultar DB en tiempo real
                        for idx, cloud_cfg in enumerate(AVAILABLE_CLOUDS, 1):
                            target_host = cloud_cfg.get('moodle_host', '')
                            zips = cloud_cfg.get('zips', '?')
                            short = target_host.replace('https://', '').replace('http://', '').strip('/')
                            
                            assigned_users = []
                            for u in expanded_users.keys():
                                u_info = jdb.get_user(u)
                                current_host = u_info.get('moodle_host', '') if u_info else cloud_cfg.get('moodle_host', '')
                                if current_host == target_host:
                                    assigned_users.append(u.lstrip('@'))
                            
                            users_str = ", ".join(assigned_users) if assigned_users else "Ninguno"
                            
                            uclouds_msg += f"🌐 <b>Nube {idx}:</b> <code>{short}</code>\n"
                            uclouds_msg += f"⚖️ <b>Límite:</b> {zips} MB\n"
                            uclouds_msg += f"👤 <b>Usuarios:</b> {users_str}\n"
                            uclouds_msg += f"────────────────────────\n\n"
                        
                        send_long_message(bot, chat_id, uclouds_msg, original_message=message, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error al obtener nubes y usuarios: {str(e)}')
                    return

                elif '/adm_allclouds' in msgText:
                    try:
                        show_loading_progress(bot, message, 1, 3)
                        total_evidences = admin_evidence_manager.refresh_data()
                        show_loading_progress(bot, message, 2, 3)
                        
                        if total_evidences == 0:
                            empty_msg = f"""
👑 TODAS LAS NUBES
────────────────────────
📊 RESUMEN GENERAL:
• Nubes configuradas: {len(AVAILABLE_CLOUDS)}
• Evidencias totales: 0
• Archivos totales: 0
────────────────────────
✅ Todas las nubes están vacías
                            """
                            bot.editMessageText(message, empty_msg)
                            return
                        
                        total_clouds = len(admin_evidence_manager.clouds_dict)
                        total_files = 0
                        
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            for ev in evidences:
                                total_files += ev['files_count']
                        
                        menu_msg = f"""
👑 GESTIÓN DE TODAS LAS NUBES
────────────────────────
📊 RESUMEN GENERAL:
• Nubes: {total_clouds}
• Evidencias totales: {total_evidences}
• Archivos totales: {total_files}

📋 NUBES DISPONIBLES:"""
                        
                        cloud_index = 0
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            cloud_files = sum(ev['files_count'] for ev in evidences)
                            short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                            
                            menu_msg += f"\n\n{cloud_index}. <code>{short_name}</code>"
                            menu_msg += f"\n   📁 {len(evidences)} evidencias, {cloud_files} archivos"
                            menu_msg += f"\n   🔍 /adm_cloud_{cloud_index}"
                            
                            if len(evidences) > 0:
                                menu_msg += f"\n   🗑️ /adm_wipe_{cloud_index}"
                            
                            cloud_index += 1
                        
                        show_loading_progress(bot, message, 3, 3)
                        
                        if total_evidences > 0:
                            menu_msg += f"""

────────────────────────
🔧 OPCIONES MASIVAS:
/adm_nuke - ⚠️ Eliminar TODO
────────────────────────
ℹ️ Usa /adm_cloud_X para ver evidencias
                            """
                        else:
                            menu_msg += f"""

────────────────────────
✅ Todas las nubes están vacías
────────────────────────
                            """
                        
                        bot.editMessageText(message, menu_msg, parse_mode='html')
                        
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                elif '/adm_cloud_' in msgText:
                    try:
                        cloud_idx = extract_one_param_simple(msgText, '/adm_cloud_')
                        if cloud_idx is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_cloud_0')
                            return
                        
                        admin_evidence_manager.refresh_data()
                        
                        if cloud_idx < 0 or cloud_idx >= len(admin_evidence_manager.clouds_dict):
                            bot.editMessageText(message, f'❌ Índice inválido. Máximo: {len(admin_evidence_manager.clouds_dict)-1}')
                            return
                        
                        cloud_name = list(admin_evidence_manager.clouds_dict.keys())[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict[cloud_name]
                        short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                        
                        if not evidences:
                            empty_msg = f"""
📭 NUBE VACÍA
────────────────────────
☁️ <code>{short_name}</code>
📊 No hay evidencias en esta nube.
────────────────────────
                            """
                            bot.editMessageText(message, empty_msg, parse_mode='html')
                            return
                        
                        list_msg = f"""
📋 EVIDENCIAS DE LA NUBE
☁️ <code>{short_name}</code>
────────────────────────

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
                            
                            list_msg += f"{idx}. {clean_name[:35]}"
                            if len(clean_name) > 35:
                                list_msg += "..."
                            list_msg += f"{user_str}\n"
                            list_msg += f"   📁 {evidence['files_count']} archivos\n"
                            list_msg += f"   👁️ /adm_show_{cloud_idx}_{idx}\n"
                            list_msg += f"   📄 /adm_fetch_{cloud_idx}_{idx}\n"
                            list_msg += f"   🗑️ /adm_delete_{cloud_idx}_{idx}\n\n"
                        
                        total_evidences = len(evidences)
                        total_files = sum(e['files_count'] for e in evidences)
                        
                        list_msg += f"""
────────────────────────
🔧 ACCIÓN MASIVA:
/adm_wipe_{cloud_idx} - Eliminar TODO

📊 RESUMEN:
• Evidencias: {total_evidences}
• Archivos: {total_files}
────────────────────────
                        """
                        
                        send_long_message(bot, message.chat.id, list_msg, original_message=message, parse_mode='html')
                        
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                elif '/adm_show_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_show_')
                        if params is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_show_0_1')
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
👁️ DETALLES DE EVIDENCIA
────────────────────────
📝 Nombre: {clean_name}
📁 Archivos: {evidence['files_count']}
☁️ Nube: <code>{short_name}</code>

🔧 ACCIONES:
📄 /adm_fetch_{cloud_idx}_{evid_idx} - TXT
🗑️ /adm_delete_{cloud_idx}_{evid_idx} - Eliminar
────────────────────────
                            """
                            bot.editMessageText(message, show_msg, parse_mode='html')
                        else:
                            bot.editMessageText(message, '❌ No se encontró la evidencia')
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                elif '/adm_fetch_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_fetch_')
                        if params is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_fetch_0_1')
                            return
                        
                        cloud_idx, evid_idx = params
                        bot.editMessageText(message, '📄 Obteniendo archivo TXT...')
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
                                bot.editMessageText(message, f'✅ TXT enviado: {clean_name[:50]}')
                            else:
                                bot.editMessageText(message, '❌ No se encontró la evidencia')
                        else:
                            bot.editMessageText(message, '❌ No hay archivos en esta evidencia')
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                elif '/adm_delete_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_delete_')
                        if params is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_delete_0_1')
                            return
                        
                        cloud_idx, evid_idx = params
                        bot.editMessageText(message, '🔍 Verificando datos...')
                        
                        admin_evidence_manager.refresh_data()
                        cloud_names = list(admin_evidence_manager.clouds_dict.keys())
                        
                        if cloud_idx < 0 or cloud_idx >= len(cloud_names):
                            bot.editMessageText(message, f'❌ Índice de nube inválido')
                            show_updated_all_clouds(bot, message)
                            return
                        
                        cloud_name = cloud_names[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict.get(cloud_name, [])
                        
                        if not evidences:
                            bot.editMessageText(message, f'📭 La nube {cloud_idx} ya está vacía')
                            show_updated_all_clouds(bot, message)
                            return
                        
                        if evid_idx < 0 or evid_idx >= len(evidences):
                            bot.editMessageText(message, f'❌ Índice de evidencia inválido')
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
                        bot.editMessageText(message, f'🗑️ Eliminando evidencia: {clean_name[:50]}...')
                        
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
✅ ELIMINACIÓN EXITOSA
────────────────────────
🗑️ Evidencia: {clean_name[:50]}
📁 Archivos eliminados: {files_count}
☁️ Nube: <code>{short_name}</code>
────────────────────────
                                    """
                                    bot.editMessageText(message, result_msg, parse_mode='html')
                                    time.sleep(1)
                                    show_updated_cloud(bot, message, cloud_idx)
                                else:
                                    result_msg = f"""
✅ ELIMINACIÓN COMPLETA
────────────────────────
🗑️ Última evidencia eliminada
📁 Archivos borrados: {files_count}
────────────────────────
                                    """
                                    bot.editMessageText(message, result_msg, parse_mode='html')
                                    time.sleep(1)
                                    show_updated_all_clouds(bot, message)
                            else:
                                show_updated_all_clouds(bot, message)
                        else:
                            bot.editMessageText(message, f'❌ Error al eliminar: {clean_name}')
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                elif '/adm_wipe_' in msgText:
                    try:
                        cloud_idx = extract_one_param_simple(msgText, '/adm_wipe_')
                        if cloud_idx is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_wipe_0')
                            return
                        
                        if cloud_idx < 0 or cloud_idx >= len(admin_evidence_manager.clouds_dict):
                            bot.editMessageText(message, f'❌ Índice inválido. Máximo: {len(admin_evidence_manager.clouds_dict)-1}')
                            return
                        
                        cloud_name = list(admin_evidence_manager.clouds_dict.keys())[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict[cloud_name]
                        
                        if not evidences:
                            bot.editMessageText(message, f'📭 La nube {cloud_idx} ya está vacía')
                            return
                        
                        short_name = cloud_name.replace('https://', '').replace('http://', '').strip('/')
                        bot.editMessageText(message, f'💣 Limpiando nube <code>{short_name}</code>...', parse_mode='html')
                        
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
💥 LIMPIEZA EXITOSA
────────────────────────
✅ Nube: <code>{short_name}</code>
✅ Evidencias: {deleted_count}
✅ Archivos: {total_files}
────────────────────────
                                """
                                bot.editMessageText(message, result_msg, parse_mode='html')
                                time.sleep(1)
                                show_updated_all_clouds(bot, message)
                            else:
                                bot.editMessageText(message, f'❌ Error al limpiar {short_name}')
                        else:
                            bot.editMessageText(message, '❌ No se encontró configuración')
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                elif '/adm_nuke' in msgText:
                    try:
                        total_evidences = len(admin_evidence_manager.current_list)
                        if total_evidences == 0:
                            bot.editMessageText(message, '📭 No hay evidencias para eliminar')
                            return
                        
                        bot.editMessageText(message, '💣💣💣 ELIMINANDO TODO...')
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
                                    results.append(f"✅ <code>{short_name}</code>: {deleted_count} ev., {total_files} arch.")
                                else:
                                    results.append(f"❌ <code>{short_name}</code>: Error")
                        
                        admin_evidence_manager.refresh_data(force=True)
                        final_msg = f"""
💥 <b>ELIMINACIÓN MASIVA COMPLETADA</b>
────────────────────────
📊 Evidencias: {deleted_total}
📁 Archivos: {files_total}
────────────────────────
"""
                        for result in results:
                            final_msg += f"\n{result}"
                        bot.editMessageText(message, final_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                elif '/adm_logs' in msgText:
                    try:
                        if not memory_stats.has_any_data():
                            bot.editMessageText(message, "⚠️ No hay datos registrados.")
                            return
                        
                        limit = 300
                        if '_' in msgText:
                            try:
                                limit = int(msgText.split('_')[2])
                            except: pass
                        
                        uploads = memory_stats.get_recent_uploads(limit)
                        deletes = memory_stats.get_recent_deletes(limit)
                        
                        logs_msg = "📋 <b>ÚLTIMOS LOGS</b>\n────────────────────────\n\n"
                        if uploads:
                            logs_msg += "⬆️ <b>SUBIDAS:</b>\n"
                            for log in uploads:
                                logs_msg += f"• {log['timestamp']} - @{log['username']}: {log['filename']} ({log['file_size_formatted']})\n"
                            logs_msg += "\n"
                        if deletes:
                            logs_msg += "🗑️ <b>ELIMINACIONES:</b>\n"
                            for log in deletes:
                                if log['type'] == 'delete_all':
                                    logs_msg += f"• {log['timestamp']} - @{log['username']}: ELIMINÓ TODO ({log.get('deleted_evidences', 1)} ev.)\n"
                                else:
                                    logs_msg += f"• {log['timestamp']} - @{log['username']}: {log['filename']}\n"
                        
                        if len(logs_msg) > 4000:
                            logs_msg = logs_msg[:4000] + "\n\n⚠️ Truncado"
                        bot.editMessageText(message, logs_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al obtener logs: {str(e)}")
                    return
                
                elif '/adm_users' in msgText:
                    try:
                        users = memory_stats.get_all_users()
                        if not users:
                            bot.editMessageText(message, "⚠️ No hay usuarios registrados.")
                            return
                        
                        users_msg = "👥 <b>ESTADÍSTICAS POR USUARIO</b>\n────────────────────────\n\n"
                        for user, data in sorted(users.items(), key=lambda x: x[1]['uploads'], reverse=True):
                            total_size_formatted = format_file_size(data['total_size'])
                            users_msg += f"👤 <b>@{user}</b>\n   📤 Subidas: {data['uploads']}\n   🗑️ Eliminaciones: {data['deletes']}\n   💾 Espacio: {total_size_formatted}\n\n"
                        
                        if len(users_msg) > 4000:
                            users_msg = users_msg[:4000] + "\n\n⚠️ Truncado"
                        bot.editMessageText(message, users_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al obtener usuarios: {str(e)}")
                    return
                
                elif '/adm_uploads' in msgText:
                    try:
                        uploads = memory_stats.get_recent_uploads(15)
                        if not uploads:
                            bot.editMessageText(message, "⚠️ No hay subidas registradas.")
                            return
                        
                        uploads_msg = "📤 <b>ÚLTIMAS SUBIDAS</b>\n────────────────────────\n\n"
                        for i, log in enumerate(uploads, 1):
                            uploads_msg += f"{i}. <code>{log['filename']}</code>\n   👤 @{log['username']} | 📏 {log['file_size_formatted']}\n\n"
                        bot.editMessageText(message, uploads_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al obtener subidas: {str(e)}")
                    return
                
                elif '/adm_deletes' in msgText:
                    try:
                        deletes = memory_stats.get_recent_deletes(15)
                        if not deletes:
                            bot.editMessageText(message, "⚠️ No hay eliminaciones registradas.")
                            return
                        
                        deletes_msg = "🗑️ <b>ÚLTIMAS ELIMINACIONES</b>\n────────────────────────\n\n"
                        for i, log in enumerate(deletes, 1):
                            if log['type'] == 'delete_all':
                                deletes_msg += f"{i}. ELIMINACIÓN MASIVA\n   👤 @{log['username']} ({log.get('deleted_evidences', 1)} ev.)\n\n"
                            else:
                                deletes_msg += f"{i}. {log['filename']}\n   👤 @{log['username']}\n\n"
                        bot.editMessageText(message, deletes_msg, parse_mode='html')
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al obtener eliminaciones: {str(e)}")
                    return
                
                elif '/adm_cleardata' in msgText:
                    try:
                        if not memory_stats.has_any_data():
                            bot.editMessageText(message, "⚠️ No hay datos para limpiar.")
                            return
                        result = memory_stats.clear_all_data()
                        bot.editMessageText(message, f"✅ {result}")
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al limpiar datos: {str(e)}")
                    return
        
        # ============================================
        # COMANDOS REGULARES DE USUARIO
        # ============================================
        
        if '/mystats' in msgText:
            user_stats = memory_stats.get_user_stats(username)
            if user_stats:
                total_size_formatted = format_file_size(user_stats['total_size'])
                stats_msg = f"""
📊 <b>TUS ESTADÍSTICAS</b>
────────────────────────
👤 Usuario: @{username}
📤 Subidas: {user_stats['uploads']}
🗑️ Eliminaciones: {user_stats['deletes']}
💾 Espacio usado: {total_size_formatted}
📅 Última actividad: {user_stats['last_activity']}
────────────────────────
                """
            else:
                stats_msg = f"""
📊 <b>TUS ESTADÍSTICAS</b>
────────────────────────
👤 Usuario: @{username}
📤 Subidas: 0
🗑️ Eliminaciones: 0
💾 Espacio usado: 0 B
────────────────────────
ℹ️ Aún no tienes actividad registrada.
                """
            bot.editMessageText(message, stats_msg, parse_mode='html')
            return
        
        elif '/files' == msgText:
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
            loged = client.login()
            if loged:
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
                    files_msg = "📁 <b>TUS EVIDENCIAS</b>\n────────────────────────\n\n"
                    for idx, item in enumerate(visible_list):
                        files_msg += f"• {item['name']} [ {item['file_count']} ]\n  /txt_{idx} | /del_{idx}\n\n"
                    files_msg += f"────────────────────────\nTotal: {len(visible_list)} evidencia(s)"
                    bot.editMessageText(message, files_msg, parse_mode='html')
                else:
                    bot.editMessageText(message, '📭 No hay evidencias disponibles')
                client.logout()
            else:
                bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
                
        elif '/txt_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],proxy=proxy)
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
                        bot.editMessageText(message, '❌ Índice inválido. Use /files para ver la lista.')
                        client.logout()
                        return
                    
                    evindex = visible_list[findex]['original']
                    clean_name = visible_list[findex]['clean_name']
                    txtname = clean_name + '.txt'
                    sendTxt(txtname, evindex['files'], update, bot)
                    client.logout()
                    bot.editMessageText(message,'📄 TXT Aquí')
                else:
                    bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except ValueError:
                bot.editMessageText(message, '❌ Formato incorrecto. Use: /txt_0')
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
             
        elif '/del_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
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
                        bot.editMessageText(message, '❌ Índice inválido. Use /files para ver la lista.')
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
                    
                    confirmation_msg = f"🗑️ <b>Evidencia eliminada:</b> {evidence_clean_name}\n📁 Archivos borrados: {file_count}\n────────────────────────\n"
                    if len(updated_visible_list) > 0:
                        confirmation_msg += "📋 <b>Tus evidencias actualizadas:</b>\n\n"
                        for idx, item in enumerate(updated_visible_list):
                            clean_name = item['clean_name']
                            item_file_count = len(item['original']['files']) if 'files' in item['original'] else 0
                            confirmation_msg += f"• {clean_name} [ {item_file_count} ]\n  /txt_{idx} | /del_{idx}\n\n"
                        bot.editMessageText(message, confirmation_msg, parse_mode='html')
                    else:
                        confirmation_msg += "📭 No hay evidencias disponibles"
                        bot.editMessageText(message, confirmation_msg, parse_mode='html')
                else:
                    bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except ValueError:
                bot.editMessageText(message, '❌ Formato incorrecto. Use: /del_0')
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                
        elif '/delall' in msgText:
            try:
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
                loged = client.login()
                if loged:
                    all_evidences = client.getEvidences()
                    user_evidences = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            user_evidences.append(ev)
                    
                    if not user_evidences:
                        bot.editMessageText(message, '📭 No hay evidencias disponibles')
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
                    
                    deletion_msg = f"🗑️ <b>ELIMINACIÓN MASIVA COMPLETADA</b>\n────────────────────────\n• Evidencias eliminadas: {total_evidences}\n• Archivos borrados: {total_files}\n\n✅ ¡Todas tus evidencias han sido eliminadas!"
                    bot.editMessageText(message, deletion_msg, parse_mode='html')
                else:
                    bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                
        elif 'http' in msgText:
            url = msgText
            funny_message_sent = None
            file_size = 0
            file_size_mb = 0
            filename = url.split('/')[-1] or "Desconocido"
            
            try:
                headers = {}
                if user_info['proxy']:
                    proxy_dict = ProxyCloud.parse(user_info['proxy'])
                    if 'http' in proxy_dict:
                        headers.update({'Proxy': proxy_dict['http']})
                
                response = requests.head(url, allow_redirects=True, timeout=5, headers=headers)
                file_size = int(response.headers.get('content-length', 0))
                file_size_mb = file_size / (1024 * 1024)
                
                cd = response.headers.get('content-disposition')
                if cd and 'filename=' in cd:
                    filename = cd.split('filename=')[1].strip('"\'')
                else:
                    filename = unquote(filename)
                
                if file_size_mb > 500:
                    funny_message = get_random_large_file_message()
                    warning_msg = bot.sendMessage(chat_id, f"⚠️ {funny_message}\n\n❌ Cojoneee, tú piensas q esto es una nube artificial o q? Para q tú quieres subir {file_size_mb:.2f} MB?\n\n⬆️ Bueno, lo subiré😡")
                    funny_message_sent = warning_msg
            except: pass
            
            if LOG_GROUP_ID != 0:
                try:
                    clean_host = user_info['moodle_host'].replace('https://', '').replace('http://', '').strip('/')
                    tamano_formateado = format_file_size(file_size) if file_size > 0 else "Desconocido"
                    mensaje_log = (f"🔔 <b>¡Nuevo enlace recibido!</b>\n👤 Usuario: @{username}\n📄 Archivo: <code>{filename}</code>\n⚖️ Peso: {tamano_formateado}\n🔗 Enlace: <code>{url}</code>\n☁️ Nube: <code>{clean_host}</code>")
                    bot.sendMessage(LOG_GROUP_ID, mensaje_log, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar enlace: {e}")
            
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
            
            if funny_message_sent:
                delete_message_after_delay(bot, funny_message_sent.chat.id, funny_message_sent.message_id, 8)
        else:
            bot.editMessageText(message,'➲ No se pudo procesar ✗ ')
            
    except Exception as ex:
        print(f"Error general en onmessage: {str(ex)}")
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