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
ADMIN_CHAT_ID = 7363341763  # Tu ID para notificaciones

# VARIABLES GLOBALES DE CONTROL
MAINTENANCE_MODE = False
BANNED_USERS = set()

# CUBA TIMEZONE
try:
    CUBA_TZ = pytz.timezone('America/Havana')
except:
    CUBA_TZ = None

# SEPARATOR FOR USER EVIDENCES
USER_EVIDENCE_MARKER = " "  # Space as separator

# PRE-CONFIGURACIÓN DE USUARIOS
PRE_CONFIGURATED_USERS = {
    "Thali355,Eliel_21,Kev_inn10": {
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
    "thu,gatitoo_miauu,Satoru_2115,jc041228,SchnauzerMinnie": {
        "cloudtype": "moodle",
        "moodle_host": "https://cursos.uo.edu.cu/",
        "moodle_repo_id": 4,
        "moodle_user": "desiderio.vazquez",
        "moodle_password": "ThaliEliel1521.",
        "zips": 99,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    "VanNeiFertio,XD": {
        "cloudtype": "moodle",
        "moodle_host": "https://cursos.ucf.edu.cu/",
        "moodle_repo_id": 4,
        "moodle_user": "eliel2216",
        "moodle_password": "Et543210.",
        "zips": 49,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    }
}

# ==============================
# SISTEMA DE CACHÉ PARA OPTIMIZACIÓN
# ==============================

class CloudCache:
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
    return dt.strftime("%d/%m/%y %I:%M %p")

def format_file_size(size_bytes):
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
    
    def log_upload(self, username, filename, file_size, moodle_host):
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
        return "✅ Todos los datos han sido eliminados"

memory_stats = MemoryStats()

def get_random_large_file_message():
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
        "¡500MB detectados! ¿Traes la biblioteca de Alejandría en un ZIP? 📚"
    ]
    return random.choice(messages)

def expand_user_groups():
    expanded = {}
    for user_group, config in PRE_CONFIGURATED_USERS.items():
        users = [u.strip() for u in user_group.split(',')]
        for user in users:
            expanded[user] = config.copy()
    return expanded

# ==============================
# FUNCIÓN PARA DIVIDIR MENSAJES LARGOS
# ==============================
def send_long_message(bot, chat_id, text, original_message=None):
    MAX_LEN = 4000
    if len(text) <= MAX_LEN:
        if original_message:
            bot.editMessageText(original_message, text)
        else:
            bot.sendMessage(chat_id, text)
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
        bot.editMessageText(original_message, messages_to_send[0])
    else:
        bot.sendMessage(chat_id, messages_to_send[0])
        
    for msg_part in messages_to_send[1:]:
        time.sleep(0.5)
        bot.sendMessage(chat_id, msg_part)


def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

# CORRECCIÓN DE BUG 1: try..finally añadido para evitar fugas de disco
def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'⬆️ Preparando Para Subir ☁ ●●○')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        proxy = ProxyCloud.parse(user_info['proxy'])
        
        client = MoodleClient(user_info['moodle_user'],
                              user_info['moodle_password'],
                              user_info['moodle_host'],
                              user_info['moodle_repo_id'],
                              proxy=proxy)
        loged = client.login()
        if loged:
            evidences = client.getEvidences()
            username = update.message.sender.username
            
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
                try:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    tokenize = False
                    if user_info['tokenize']!=0:
                       tokenize = True
                    
                    # CORRECCIÓN: Sistema de reintentos más inteligente
                    while resp is None and iter < 10:
                        try:
                            fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                            if resp is None:
                                time.sleep(2) # Pausa si falla antes del reintento
                        except:
                            time.sleep(2)
                        iter += 1
                        
                    if resp is not None:
                        draftlist.append(resp)
                finally:
                    # Garantizamos que el archivo se borra SIEMPRE del servidor, haya error o no
                    if os.path.exists(f):
                        try:
                            os.unlink(f)
                        except: pass
            
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
        file_size = get_file_size(file)
        getUser = jdb.get_user(update.message.sender.username)
        max_file_size = 1024 * 1024 * getUser['zips']
        file_upload_count = 0
        client = None
        
        username = update.message.sender.username
        
        if file_size > max_file_size:
            compresingInfo = infos.createCompresing(file,file_size,max_file_size)
            bot.editMessageText(message,compresingInfo)
            zipname = str(file).split('.')[0] + createID()
            mult_file = zipfile.MultiFile(zipname,max_file_size)
            zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
            zip.write(file)
            zip.close()
            mult_file.close()
            client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
            try:
                os.unlink(file)
            except:pass
            file_upload_count = len(mult_file.files)
        else:
            client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
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
            
            if len(files)>0:
                txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
                sendTxt(txtname,files,update,bot)
        else:
            bot.editMessageText(message,'➥ Error en la página ✗')
    finally:
        # Asegurarnos de limpiar el archivo original descargado
        if os.path.exists(file):
            try: os.unlink(file)
            except: pass

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            try:
                bot.editMessageText(message,'➥ Error en la descarga ✗')
            except:
                pass

