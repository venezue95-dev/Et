import datetime
import urllib.parse
import time
import os

def sizeof_fmt(num, suffix='B'):
    """Formatea los bytes a un estilo limpio (KB, MB, GB) sin la 'i'"""
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            if unit == '':
                return f"{num} {unit}{suffix}"
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Y{suffix}"

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
    msg = '<b>⬇️ Descargando...</b>\n\n'
    msg += f'<b>📄 Archivo:</b> <code>{filename}</code>\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += f'<b>📊 Porcentaje:</b> <b>{porcent(currentBits, totalBits)}%</b>\n\n'
    msg += f'<b>💾 Tamaño total:</b> <b>{sizeof_fmt(totalBits)}</b>\n\n'
    msg += f'<b>📥 Descargado:</b> <b>{sizeof_fmt(currentBits)}</b>\n\n'
    msg += f'<b>⚡ Velocidad:</b> <b>{sizeof_fmt(speed)}/s</b>\n\n'
    msg += f'<b>⏱️ Tiempo:</b> <b>{datetime.timedelta(seconds=int(time_val))}</b>\n\n'

    if tid != '':
        msg += f'/cancel_{tid}'
    return msg

def createUploading(filename, totalBits, currentBits, speed, time_val, originalname='', tid=''):
    msg = '<b>⬆️ Subiendo a la nube...</b>\n\n'
    if originalname != '':
        msg += f'<b>📁 Nombre:</b> <code>{originalname}</code>\n'
        msg += f'<b>📤 Subiendo:</b> <code>{filename}</code>\n'
    else:
        msg += f'<b>📁 Nombre:</b> <code>{filename}</code>\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += f'<b>📊 Porcentaje:</b> <b>{porcent(currentBits, totalBits)}%</b>\n\n'
    msg += f'<b>💾 Tamaño total:</b> <b>{sizeof_fmt(totalBits)}</b>\n\n'
    msg += f'<b>📤 Subido:</b> <b>{sizeof_fmt(currentBits)}</b>\n\n'
    msg += f'<b>⚡ Velocidad:</b> <b>{sizeof_fmt(speed)}/s</b>\n\n'
    msg += f'<b>⏱️ Tiempo:</b> <b>{datetime.timedelta(seconds=int(time_val))}</b>\n\n'

    if tid != '':
        msg += f'/cancel_{tid}'
    return msg

def createCompresing(filename, filesize, splitsize):
    parts = round(int(filesize / splitsize) + 1, 1)
    msg = '<b>🗜️ Comprimiendo...</b>\n\n'
    msg += f'<b>📁 Nombre:</b> <code>{filename}</code>\n\n'
    msg += f'<b>📊 Tamaño total:</b> <b>{sizeof_fmt(filesize)}</b>\n\n'
    msg += f'<b>📦 Tamaño de partes:</b> <b>{sizeof_fmt(splitsize)}</b>\n\n'
    msg += f'<b>🔢 Cantidad de partes:</b> <b>{parts}</b>\n\n'
    return msg

def createFinishUploading(filename, filesize, split_size, current, count, findex):
    msg = '<b>✅ ¡Proceso completado con éxito!</b>\n\n'
    msg += f'<b>📁 Nombre:</b> <code>{filename}</code>\n\n'
    msg += f'<b>📊 Tamaño total:</b> <b>{sizeof_fmt(filesize)}</b>\n\n'
    msg += f'<b>📦 Tamaño de partes:</b> <code>{sizeof_fmt(split_size)}</code>\n\n'
    msg += f'<b>🔢 Partes subidas:</b> <b>{current}/{count}</b>'
    return msg

def createFileMsg(filename, files):
    if len(files) > 0:
        msg = '<b>🔗 Enlaces de descarga:</b>\n'
        for f in files:
            url = urllib.parse.unquote(f['directurl'], encoding='utf-8', errors='replace')
            msg += f"<a href='{url}'><b>➥ {f['name']}</b></a>\n"
        return msg
    return ''

def createFilesMsg(evfiles):
    msg = f'<b>📁 Archivos guardados ({len(evfiles)})</b>\n\n'
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
            msg += f'<b>📄 {fname}</b>\n'
            msg += f'👁️ <code>/txt_{i}</code>  |  🗑️ <code>/del_{i}</code>\n\n'
            i += 1
        except Exception:
            pass
    return msg

def createStat(username, userdata, isadmin):
    msg = '<b>⚙️ Configuración de usuario</b>\n\n'
    msg += f'<b>👤 Nombre:</b> @{username}\n'
    msg += f'<b>👤 Usuario Moodle:</b> <code>{userdata["moodle_user"]}</code>\n'
    msg += f'<b>🔑 Contraseña:</b> <code>{userdata["moodle_password"]}</code>\n'
    msg += f'<b>🌐 Host:</b> <code>{userdata["moodle_host"]}</code>\n'
    if userdata['cloudtype'] == 'moodle':
        msg += f'<b>📁 RepoID:</b> <b>{userdata["moodle_repo_id"]}</b>\n'
    msg += f'<b>☁️ Tipo de nube:</b> <b>{userdata["cloudtype"]}</b>\n'
    msg += f'<b>⬆️ Tipo de subida:</b> <b>{userdata["uploadtype"]}</b>\n'
    if userdata['cloudtype'] == 'cloud':
        msg += f'<b>📂 Directorio:</b> <code>/{userdata["dir"]}</code>\n'
    msg += f'<b>📏 Límite de zips:</b> <b>{sizeof_fmt(userdata["zips"] * 1024 * 1024)}</b>\n\n'
    
    msg_admin = 'No'
    if isadmin:
        msg_admin = 'Sí'
    msg += f'<b>👑 Administrador:</b> <b>{msg_admin}</b>\n'
    
    proxy = 'No'
    if userdata['proxy'] != '':
        proxy = 'Sí'
    tokenize = 'No'
    if userdata['tokenize'] != 0:
        tokenize = 'Sí'
    msg += f'<b>🔗 Proxy:</b> <b>{proxy}</b>\n'
    msg += f'<b>🔐 Tokenización:</b> <b>{tokenize}</b>\n\n'
    return msg
    
