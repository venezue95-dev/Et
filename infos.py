from pyobigram.utils import sizeof_fmt, nice_time
import datetime
import urllib.parse
import time
import os

def text_progres(index, max):
    try:
        if max < 1:
            max += 1
        porcent = index / max
        porcent *= 100
        porcent = round(porcent)
        make_text = ''
        index_make = 1
        make_text += '\n[ '
        while(index_make < 21):
            if porcent >= index_make * 5: make_text += '⬢'
            else: make_text += '⬡'
            index_make += 1
        make_text += ' ]\n'
        return make_text
    except Exception as ex:
            return ''

def porcent(index, max):
    porcent = index / max
    porcent *= 100
    porcent = round(porcent)
    return porcent

def createDownloading(filename, totalBits, currentBits, speed, time, tid=''):
    msg = '⬇️ <b>Descargando archivo...</b>\n\n'
    msg += '📄 <b>Archivo:</b> <code>' + str(filename) + '</code>\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += '📊 <b>Progreso:</b> ' + str(porcent(currentBits, totalBits)) + '%\n'
    msg += '💾 <b>Total:</b> ' + sizeof_fmt(totalBits) + '\n'
    msg += '📥 <b>Descargado:</b> ' + sizeof_fmt(currentBits) + '\n'
    msg += '⚡ <b>Velocidad:</b> ' + sizeof_fmt(speed) + '/s\n'
    msg += '⏱️ <b>Tiempo restante:</b> ' + str(datetime.timedelta(seconds=int(time))) + '\n\n'

    if tid != '':
        msg += '/cancel_' + tid
    return msg

def createUploading(filename, totalBits, currentBits, speed, time, originalname='', tid=''):
    msg = '⬆️ <b>Subiendo a la nube...</b> ☁️\n\n'
    if originalname != '':
        msg += '📁 <b>Nombre:</b> <code>' + str(originalname) + '</code>\n'
    else:
        msg += '📁 <b>Nombre:</b> <code>' + str(filename) + '</code>\n'
    msg += text_progres(currentBits, totalBits) + '\n'
    msg += '📊 <b>Progreso:</b> ' + str(porcent(currentBits, totalBits)) + '%\n'
    msg += '💾 <b>Total:</b> ' + sizeof_fmt(totalBits) + '\n'
    msg += '📤 <b>Subido:</b> ' + sizeof_fmt(currentBits) + '\n'
    msg += '⚡ <b>Velocidad:</b> ' + sizeof_fmt(speed) + '/s\n'
    msg += '⏱️ <b>Tiempo restante:</b> ' + str(datetime.timedelta(seconds=int(time))) + '\n\n'

    if tid != '':
        msg += '/cancel_' + tid
    return msg

def createCompresing(filename, filesize, splitsize):
    msg = '🗜️ <b>Comprimiendo archivo...</b>\n\n'
    msg += '📁 <b>Nombre:</b> <code>' + str(filename) + '</code>\n'
    msg += '📊 <b>Tamaño total:</b> ' + sizeof_fmt(filesize) + '\n'
    msg += '📦 <b>Tamaño de partes:</b> ' + sizeof_fmt(splitsize) + '\n'
    msg += '🔢 <b>Cantidad de partes:</b> ' + str(round(int(filesize/splitsize)+1, 1)) + '\n'
    return msg

def createFinishUploading(filename, filesize, split_size, current, count, findex):
    msg = '✅ <b>¡Proceso finalizado con éxito!</b>\n\n'
    msg += '📁 <b>Nombre:</b> <code>' + str(filename) + '</code>\n'
    msg += '📊 <b>Tamaño total:</b> ' + sizeof_fmt(filesize) + '\n'
    msg += '📦 <b>Tamaño de partes:</b> ' + sizeof_fmt(split_size) + '\n'
    msg += '🔢 <b>Partes subidas:</b> ' + str(current) + '/' + str(count) + '\n'
    return msg

def createFileMsg(filename, files):
    import urllib
    if len(files) > 0:
        msg = '🔗 <b>Enlaces generados:</b>\n'
        for f in files:
            url = urllib.parse.unquote(f['directurl'], encoding='utf-8', errors='replace')
            msg += f"🔽 <a href='{url}'>{f['name']}</a>\n"
        return msg
    return ''

def createFilesMsg(evfiles):
    msg = '📁 <b>Archivos guardados</b> (' + str(len(evfiles)) + ')\n\n'
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
        except: pass
    return msg

def createStat(username, userdata, isadmin):
    from pyobigram.utils import sizeof_fmt
    msg = '⚙️ <b>Configuración de usuario</b>\n\n'
    msg += '👤 <b>Nombre:</b> @' + str(username) + '\n'
    msg += '👤 <b>Usuario:</b> <code>' + str(userdata['moodle_user']) + '</code>\n'
    msg += '🔑 <b>Contraseña:</b> <code>' + str(userdata['moodle_password']) + '</code>\n'
    msg += '🌐 <b>Host:</b> <code>' + str(userdata['moodle_host']) + '</code>\n'
    if userdata['cloudtype'] == 'moodle':
        msg += '📁 <b>RepoID:</b> ' + str(userdata['moodle_repo_id']) + '\n'
    msg += '☁️ <b>Tipo de nube:</b> ' + str(userdata['cloudtype']) + '\n'
    msg += '⬆️ <b>Tipo de subida:</b> ' + str(userdata['uploadtype']) + '\n'
    if userdata['cloudtype'] == 'cloud':
        msg += '📂 <b>Directorio:</b> /' + str(userdata['dir']) + '\n'
    msg += '📏 <b>Límite de zips:</b> ' + sizeof_fmt(userdata['zips']*1024*1024) + '\n\n'
    msg_admin = 'No'
    if isadmin:
        msg_admin = 'Sí'
    msg += '👑 <b>Administrador:</b> ' + msg_admin + '\n'
    proxy = 'No'
    if userdata['proxy'] != '':
       proxy = 'Sí'
    tokenize = 'No'
    if userdata['tokenize'] != 0:
       tokenize = 'Sí'
    msg += '🔗 <b>Proxy:</b> ' + proxy + '\n'
    msg += '🔐 <b>Tokenización:</b> ' + tokenize + '\n'
    return msg
    
