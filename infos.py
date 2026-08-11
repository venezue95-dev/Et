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
    msg = '<b><b>⬇️ Descargando...</b></b>\n\n'
    msg += f'<b><b>📄 Archivo:</b></b> <code>{filename}</code>\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += f'<b><b>📊 Porcentaje:</b></b> <b><b>{porcent(currentBits, totalBits)}%</b></b>\n\n'
    msg += f'<b><b>💾 Tamaño total:</b></b> <b><b>{sizeof_fmt(totalBits)}</b></b>\n\n'
    msg += f'<b><b>📥 Descargado:</b></b> <b><b>{sizeof_fmt(currentBits)}</b></b>\n\n'
    msg += f'<b><b>⚡ Velocidad:</b></b> <b><b>{sizeof_fmt(speed)}/s</b></b>\n\n'
    msg += f'<b><b>⏱️ Tiempo:</b></b> <b><b>{datetime.timedelta(seconds=int(time_val))}</b></b>\n\n'

    if tid != '':
        msg += f'/cancel_{tid}'
    return msg

def createUploading(filename, totalBits, currentBits, speed, time_val, originalname='', tid=''):
    msg = '<b><b>⬆️ Subiendo a la nube...</b></b>\n\n'
    if originalname != '':
        msg += f'<b><b>📁 Nombre:</b></b> <code>{originalname}</code>\n'
        msg += f'<b><b>📤 Subiendo:</b></b> <code>{filename}</code>\n'
    else:
        msg += f'<b><b>📁 Nombre:</b></b> <code>{filename}</code>\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += f'<b><b>📊 Porcentaje:</b></b> <b><b>{porcent(currentBits, totalBits)}%</b></b>\n\n'
    msg += f'<b><b>💾 Tamaño total:</b></b> <b><b>{sizeof_fmt(totalBits)}</b></b>\n\n'
    msg += f'<b><b>📤 Subido:</b></b> <b><b>{sizeof_fmt(currentBits)}</b></b>\n\n'
    msg += f'<b><b>⚡ Velocidad:</b></b> <b><b>{sizeof_fmt(speed)}/s</b></b>\n\n'
    msg += f'<b><b>⏱️ Tiempo:</b></b> <b><b>{datetime.timedelta(seconds=int(time_val))}</b></b>\n\n'

    if tid != '':
        msg += f'/cancel_{tid}'
    return msg

def createCompresing(filename, filesize, splitsize):
    parts = round(int(filesize / splitsize) + 1, 1)
    msg = '<b><b>🗜️ Comprimiendo...</b></b>\n\n'
    msg += f'<b><b>📁 Nombre:</b></b> <code>{filename}</code>\n\n'
    msg += f'<b><b>📊 Tamaño total:</b></b> <b><b>{sizeof_fmt(filesize)}</b></b>\n\n'
    msg += f'<b><b>📦 Tamaño de partes:</b></b> <b><b>{sizeof_fmt(splitsize)}</b></b>\n\n'
    msg += f'<b><b>🔢 Cantidad de partes:</b></b> <b><b>{parts}</b></b>\n\n'
    return msg

def createFinishUploading(filename, filesize, split_size, current, count, findex):
    msg = '<b><b>✅ ¡Proceso completado con éxito!</b></b>\n\n'
    msg += f'<b><b>📁 Nombre:</b></b> <code>{filename}</code>\n\n'
    msg += f'<b><b>📊 Tamaño total:</b></b> <b><b>{sizeof_fmt(filesize)}</b></b>\n\n'
    msg += f'<b><b>📦 Tamaño de partes:</b></b> <b><b>{sizeof_fmt(split_size)}</b></b>\n\n'
    msg += f'<b><b>🔢 Partes subidas:</b></b> <b><b>{current}/{count}</b></b>'
    return msg

def createFileMsg(filename, files):
    if len(files) > 0:
        msg = '<b><b>🔗 Enlaces de descarga:</b></b>\n'
        for f in files:
            url = urllib.parse.unquote(f['directurl'], encoding='utf-8', errors='replace')
            msg += f"<a href='{url}'><b><b>➥ {f['name']}</b></b></a>\n"
        return msg
    return ''

def createFilesMsg(evfiles):
    msg = f'<b><b>📁 Archivos guardados ({len(evfiles)})</b></b>\n\n'
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
            msg += f'<b><b>📄 {fname}</b></b>\n'
            msg += f'👁️ /txt_{i}  |  🗑️ /del_{i}\n\n'
            i += 1
        except Exception:
            pass
    return msg

def createStat(username, userdata, isadmin):
    from pyobigram.utils import sizeof_fmt
    msg = '<b><b>⚙️ Configuración de usuario</b></b>\n\n'
    msg += f'<b><b>👤 Nombre:</b></b> @{username}\n'
    msg += f'<b><b>👤 Usuario Moodle:</b></b> <code>{userdata["moodle_user"]}</code>\n'
    msg += f'<b><b>🔑 Contraseña:</b></b> <code>{userdata["moodle_password"]}</code>\n'
    msg += f'<b><b>🌐 Host:</b></b> <code>{userdata["moodle_host"]}</code>\n'
    if userdata['cloudtype'] == 'moodle':
        msg += f'<b><b>📁 RepoID:</b></b> <b><b>{userdata["moodle_repo_id"]}</b></b>\n'
    msg += f'<b><b>☁️ Tipo de nube:</b></b> <b><b>{userdata["cloudtype"]}</b></b>\n'
    msg += f'<b><b>⬆️ Tipo de subida:</b></b> <b><b>{userdata["uploadtype"]}</b></b>\n'
    if userdata['cloudtype'] == 'cloud':
        msg += f'<b><b>📂 Directorio:</b></b> <code>/{userdata["dir"]}</code>\n'
    msg += f'<b><b>📏 Límite de zips:</b></b> <b><b>{sizeof_fmt(userdata["zips"] * 1024 * 1024)}</b></b>\n\n'
    
    msg_admin = 'No'
    if isadmin:
        msg_admin = 'Sí'
    msg += f'<b><b>👑 Administrador:</b></b> <b><b>{msg_admin}</b></b>\n'
    
    proxy = 'No'
    if userdata['proxy'] != '':
        proxy = 'Sí'
    tokenize = 'No'
    if userdata['tokenize'] != 0:
        tokenize = 'Sí'
    msg += f'<b><b>🔗 Proxy:</b></b> <b><b>{proxy}</b></b>\n'
    msg += f'<b><b>🔐 Tokenización:</b></b> <b><b>{tokenize}</b></b>\n\n'
    return msg
    