def sendTxt(name,files,update,bot):
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
    bot.sendFile(update.message.chat.id,name)
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
            proxy_parsed = ProxyCloud.parse(proxy)
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
        
        proxy_parsed = ProxyCloud.parse(proxy)
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
        
        proxy_parsed = ProxyCloud.parse(proxy)
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
                
                proxy_parsed = ProxyCloud.parse(proxy)
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
            short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
            empty_msg = f"""
📭 NUBE VACÍA
━━━━━━━━━━━━━━━━━━━

✅ ELIMINACIÓN COMPLETA
☁️ {short_name}

🎉 ¡Has eliminado todas las evidencias de esta nube!

🔄 Regresando a todas las nubes...
━━━━━━━━━━━━━━━━━━━
            """
            bot.editMessageText(message, empty_msg)
            time.sleep(1.5)
            show_updated_all_clouds(bot, message)
            return
        
        short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
        
        list_msg = f"📋 NUBE ACTUALIZADA\n☁️ {short_name}\n━━━━━━━━━━━━━━━━━━━\n\n"
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
━━━━━━━━━━━━━━━━━━━
🔧 ACCIONES MASIVAS:
/adm_wipe_{cloud_idx} - Eliminar TODO de esta nube

📊 RESUMEN:
• Evidencias: {total_evidences}
• Archivos: {total_files}
━━━━━━━━━━━━━━━━━━━
        """
        
        send_long_message(bot, message.chat.id, list_msg, original_message=message)
        
    except Exception as e:
        error_msg = f"""
❌ ERROR AL ACTUALIZAR
━━━━━━━━━━━━━━━━━━━

⚠️ No se pudo mostrar la nube actualizada.

🔧 Solución:
Usa /adm_allclouds para ver todas las nubes disponibles

