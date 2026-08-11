from pyobigram.utils import sizeof_fmt, nice_time
import datetime
import urllib.parse
import time
import os

def text_progres(index, max):
    try:
        if max < 1:
            max += 1
        porcent_val = (index / max) * 100
        porcent_val = round(porcent_val)
        make_text = '\n[ '
        index_make = 1
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
    val = (index / max) * 100
    return round(val)

def createDownloading(filename, totalBits, currentBits, speed, time_val, tid=''):
    msg = (
        '⬇️ Descargando ●●○\n\n'
        f'📄 Archivo: {filename}\n'
        f'{text_progres(currentBits, totalBits)}\n'
        f'📊 Porcentaje: {porcent(currentBits, totalBits)}%\n\n'
        f'💾 Total: {sizeof_fmt(totalBits)}\n\n'
        f'📥 Descargado: {sizeof_fmt(currentBits)}\n\n'
        f'⚡ Velocidad: {sizeof_fmt(speed)}/s\n\n'
        f'⏱️ Tiempo de descarga: {datetime.timedelta(seconds=int(time_val))}\n\n'
    )
    if tid != '':
        msg += f'/cancel_{tid}'
    return msg

def createUploading(filename, totalBits, currentBits, speed, time_val, originalname='', tid=''):
    display_name = originalname if originalname != '' else filename
    msg = (
        '⬆️ Subiendo a la nube ☁ ●●○\n\n'
        f'📁 Archivo: {display_name}\n'
        f'{text_progres(currentBits, totalBits)}\n'
        f'📊 Porcentaje: {porcent(currentBits, totalBits)}%\n\n'
        f'💾 Total: {sizeof_fmt(totalBits)}\n\n'
        f'📤 Subido: {sizeof_fmt(currentBits)}\n\n'
        f'⚡ Velocidad: {sizeof_fmt(speed)}/s\n\n'
        f'⏱️ Tiempo de subida: {datetime.timedelta(seconds=int(time_val))}\n\n'
    )
    if tid != '':
        msg += f'/cancel_{tid}'
    return msg

def createCompresing(filename, filesize, splitsize):
    parts = round(int(filesize / splitsize) + 1, 1)
    return (
        '🗜️ Comprimiendo ●●○\n\n'
        f'📁 Nombre: {filename}\n'
        f'📊 Tamaño total: {sizeof_fmt(filesize)}\n'
        f'📦 Tamaño partes: {sizeof_fmt(splitsize)}\n'
        f'🔢 Cantidad partes: {parts}\n\n'
    )

def createFinishUploading(filename, filesize, split_size, current, count, findex):
    return (
        '🚀 Proceso finalizado ✅\n\n'
        f'📁 Nombre: {filename}\n'
        f'📊 Tamaño total: {sizeof_fmt(filesize)}\n'
        f'📦 Tamaño partes: {sizeof_fmt(split_size)}\n'
        f'🔢 Partes subidas: {current}/{count}\n'
    )

def createFileMsg(filename, files):
    if len(files) > 0:
        msg = '<b>➥ Enlaces ⋐⋑</b>\n'
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
            fext = f'.{fextarray[-2]}' if len(fextarray) >= 3 else f'.{fextarray[-1]}'
            fname = f['name'] + fext
            msg += f'/txt_{i} /del_{i}\n{fname}\n\n'
            i += 1
        except Exception:
            pass
    return msg

def createStat(username, userdata, isadmin):
    msg = (
        '⚙️ Configuraciones de usuario 👤\n\n'
        f'👤 Nombre: @{username}\n'
        f'👤 Usuario: {userdata["moodle_user"]}\n'
        f'🔑 Contraseña: {userdata["moodle_password"]}\n'
        f'🌐 Host: {userdata["moodle_host"]}\n'
    )
    if userdata['cloudtype'] == 'moodle':
        msg += f'📁 RepoID: {userdata["moodle_repo_id"]}\n'
    msg += f'☁️ Tipo de nube: {userdata["cloudtype"]}\n'
    msg += f'⬆️ Tipo de subida: {userdata["uploadtype"]}\n'
    if userdata['cloudtype'] == 'cloud':
        msg += f'📂 Directorio: /{userdata["dir"]}\n'
    msg += f'📏 Tamaño de zips: {sizeof_fmt(userdata["zips"] * 1024 * 1024)}\n\n'
    
    admin_str = 'Sí' if isadmin else 'No'
    msg += f'👑 Administrador: {admin_str}\n'
    
    proxy_str = 'Sí' if userdata['proxy'] != '' else 'No'
    tokenize_str = 'Sí' if userdata['tokenize'] != 0 else 'No'
    
    msg += f'🔗 Proxy: {proxy_str}\n'
    msg += f'🔐 Tokenize: {tokenize_str}\n\n'
    return msg
    
