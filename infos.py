from pyobigram.utils import sizeof_fmt, nice_time
import datetime
import urllib.parse
import time
import os

def text_progres(index, max):
    try:
        if max < 1:
            max += 1
        porcent_val = index / max
        porcent_val *= 100
        porcent_val = round(porcent_val)
        make_text = ''
        index_make = 1
        make_text += '\n[ '
        while index_make < 21:
            if porcent_val >= index_make * 5:
                make_text += '⬢'
            else:
                make_text += '⬡'
            index_make += 1
        make_text += ' ]\n'
        return make_text
    except Exception:
        return ''

def porcent(index, max):
    if max < 1:
        max = 1
    porcent_val = index / max
    porcent_val *= 100
    porcent_val = round(porcent_val)
    return porcent_val

def createDownloading(filename, totalBits, currentBits, speed, time_val, tid=''):
    msg = '⬇️ Descargando archivo...\n\n'
    msg += f'📄 Archivo: {filename}\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += f'📊 Porcentaje: {porcent(currentBits, totalBits)}%\n\n'
    msg += f'💾 Total: {sizeof_fmt(totalBits)}\n\n'
    msg += f'📥 Descargado: {sizeof_fmt(currentBits)}\n\n'
    msg += f'⚡ Velocidad: {sizeof_fmt(speed)}/s\n\n'
    msg += f'⏱️ Tiempo de descarga: {datetime.timedelta(seconds=int(time_val))}\n\n'

    if tid != '':
        msg += '/cancel_' + tid
    return msg

def createUploading(filename, totalBits, currentBits, speed, time_val, originalname='', tid=''):
    msg = '⬆️ Subiendo a la nube ☁ ●●○\n\n'
    msg += f'📁 Nombre: {filename}\n'
    if originalname != '':
        msg = str(msg).replace(filename, originalname)
        msg += f'📁 Nombre: {filename}\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += f'📊 Porcentaje: {porcent(currentBits, totalBits)}%\n\n'
    msg += f'💾 Total: {sizeof_fmt(totalBits)}\n\n'
    msg += f'📤 Subido: {sizeof_fmt(currentBits)}\n\n'
    msg += f'⚡ Velocidad: {sizeof_fmt(speed)}/s\n\n'
    msg += f'⏱️ Tiempo de subida: {datetime.timedelta(seconds=int(time_val))}\n\n'

    if tid != '':
        msg += '/cancel_' + tid
    return msg

def createCompresing(filename, filesize, splitsize):
    msg = '🗜️ Comprimiendo archivo...\n\n'
    msg += f'📁 Nombre: {filename}\n\n'
    msg += f'📊 Tamaño total: {sizeof_fmt(filesize)}\n\n'
    msg += f'📦 Tamaño de partes: {sizeof_fmt(splitsize)}\n\n'
    msg += f'🔢 Cantidad de partes: {round(int(filesize / splitsize) + 1, 1)}\n\n'
    return msg

def createFinishUploading(filename, filesize, split_size, current, count, findex):
    msg = '🚀 Proceso finalizado ✅\n\n'
    msg += f'📁 Nombre: {filename}\n\n'
    msg += f'📊 Tamaño total: {sizeof_fmt(filesize)}\n\n'
    msg += f'📦 Tamaño de partes: {sizeof_fmt(split_size)}\n\n'
    msg += f'🔢 Partes subidas: {current}/{count}\n'
    return msg

def createFileMsg(filename, files):
    if len(files) > 0:
        msg = '\n<b>➥ Enlaces ⋐⋑</b>\n'
        for f in files:
            url = urllib.parse.unquote(f['directurl'], encoding='utf-8', errors='replace')
            msg += f"<a href='{url}'>➥{f['name']}⋐⋑</a>\n"
        return msg
    return ''

def createFilesMsg(evfiles):
    msg = f'📁 Archivos ({len(evfiles)}) 🗂️\n\n'
    i = 0
    for f in evfiles:
        try:
            fextarray = str(f['files'][0]['name']).split('.')
            fext = ''
            if len(fextarray) >= 3:
                fext = '.' + fextarray[-2]
            else:
                fext = '.' + fextarray[-1]
            fname = f['name'] + fext
            msg += f'/txt_{i} /del_{i}\n{fname}\n\n'
            i += 1
        except Exception:
            pass
    return msg

def createStat(username, userdata, isadmin):
    from pyobigram.utils import sizeof_fmt
    msg = '⚙️ Configuración de usuario 👤\n\n'
    msg += f'👤 Nombre: @{username}\n'
    msg += f'👤 Usuario: {userdata["moodle_user"]}\n'
    msg += f'🔑 Contraseña: {userdata["moodle_password"]}\n'
    msg += f'🌐 Host: {userdata["moodle_host"]}\n'
    if userdata['cloudtype'] == 'moodle':
        msg += f'📁 RepoID: {userdata["moodle_repo_id"]}\n'
    msg += f'☁️ Tipo de nube: {userdata["cloudtype"]}\n'
    msg += f'⬆️ Tipo de subida: {userdata["uploadtype"]}\n'
    if userdata['cloudtype'] == 'cloud':
        msg += f'📂 Directorio: /{userdata["dir"]}\n'
    msg += f'📏 Tamaño de zips: {sizeof_fmt(userdata["zips"] * 1024 * 1024)}\n\n'
    
    msg_admin = 'No'
    if isadmin:
        msg_admin = 'Sí'
    msg += f'👑 Administrador: {msg_admin}\n'
    
    proxy = 'No'
    if userdata['proxy'] != '':
        proxy = 'Sí'
    tokenize = 'No'
    if userdata['tokenize'] != 0:
        tokenize = 'Sí'
    msg += f'🔗 Proxy: {proxy}\n'
    msg += f'🔐 Tokenización: {tokenize}\n\n'
    return msg
    