━━━━━━━━━━━━━━━━━━━
        """
        bot.editMessageText(message, error_msg)

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
👑 TODAS LAS NUBES ACTUALIZADAS
━━━━━━━━━━━━━━━━━━━

📊 RESUMEN GENERAL:
• Nubes: {total_clouds}
• Evidencias totales: 0
• Archivos totales: 0

━━━━━━━━━━━━━━━━━━━
✅ Todas las nubes están vacías
📭 No hay evidencias para eliminar
━━━━━━━━━━━━━━━━━━━
            """
            bot.editMessageText(message, empty_msg)
            return
        
        menu_msg = f"""
👑 TODAS LAS NUBES ACTUALIZADAS
━━━━━━━━━━━━━━━━━━━

📊 RESUMEN GENERAL:
• Nubes: {total_clouds}
• Evidencias totales: {total_evidences}
• Archivos totales: {total_files}

📋 NUBES DISPONIBLES:"""
        
        cloud_index = 0
        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
            cloud_files = sum(ev['files_count'] for ev in evidences)
            short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
            
            menu_msg += f"\n\n{cloud_index}. {short_name}"
            menu_msg += f"\n   📁 {len(evidences)} evidencias, {cloud_files} archivos"
            menu_msg += f"\n   🔍 /adm_cloud_{cloud_index}"
            
            if len(evidences) > 0:
                menu_msg += f"\n   🗑️ /adm_wipe_{cloud_index}"
            
            cloud_index += 1
        
        if total_evidences > 0:
            menu_msg += f"""

━━━━━━━━━━━━━━━━━━━
🔧 OPCIONES MASIVAS:
/adm_nuke - ⚠️ Eliminar TODO (peligro)
━━━━━━━━━━━━━━━━━━━
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
# FUNCIÓN ONMESSAGE
# ==============================
def onmessage(update,bot:ObigramClient):
    global MAINTENANCE_MODE, BANNED_USERS
    
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        
        msgText = ''
        try: msgText = update.message.text
        except:pass

        # === NUEVO: SISTEMA DE BANEO Y MANTENIMIENTO ===
        if username in BANNED_USERS and username != ADMIN_USERNAME:
            bot.sendMessage(update.message.chat.id, '🚫 Has sido baneado y no puedes usar este bot.')
            return
            
        if MAINTENANCE_MODE and username != ADMIN_USERNAME:
            bot.sendMessage(update.message.chat.id, '🛠️ El bot se encuentra en mantenimiento temporal. Por favor, intenta más tarde.')
            return

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()
        
        expanded_users = expand_user_groups()
        
        if username not in expanded_users:
            bot.sendMessage(update.message.chat.id,'➲ No tienes acceso a este bot ✗')
            return
        
        initialize_database(jdb)
        
        user_info = jdb.get_user(username)
        if user_info is None:
            config = expanded_users[username]
            jdb.create_user(username)
            user_info = jdb.get_user(username)
            for key, value in config.items():
                user_info[key] = value
            jdb.save_data_user(username, user_info)
            jdb.save()

        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'➲ Tarea Cancelada ✗ ')
            except Exception as ex:
                print(str(ex))
            return
            
        # === COMANDOS EXCLUSIVOS ADMIN ===
        if username == ADMIN_USERNAME:
            if msgText.startswith('/ban '):
                target = msgText.replace('/ban ', '').replace('@', '').strip()
                BANNED_USERS.add(target)
                bot.sendMessage(update.message.chat.id, f'🚫 El usuario @{target} ha sido baneado.')
                return
                
            elif msgText.startswith('/unban '):
                target = msgText.replace('/unban ', '').replace('@', '').strip()
                BANNED_USERS.discard(target)
                bot.sendMessage(update.message.chat.id, f'✅ El usuario @{target} ha sido desbaneado.')
                return
                
            elif msgText == '/mantenimiento':
                MAINTENANCE_MODE = not MAINTENANCE_MODE
                estado = "ACTIVADO 🔴" if MAINTENANCE_MODE else "DESACTIVADO 🟢"
                bot.sendMessage(update.message.chat.id, f'🛠️ Modo mantenimiento: {estado}\nLos usuarios normales no podrán usar el bot hasta que lo desactives.')
                return

        message = bot.sendMessage(update.message.chat.id,'➲ Procesando ✪ ●●○')
        thread.store('msg',message)

        if '/start' in msgText:
            if username == ADMIN_USERNAME:
                start_msg = f"""
👑 USUARIO ADMINISTRADOR

👤 Usuario: @{username}
🔧 Rol: Administrador

⚠️ NOTA IMPORTANTE:
• Tienes acceso de administrador a TODAS las nubes
• Puedes gestionar evidencias de todos los usuarios

🎯 COMANDOS PRINCIPALES:
/admin - Panel principal de administración
/mantenimiento - Activar/Desactivar bot
/ban @usuario - Bloquear a alguien
/unban @usuario - Desbloquear a alguien

