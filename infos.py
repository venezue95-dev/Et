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
    msg = '⬇️ <b>Descargando archivo...</b>\n\n'
    msg += f'📄 <b>Archivo:</b> <code>{filename}</code>\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += f'📊 <b>Progreso:</b> {porcent(currentBits, totalBits)}%\n'
    msg += f'💾 <b>Total:</b> {sizeof_fmt(totalBits)}\n'
    msg += f'📥 <b>Descargado:</b> {sizeof_fmt(currentBits)}\n'
    msg += f'⚡ <b>Velocidad:</b> {sizeof_fmt(speed)}/s\n'
    msg += f'⏱️ <b>Tiempo restante:</b> {datetime.timedelta(seconds=int(time_val))}\n\n'

    if tid != '':
        msg += f'/cancel_{tid}'
    return msg

def createUploading(filename, totalBits, currentBits, speed, time_val, originalname='', tid=''):
    msg = '⬆️ <b>Subiendo a la nube...</b> ☁️\n\n'
    if originalname != '':
        msg += f'📁 <b>Nombre:</b> <code>{originalname}</code>\n'
    else:
        msg += f'📁 <b>Nombre:</b> <code>{filename}</code>\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += f'📊 <b>Progreso:</b> {porcent(currentBits, totalBits)}%\n'
    msg += f'💾 <b>Total:</b> {sizeof_fmt(totalBits)}\n'
    msg += f'📤 <b>Subido:</b> {sizeof_fmt(currentBits)}\n'
    msg += f'⚡ <b>Velocidad:</b> {sizeof_fmt(speed)}/s\n'
    msg += f'⏱️ <b>Tiempo restante:</b> {datetime.timedelta(seconds=int(time_val))}\n\n'

    if tid != '':
        msg += f'/cancel_{tid}'
    return msg

def createCompresing(filename, filesize, splitsize):
    msg = '🗜️ <b>Comprimiendo archivo...</b>\n\n'
    msg += f'📁 <b>Nombre:</b> <code>{filename}</code>\n'
    msg += f'📊 <b>Tamaño total:</b> {sizeof_fmt(filesize)}\n'
    msg += f'📦 <b>Tamaño de partes:</b> {sizeof_fmt(splitsize)}\n'
    msg += f'🔢 <b>Cantidad de partes:</b> {round(int(filesize / splitsize) + 1, 1)}\n'
    return msg

def createFinishUploading(filename, filesize, split_size, current, count, findex):
    msg = '✅ <b>¡Proceso finalizado con éxito!</b>\n\n'
    msg += f'📁 <b>Nombre:</b> <code>{filename}</code>\n'
    msg += f'📊 <b>Tamaño total:</b> {sizeof_fmt(filesize)}\n'
    msg += f'📦 <b>Tamaño de partes:</b> {sizeof_fmt(split_size)}\n'
    msg += f'🔢 <b>Partes subidas:</b> {current}/{count}\n'
    return msg

def createFileMsg(filename, files):
    if len(files) > 0:
        msg = '\n🔗 <b>Enlaces generados:</b>\n'
        for f in files:
            url = urllib.parse.unquote(f['directurl'], encoding='utf-8', errors='replace')
            msg += f"🔽 <a href='{url}'>{f['name']}</a>\n"
        return msg
    return ''

def createFilesMsg(evfiles):
    msg = f'📁 <b>Archivos guardados</b> ({len(evfiles)})\n\n'
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
            msg += f'📄 <code>{fname}</code>\n'
            msg += f'👁️ /txt_{i}  |  🗑️ /del_{i}\n\n'
            i += 1
        except Exception:
            pass
    return msg

def createStat(username, userdata, isadmin):
    from pyobigram.utils import sizeof_fmt
    msg = '⚙️ <b>Configuración de usuario</b>\n\n'
    msg += f'👤 <b>Nombre:</b> @{username}\n'
    msg += f'👤 <b>Usuario:</b> <code>{userdata["moodle_user"]}</code>\n'
    msg += f'🔑 <b>Contraseña:</b> <code>{userdata["moodle_password"]}</code>\n'
    msg += f'🌐 <b>Host:</b> <code>{userdata["moodle_host"]}</code>\n'
    if userdata['cloudtype'] == 'moodle':
        msg += f'📁 <b>RepoID:</b> {userdata["moodle_repo_id"]}\n'
    msg += f'☁️ <b>Tipo de nube:</b> {userdata["cloudtype"]}\n'
    msg += f'⬆️ <b>Tipo de subida:</b> {userdata["uploadtype"]}\n'
    if userdata['cloudtype'] == 'cloud':
        msg += f'📂 <b>Directorio:</b> /{userdata["dir"]}\n'
    msg += f'📏 <b>Límite de zips:</b> {sizeof_fmt(userdata["zips"] * 1024 * 1024)}\n\n'
    
    msg_admin = 'Sí' if isadmin else 'No'
    msg += f'👑 <b>Administrador:</b> {msg_admin}\n'
    
    proxy = 'Sí' if userdata['proxy'] != '' else 'No'
    tokenize = 'Sí' if userdata['tokenize'] != 0 else 'No'
    msg += f'🔗 <b>Proxy:</b> {proxy}\n'
    msg += f'🔐 <b>Tokenización:</b> {tokenize}\n'
    return msg
    
