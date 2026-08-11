from pyobigram.utils import sizeof_fmt, nice_time
import datetime
import time
import os
import urllib.parse

def text_progres(index, max):
    try:
        if max < 1:
            max += 1
        porcent = index / max
        porcent *= 100
        porcent = round(porcent)
        make_text = '\n[ '
        index_make = 1
        while(index_make < 21):
            if porcent >= index_make * 5: 
                make_text += '⬢'
            else: 
                make_text += '⬡'
            index_make += 1
        make_text += ' ]'
        return make_text
    except Exception as ex:
        return ''

def porcent(index, max):
    try:
        if max < 1:
            max += 1
        p = (index / max) * 100
        return round(p)
    except:
        return 0

def createDownloading(filename, totalBits, currentBits, speed, time, tid=''):
    msg = '⬇️ Descargando ●●○\n\n'
    msg += '📄 Archivo: ' + str(filename) + '\n'
    msg += text_progres(currentBits, totalBits) + '\n\n'
    msg += '📊 Porcentaje: ' + str(porcent(currentBits, totalBits)) + '%\n\n'
    msg += '💾 Total: ' + sizeof_fmt(totalBits) + '\n\n'
    msg += '📥 Descargado: ' + sizeof_fmt(currentBits) + '\n\n'
    msg += '⚡ Velocidad: ' + sizeof_fmt(speed) + '/s\n\n'
    msg += '⏱️ Tiempo de descarga: ' + str(datetime.timedelta(seconds=int(time))) + 's'
    
    if tid != '':
        msg += '\n/cancel_' + tid
    return msg

def createUploading(filename, totalBits, currentBits, speed, time, originalname='', tid=''):
    display_name = originalname if originalname != '' else filename
    msg = '⬆️ Subiendo a la nube ☁ ●●○\n\n'
    msg += '📁 Nombre: ' + str(display_name) + '\n'
    if originalname != '':
        msg += '📤 Subiendo: ' + str(filename) + '\n'
    msg += text_progres(currentBits, totalBits) + '\n\n'
    msg += '📊 Porcentaje: ' + str(porcent(currentBits, totalBits)) + '%\n\n'
    msg += '💾 Total: ' + sizeof_fmt(totalBits) + '\n\n'
    msg += '📤 Subido: ' + sizeof_fmt(currentBits) + '\n\n'
    msg += '⚡ Velocidad: ' + sizeof_fmt(speed) + '/s\n\n'
    msg += '⏱️ Tiempo de subida: ' + str(datetime.timedelta(seconds=int(time))) + 's'
    
    if tid != '':
        msg += '\n/cancel_' + tid
    return msg

def createCompresing(filename, filesize, splitsize, tid=''):
    msg = '🗜️ Comprimiendo ●●○\n\n'
    msg += '📁 Nombre: ' + str(filename) + '\n'
    msg += '📊 Tamaño total: ' + str(sizeof_fmt(filesize)) + '\n'
    msg += '📦 Tamaño partes: ' + str(sizeof_fmt(splitsize)) + '\n'
    msg += '🔢 Cantidad partes: ' + str(round(int(filesize / splitsize) + 1, 1))
    
    if tid != '':
        msg += '\n/cancel_' + tid
    return msg

def createFinishUploading(filename, filesize, split_size, current, count, findex):
    msg = '🚀 Proceso finalizado ✅\n\n'
    msg += '📁 Nombre: ' + str(filename) + '\n'
    msg += '📊 Tamaño total: ' + str(sizeof_fmt(filesize)) + '\n'
    msg += '📦 Tamaño partes: ' + str(sizeof_fmt(split_size)) + '\n'
    msg += '🔢 Partes subidas: ' + str(current) + '/' + str(count)
    return msg

def createFileMsg(filename, files):
    if len(files) > 0:
        msg = '<b>➥ Enlaces ⋐⋑</b>\n'
        for f in files:
            url = urllib.parse.unquote(f['directurl'], encoding='utf-8', errors='replace')
            msg += "<a href='" + url + "'>➥" + f['name'] + '⋐⋑</a>\n'
        return msg.strip()
    return ''

def createFilesMsg(evfiles):
    msg = '📁 Archivos (' + str(len(evfiles)) + ') 🗂️\n\n'
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
            msg += '/txt_' + str(i) + ' /del_' + str(i) + '\n' + fname + '\n\n'
            i += 1
        except:
            pass
    return msg.strip()

def createStat(username, userdata, isadmin):
    msg = '⚙️ Configuraciones de usuario 👤\n\n'
    msg += '👤 Nombre: @' + str(username) + '\n'
    msg += '👤 Usuario: ' + str(userdata['moodle_user']) + '\n'
    msg += '🔑 Password: ' + str(userdata['moodle_password']) + '\n'
    msg += '🌐 Host: ' + str(userdata['moodle_host']) + '\n'
    if userdata['cloudtype'] == 'moodle':
        msg += '📁 RepoID: ' + str(userdata['moodle_repo_id']) + '\n'
    msg += '☁️ CloudType: ' + str(userdata['cloudtype']) + '\n'
    msg += '⬆️ UpType: ' + str(userdata['uploadtype']) + '\n'
    if userdata['cloudtype'] == 'cloud':
        msg += '📂 Dir: /' + str(userdata['dir']) + '\n'
    msg += '📏 Tamaño de zips : ' + sizeof_fmt(userdata['zips'] * 1024 * 1024) + '\n\n'
    
    msgAdmin = 'Sí' if isadmin else 'No'
    msg += '👑 Admin : ' + msgAdmin + '\n'
    
    proxy = 'SÍ' if userdata['proxy'] != '' else 'NO'
    tokenize = 'SÍ' if userdata['tokenize'] != 0 else 'NO'
    
    msg += '🔗 Proxy : ' + proxy + '\n'
    msg += '🔐 Tokenize : ' + tokenize + '\n'
    return msg