📈 COMANDOS DE ESTADÍSTICAS:
/adm_logs - Ver logs del sistema
/adm_users - Ver usuarios y estadísticas
/adm_uploads - Ver últimas subidas
/adm_cleardata - Limpiar estadísticas

☁️ COMANDOS DE GESTIÓN DE NUBES:
/adm_allclouds - Ver todas las nubes
/adm_cloud_X - Ver nube específica

🔗 FileToLink: @fileeliellinkBot
                """
            else:
                start_msg = f"""
👤 USUARIO REGULAR

👤 Usuario: @{username}
☁️ Nube: Moodle
📁 Evidence: Activado
🔗 Host: {user_info["moodle_host"]}

🔧 TUS COMANDOS:
/start - Ver esta información
/files - Ver tus evidencias
/txt_X - Ver TXT de evidencia X
/del_X - Eliminar evidencia X
/delall - Eliminar todas tus evidencias
/mystats - Ver tus estadísticas

🔗 FileToLink: @fileeliellinkBot
                """
            
            bot.editMessageText(message, start_msg)
            return
        
        if username == ADMIN_USERNAME:
            if msgText == '/admin':
                stats = memory_stats.get_all_stats()
                total_size_formatted = format_file_size(stats['total_size_uploaded'])
                current_date = format_cuba_date()
                estado_mantenimiento = "ACTIVADO 🔴" if MAINTENANCE_MODE else "DESACTIVADO 🟢"
                
                admin_msg = f"""
👑 PANEL DE ADMINISTRADOR
📅 {current_date}
━━━━━━━━━━━━━━━━━━━
🛠️ Mantenimiento: {estado_mantenimiento}
🚫 Baneados actuales: {len(BANNED_USERS)}

📊 ESTADÍSTICAS GLOBALES:
• Subidas totales: {stats['total_uploads']}
• Eliminaciones totales: {stats['total_deletes']}
• Espacio total subido: {total_size_formatted}

📈 COMANDOS:
/adm_logs - Ver últimos logs
/adm_users - Ver estadísticas por usuario
/adm_uploads - Ver últimas subidas
/adm_cleardata - Limpiar todos los datos

☁️ NUBES:
/adm_allclouds - Ver todas las nubes
━━━━━━━━━━━━━━━━━━━
🕐 Hora Cuba: {format_cuba_datetime()}
                """
                
                bot.editMessageText(message, admin_msg)
                return
            
            elif '/adm_' in msgText:
                if '/adm_allclouds' in msgText:
                    try:
                        show_loading_progress(bot, message, 1, 3)
                        total_evidences = admin_evidence_manager.refresh_data()
                        show_loading_progress(bot, message, 2, 3)
                        
                        if total_evidences == 0:
                            empty_msg = f"""
👑 TODAS LAS NUBES
━━━━━━━━━━━━━━━━━━━
✅ Todas las nubes están vacías
📭 No hay evidencias para eliminar
━━━━━━━━━━━━━━━━━━━
                            """
                            bot.editMessageText(message, empty_msg)
                            return
                        
                        total_clouds = len(admin_evidence_manager.clouds_dict)
                        total_files = 0
                        
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            for ev in evidences:
                                total_files += ev['files_count']
                        
                        menu_msg = f"👑 GESTIÓN DE TODAS LAS NUBES\n━━━━━━━━━━━━━━━━━━━\n📋 NUBES DISPONIBLES:"
                        
                        cloud_index = 0
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            cloud_files = sum(ev['files_count'] for ev in evidences)
                            short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                            menu_msg += f"\n\n{cloud_index}. {short_name}"
                            menu_msg += f"\n   📁 {len(evidences)} evids, {cloud_files} archs"
                            menu_msg += f"\n   🔍 /adm_cloud_{cloud_index}"
                            if len(evidences) > 0:
                                menu_msg += f"\n   🗑️ /adm_wipe_{cloud_index}"
                            cloud_index += 1
                        
                        show_loading_progress(bot, message, 3, 3)
                        
                        if total_evidences > 0:
                            menu_msg += f"\n\n━━━━━━━━━━━━━━━━━━━\n/adm_nuke - ⚠️ Eliminar TODO\n━━━━━━━━━━━━━━━━━━━"
                        
                        bot.editMessageText(message, menu_msg)
                        
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
                        short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                        
                        if not evidences:
                            empty_msg = f"📭 NUBE VACÍA\n━━━━━━━━━━━━━━━━━━━\n☁️ {short_name}\n📊 No hay evidencias en esta nube."
                            bot.editMessageText(message, empty_msg)
                            return
                        
                        list_msg = f"📋 EVIDENCIAS DE LA NUBE\n☁️ {short_name}\n━━━━━━━━━━━━━━━━━━━\n\n"
                        for idx, evidence in enumerate(evidences):
                            ev_name = evidence['evidence_name']
                            clean_name = ev_name
                            user_tags = []
                            for user in evidence['group_users']:
                                marker = f"{USER_EVIDENCE_MARKER}{user}"
                                if marker in ev_name:
                                    clean_name = ev_name.replace(marker, "").strip()
                                    user_tags.append(f"@{user}")
                            
                            user_str = f" ({', '.join(user_tags[:2])})" if user_tags else ""
                            
                            list_msg += f"{idx}. {clean_name[:35]}"
                            if len(clean_name) > 35: list_msg += "..."
                            list_msg += f"{user_str}\n"
                            list_msg += f"   📁 {evidence['files_count']} archivos\n"
                            list_msg += f"   👁️ /adm_show_{cloud_idx}_{idx}\n"
                            list_msg += f"   🗑️ /adm_delete_{cloud_idx}_{idx}\n\n"
                        
                        send_long_message(bot, message.chat.id, list_msg, original_message=message)
                        
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                elif '/adm_show_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_show_')
                        if params is None: return
                        cloud_idx, evid_idx = params
                        evidence = admin_evidence_manager.get_evidence(cloud_idx, evid_idx)
                        if evidence:
                            ev_name = evidence['evidence_name']
                            cloud_name = evidence['cloud_name']
                            short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                            
                            clean_name = ev_name
                            for user in evidence['group_users']:
                                marker = f"{USER_EVIDENCE_MARKER}{user}"
                                if marker in ev_name:
                                    clean_name = ev_name.replace(marker, "").strip()
                                    break
                            
                            show_msg = f"👁️ DETALLES DE EVIDENCIA\n━━━━━━━━━━━━━━━━━━━\n📝 Nombre: {clean_name}\n📁 Archivos: {evidence['files_count']}\n☁️ Nube: {short_name}\n\n📄 /adm_fetch_{cloud_idx}_{evid_idx} - Descargar TXT\n🗑️ /adm_delete_{cloud_idx}_{evid_idx} - Eliminar\n━━━━━━━━━━━━━━━━━━━"
                            bot.editMessageText(message, show_msg)
                        else:
                            bot.editMessageText(message, '❌ No se encontró la evidencia')
                    except Exception as e:
                        pass
                    return
                
                elif '/adm_fetch_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_fetch_')
                        if params is None: return
                        cloud_idx, evid_idx = params
                        bot.editMessageText(message, '📄 Obteniendo archivo TXT...')
                        files = admin_evidence_manager.get_txt_for_evidence(cloud_idx, evid_idx)
                        
                        if files:
                            evidence = admin_evidence_manager.get_evidence(cloud_idx, evid_idx)
                            ev_name = evidence['evidence_name']
                            clean_name = ev_name
                            for user in evidence['group_users']:
                                marker = f"{USER_EVIDENCE_MARKER}{user}"
                                if marker in ev_name:
                                    clean_name = ev_name.replace(marker, "").strip()
                                    break
                            
                            safe_name = ''.join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).strip()
                            txtname = f"{safe_name}.txt"
                            with open(txtname, 'w') as txt:
                                for i, f in enumerate(files):
                                    txt.write(f['directurl'])
                                    if i < len(files) - 1: txt.write('\n\n')
                            bot.sendFile(update.message.chat.id, txtname)
                            os.unlink(txtname)
                            bot.editMessageText(message, f'✅ TXT enviado: {clean_name[:50]}')
                        else:
                            bot.editMessageText(message, '❌ No hay archivos en esta evidencia')
                    except: pass
                    return
                
                elif '/adm_delete_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_delete_')
                        if params is None: return
                        cloud_idx, evid_idx = params
                        bot.editMessageText(message, '🔍 Verificando datos...')
                        admin_evidence_manager.refresh_data()
                        cloud_names = list(admin_evidence_manager.clouds_dict.keys())
                        
                        if cloud_idx < 0 or cloud_idx >= len(cloud_names): return
                        cloud_name = cloud_names[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict.get(cloud_name, [])
                        if evid_idx < 0 or evid_idx >= len(evidences): return
                        evidence = evidences[evid_idx]
                        
                        success, ev_name, files_count = delete_evidence_from_cloud(evidence['cloud_config'], evidence['evidence_data'])
                        if success:
                            bot.editMessageText(message, f"✅ ELIMINACIÓN EXITOSA\n📁 Archivos eliminados: {files_count}\n🔄 Actualizando...")
                            time.sleep(1)
                            show_updated_cloud(bot, message, cloud_idx)
                        else:
                            bot.editMessageText(message, f'❌ Error al eliminar.')
                    except: pass
                    return
                
                elif '/adm_wipe_' in msgText:
                    try:
                        cloud_idx = extract_one_param_simple(msgText, '/adm_wipe_')
                        if cloud_idx is None: return
                        cloud_name = list(admin_evidence_manager.clouds_dict.keys())[cloud_idx]
                        
                        bot.editMessageText(message, f'💣 Limpiando nube...')
                        cloud_config = None
                        for user_group, config in PRE_CONFIGURATED_USERS.items():
                            if config.get('moodle_host') == cloud_name:
                                cloud_config = config
                                break
                        
                        if cloud_config:
                            success, deleted_count, total_files = delete_all_evidences_from_cloud(cloud_config)
                            if success:
                                bot.editMessageText(message, f"💥 LIMPIEZA COMPLETA EXITOSA\n✅ Evidencias: {deleted_count}\n✅ Archivos: {total_files}")
                                time.sleep(1)
                                show_updated_all_clouds(bot, message)
                    except: pass
                    return
                
                elif '/adm_nuke' in msgText:
                    try:
                        bot.editMessageText(message, '💣💣💣 ELIMINANDO TODO DE TODAS LAS NUBES...')
                        results = []
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            cloud_config = None
                            for user_group, config in PRE_CONFIGURATED_USERS.items():
                                if config.get('moodle_host') == cloud_name:
                                    cloud_config = config
                                    break
                            
                            if cloud_config:
                                success, deleted_count, total_files = delete_all_evidences_from_cloud(cloud_config)
                                short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                                if success: results.append(f"✅ {short_name}: {deleted_count} evidencias, {total_files} archivos")
                                else: results.append(f"❌ {short_name}: Error al eliminar")
                        
                        final_msg = f"💥💥💥 ELIMINACIÓN MASIVA COMPLETADA 💥💥💥\n━━━━━━━━━━━━━━━━━━━\n📋 DETALLE POR NUBE:\n"
                        for result in results: final_msg += f"\n{result}"
                        bot.editMessageText(message, final_msg)
                    except: pass
                    return
                
                elif '/adm_logs' in msgText:
                    try:
                        uploads = memory_stats.get_recent_uploads(300)
                        logs_msg = f"📋 ÚLTIMOS LOGS\n━━━━━━━━━━━━━━━━━━━\n\n"
                        if uploads:
                            for log in uploads:
                                logs_msg += f"┣➣ {log['timestamp']} - @{log['username']}: {log['filename']} ({log['file_size_formatted']})\n"
                        bot.editMessageText(message, logs_msg[:4000])
                    except: pass
                    return
                
                elif '/adm_users' in msgText:
                    try:
                        users = memory_stats.get_all_users()
                        users_msg = f"👥 ESTADÍSTICAS POR USUARIO\n━━━━━━━━━━━━━━━━━━━\n\n"
                        for user, data in sorted(users.items(), key=lambda x: x[1]['uploads'], reverse=True):
                            users_msg += f"👤 @{user}\n   📤 Subidas: {data['uploads']}\n   💾 Espacio usado: {format_file_size(data['total_size'])}\n\n"
                        bot.editMessageText(message, users_msg[:4000])
                    except: pass
                    return
                
                elif '/adm_cleardata' in msgText:
                    result = memory_stats.clear_all_data()
                    bot.editMessageText(message, f"✅ {result}")
                    return
        
        if '/mystats' in msgText:
            user_stats = memory_stats.get_user_stats(username)
            if user_stats:
                bot.editMessageText(message, f"📊 TUS ESTADÍSTICAS\n━━━━━━━━━━━━━━━━━━━\n👤 Usuario: @{username}\n📤 Archivos subidos: {user_stats['uploads']}\n💾 Espacio total usado: {format_file_size(user_stats['total_size'])}\n🔗 Nube: {user_info['moodle_host']}")
            else:
                bot.editMessageText(message, f"📊 TUS ESTADÍSTICAS\n━━━━━━━━━━━━━━━━━━━\nℹ️ Aún no has realizado ninguna acción")
            return
        
        elif '/files' == msgText:
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
            if client.login():
                all_evidences = client.getEvidences()
                visible_list = []
                search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                
                for ev in all_evidences:
                    if ev['name'].endswith(search_pattern):
                        clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                        file_count = len(ev['files']) if 'files' in ev else 0
                        visible_list.append({'name': clean_name, 'file_count': file_count, 'original': ev})
                
                if len(visible_list) > 0:
                    files_msg = f"📁 TUS EVIDENCIAS\n━━━━━━━━━━━━━━━━━━━\n\n"
                    for idx, item in enumerate(visible_list):
                        files_msg += f" {item['name']} [ {item['file_count']} ]\n /txt_{idx} /del_{idx}\n\n"
                    bot.editMessageText(message, files_msg)
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
                if client.login():
                    all_evidences = client.getEvidences()
                    visible_list = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                            visible_list.append({'clean_name': clean_name, 'original': ev})
                    
                    if findex < len(visible_list):
                        evindex = visible_list[findex]['original']
                        sendTxt(visible_list[findex]['clean_name'] + '.txt', evindex['files'], update, bot)
                        bot.editMessageText(message,'📄 TXT Aquí')
                    client.logout()
            except: pass
             
        elif '/del_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'], user_info['moodle_password'], user_info['moodle_host'], user_info['moodle_repo_id'], proxy=proxy)
                if client.login():
                    all_evidences = client.getEvidences()
                    visible_list = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            visible_list.append({'clean_name': ev['name'].replace(search_pattern, ""), 'original': ev})
                    
                    if findex < len(visible_list):
                        evfile = visible_list[findex]['original']
                        file_count = len(evfile['files']) if 'files' in evfile else 0
                        client.deleteEvidence(evfile)
                        memory_stats.log_delete(username, f"{visible_list[findex]['clean_name']} ({file_count})", visible_list[findex]['clean_name'], user_info['moodle_host'])
                        bot.editMessageText(message, f"🗑️ Evidencia eliminada: {visible_list[findex]['clean_name']}")
                    client.logout()
            except: pass
                
        elif '/delall' in msgText:
            try:
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'], user_info['moodle_password'], user_info['moodle_host'], user_info['moodle_repo_id'], proxy=proxy)
                if client.login():
                    all_evidences = client.getEvidences()
                    user_evidences = [ev for ev in all_evidences if ev['name'].endswith(f"{USER_EVIDENCE_MARKER}{username}")]
                    
                    for item in user_evidences:
                        try: client.deleteEvidence(item)
                        except: pass
                    
                    bot.editMessageText(message, f"🗑️ ELIMINACIÓN MASIVA COMPLETADA\n✅ ¡Todas tus evidencias han sido eliminadas!")
                    client.logout()
            except: pass
                
        # === NUEVO: PROCESAMIENTO DE ENLACES CON NOTIFICACIÓN MEJORADA ===
        elif 'http' in msgText:
            url = msgText
            
            # 1. Pre-extraer los datos del archivo rápidamente
            file_size = 0
            file_size_mb = 0
            filename = url.split('/')[-1] or "Desconocido"
            
            try:
                headers = {}
                if user_info['proxy']:
                    proxy_dict = ProxyCloud.parse(user_info['proxy'])
                    if 'http' in proxy_dict: headers.update({'Proxy': proxy_dict['http']})
                
                # Leemos la cabecera (rápido) para sacar el peso y el nombre
                response = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
                file_size = int(response.headers.get('content-length', 0))
                file_size_mb = file_size / (1024 * 1024)
                
                # Intentamos sacar el nombre original del archivo si el server lo provee
                cd = response.headers.get('content-disposition')
                if cd and 'filename=' in cd:
                    filename = cd.split('filename=')[1].strip('"\'')
                else:
                    filename = unquote(filename) # Limpiar caracteres raros del link
            except Exception as e:
                pass 
                
            # 2. Enviar notificación enriquecida al Admin (siempre y cuando no sea el propio admin)
            if username != ADMIN_USERNAME:
                try:
                    tamano_formateado = format_file_size(file_size) if file_size > 0 else "Desconocido"
                    mensaje_admin = (f"🔔 <b>¡Nuevo enlace recibido!</b>\n"
                                     f"👤 Usuario: @{username}\n"
                                     f"📄 Archivo: <code>{filename}</code>\n"
                                     f"⚖️ Peso: {tamano_formateado}\n"
                                     f"🔗 Enlace: {url}")
                    bot.sendMessage(ADMIN_CHAT_ID, mensaje_admin, parse_mode='html')
                except Exception as e:
                    print(f"Error al notificar al admin: {e}")
            
            # 3. Validar archivos gigantes y enviar el mensaje chistoso si aplica
            funny_message_sent = None
            if file_size_mb > 500:
                funny_message = get_random_large_file_message()
                warning_msg = bot.sendMessage(update.message.chat.id, 
                                  f"⚠️ {funny_message}\n\n"
                                  f"❌ Cojoneee, tú piensas q esto es una nube artificial o q? Para q tú quieres subir {file_size_mb:.2f} MB?\n\n"
                                  f"⬆️ Bueno, lo subiré😡")
                funny_message_sent = warning_msg
            
            # 4. Iniciar descarga y subida
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
            
            if funny_message_sent:
                delete_message_after_delay(bot, funny_message_sent.chat.id, funny_message_sent.message_id, 8)
            
        else:
            bot.editMessageText(message,'➲ No se pudo procesar ✗ ')
            
    except Exception as ex:
        print(f"Error general en onmessage: {str(ex)}")

def main():
    bot = ObigramClient(BOT_TOKEN)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    # CORRECCIÓN DE BUG 2: Prevención de ban de API de Telegram por bucle infinito
    while True:
        try:
            main()
        except Exception as e:
            print(f"Caída crítica detectada: {e}")
            print("Reiniciando bot en 5 segundos...")
            time.sleep(5)
