import requests
import os
import textwrap
import re
import json
import urllib.parse
from bs4 import BeautifulSoup
import requests_toolbelt as rt
from requests_toolbelt import MultipartEncoderMonitor
from requests_toolbelt import MultipartEncoder
from functools import partial
import uuid
import time
from ProxyCloud import ProxyCloud
import socket
import socks
import asyncio
import threading
import S5Crypto


class CallingUpload:
    def __init__(self, func, filename, args):
        self.func = func
        self.args = args
        self.filename = filename
        self.time_start = time.time()
        self.time_total = 0
        self.speed = 0
        self.last_read_byte = 0

    def __call__(self, monitor):
        self.speed += monitor.bytes_read - self.last_read_byte
        self.last_read_byte = monitor.bytes_read
        tcurrent = time.time() - self.time_start
        self.time_total += tcurrent
        self.time_start = time.time()
        if self.time_total >= 1:
            clock_time = (monitor.len - monitor.bytes_read) / (self.speed if self.speed > 0 else 1)
            if self.func:
                self.func(self.filename, monitor.bytes_read, monitor.len, self.speed, clock_time, self.args)
            self.time_total = 0
            self.speed = 0


class MoodleClient(object):
    def __init__(self, user, passw, host='', repo_id=4, proxy: ProxyCloud = None):
        self.username = user
        self.password = passw
        self.session = requests.Session()
        self.path = 'https://moodle.uclv.edu.cu/'
        self.host_tokenize = 'https://tguploader.url/'
        if host != '':
            self.path = host if host.endswith('/') else host + '/'
        self.userdata = None
        self.userid = ''
        self.repo_id = repo_id
        self.sesskey = ''
        self.proxy = None
        if proxy:
            self.proxy = proxy.as_dict_proxy()

    def getsession(self):
        return self.session

    def getUserData(self):
        try:
            tokenUrl = self.path + 'login/token.php?service=moodle_mobile_app&username=' + urllib.parse.quote(self.username) + '&password=' + urllib.parse.quote(self.password)
            resp = self.session.get(tokenUrl, proxies=self.proxy, timeout=10)
            data = json.loads(resp.text)
            data['s5token'] = S5Crypto.tokenize([self.username, self.password])
            return data
        except Exception:
            return None

    def getDirectUrl(self, url):
        tokens = str(url).split('/')
        direct = self.path + 'webservice/pluginfile.php/' + tokens[4] + '/user/private/' + tokens[-1] + '?token=' + (self.userdata.get('token', '') if self.userdata else '')
        return direct

    def getSessKey(self):
        fileurl = self.path + 'my/#'
        resp = self.session.get(fileurl, proxies=self.proxy, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        sesskey_input = soup.find('input', attrs={'name': 'sesskey'})
        if sesskey_input:
            return sesskey_input['value']
        return ''

    def login(self):
        try:
            login_url = self.path + 'login/index.php'
            resp = self.session.get(login_url, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            logintoken = ''
            try:
                logintoken = soup.find('input', attrs={'name': 'logintoken'})['value']
            except: pass
            
            payload = {
                'anchor': '',
                'logintoken': logintoken,
                'username': self.username,
                'password': self.password,
                'rememberusername': 1
            }
            
            resp2 = self.session.post(login_url, data=payload, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp2.text, 'html.parser')
            
            if "loginerrors" in resp2.text or "error" in resp2.url.lower():
                print('No pude iniciar sesión: credenciales incorrectas o error en el formulario')
                return False

            try:
                self.userid = soup.find('div', {'id': 'nav-notification-popover-container'})['data-userid']
            except:
                try:
                    self.userid = soup.find('a', {'title': 'Enviar un mensaje'})['data-userid']
                except:
                    try:
                        user_link = soup.find('a', href=re.compile(r'user/profile\.php\?id=\d+'))
                        if user_link:
                            self.userid = re.search(r'id=(\d+)', user_link['href']).group(1)
                    except: pass

            print('He iniciado sesión con éxito')
            self.userdata = self.getUserData()
            try:
                self.sesskey = self.getSessKey()
            except: pass
            return True
        except Exception as ex:
            print(f"Error en login: {ex}")
            return False

    def createEvidence(self, name, desc=''):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidenceurl, proxies=self.proxy, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
        files = self.extractQuery(soup.find('object')['data'])['itemid']

        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=&userid=' + self.userid + '&return='
        payload = {
            'userid': self.userid,
            'sesskey': sesskey,
            '_qf__tool_lp_form_user_evidence': 1,
            'name': name,
            'description[text]': desc,
            'description[format]': 1,
            'url': '',
            'files': files,
            'submitbutton': 'Guardar+cambios'
        }
        resp = self.session.post(saveevidence, data=payload, proxies=self.proxy, timeout=10)
        evidenceid = str(resp.url).split('?')[1].split('=')[1]

        return {'name': name, 'desc': desc, 'id': evidenceid, 'url': resp.url, 'files': []}

    def createBlog(self, name, itemid, desc="<p dir=\"ltr\" style=\"text-align: left;\">asd<br></p>"):
        post_attach = f'{self.path}blog/edit.php?action=add&userid=' + self.userid
        resp = self.session.get(post_attach, proxies=self.proxy, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser') 
        attachment_filemanager = soup.find('input', {'id': 'id_attachment_filemanager'})['value']
        post_url = f'{self.path}blog/edit.php'
        payload = {
            'action': 'add',
            'entryid': '',
            'modid': 0,
            'courseid': 0,
            'sesskey': self.sesskey,
            '_qf__blog_edit_form': 1,
            'mform_isexpanded_id_general': 1,
            'mform_isexpanded_id_tagshdr': 1,
            'subject': name,
            'summary_editor[text]': desc,
            'summary_editor[format]': 1,
            'summary_editor[itemid]': itemid,
            'attachment_filemanager': attachment_filemanager,
            'publishstate': 'site',
            'tags': '_qf__force_multiselect_submission',
            'submitbutton': 'Guardar+cambios'
        }
        resp = self.session.post(post_url, data=payload, proxies=self.proxy, timeout=10)
        return resp

    def saveEvidence(self, evidence):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?id=' + str(evidence['id']) + '&userid=' + self.userid + '&return=list'
        resp = self.session.get(evidenceurl, proxies=self.proxy, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
        files = evidence['files']
        
        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=' + str(evidence['id']) + '&userid=' + self.userid + '&return=list'
        payload = {
            'userid': self.userid,
            'sesskey': sesskey,
            '_qf__tool_lp_form_user_evidence': 1,
            'name': evidence['name'],
            'description[text]': evidence.get('desc', ''),
            'description[format]': 1,
            'url': '',
            'files': files,
            'submitbutton': 'Guardar+cambios'
        }
        resp = self.session.post(saveevidence, data=payload, proxies=self.proxy, timeout=10)
        return evidence

    def getEvidences(self):
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_list.php?userid=' + self.userid
        resp = self.session.get(evidencesurl, proxies=self.proxy, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        nodes = soup.find_all('tr', {'data-region': 'user-evidence-node'})
        ev_list = []
        for n in nodes:
            nodetd = n.find_all('td')
            evurl = nodetd[0].find('a')['href']
            evname = n.find('a').text.strip()
            evid = evurl.split('?')[1].split('=')[1]
            nodefiles = nodetd[1].find_all('a')
            nfilelist = []
            for f in nodefiles:
                url = str(f['href'])
                directurl = url
                try:
                    if self.userdata and 'token' in self.userdata:
                        directurl = url + '&token=' + self.userdata['token']
                        directurl = str(directurl).replace('pluginfile.php', 'webservice/pluginfile.php')
                except: pass
                nfilelist.append({'name': f.text.strip(), 'url': url, 'directurl': directurl})
            ev_list.append({'name': evname, 'desc': '', 'id': evid, 'url': evurl, 'files': nfilelist})
        return ev_list

    def deleteEvidence(self, evidence):
        try:
            evidencesurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
            resp = self.session.get(evidencesurl, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
            
            deleteUrl = self.path + 'lib/ajax/service.php?sesskey=' + sesskey + '&info=core_competency_delete_user_evidence,tool_lp_data_for_user_evidence_list_page'
            savejson = [
                {"index": 0, "methodname": "core_competency_delete_user_evidence", "args": {"id": evidence['id']}},
                {"index": 1, "methodname": "tool_lp_data_for_user_evidence_list_page", "args": {"userid": self.userid}}
            ]
            headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
            return self.session.post(deleteUrl, json=savejson, headers=headers, proxies=self.proxy, timeout=10)
        except Exception as e:
            print(f"Error al eliminar evidencia: {e}")
            return None

    def upload_file(self, file, evidence=None, itemid=None, progressfunc=None, args=(), tokenize=False):
        try:
            fileurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
            resp = self.session.get(fileurl, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
            
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            client_id = self.getclientid(resp.text)

            itempostid = itemid if itemid else query['itemid']

            of = open(file, 'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title': (None, ''),
                'author': (None, 'ObysoftDev'),
                'license': (None, 'allrightsreserved'),
                'itemid': (None, itempostid),
                'repo_id': (None, str(self.repo_id)),
                'p': (None, ''),
                'page': (None, ''),
                'env': (None, query['env']),
                'sesskey': (None, sesskey),
                'client_id': (None, client_id),
                'maxbytes': (None, query['maxbytes']),
                'areamaxbytes': (None, query['areamaxbytes']),
                'ctx_id': (None, query['ctx_id']),
                'savepath': (None, '/')
            }
            upload_file = {
                'repo_upload_file': (file, of, 'application/octet-stream'),
                **upload_data
            }
            post_file_url = self.path + 'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file, boundary=b)
            progrescall = CallingUpload(progressfunc, file, args)
            monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
            
            resp2 = self.session.post(
                post_file_url,
                data=monitor,
                headers={"Content-Type": "multipart/form-data; boundary=" + b},
                proxies=self.proxy
            )
            of.close()

            if evidence:
                evidence['files'] = itempostid

            data = self.parsejson(resp2.text)
            raw_url = str(data.get('url', '')).replace('\\', '')
            
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    name = raw_url.split('/')[-1]
                    data['url'] = self.path + 'webservice/pluginfile.php/' + query['ctx_id'] + '/core_competency/userevidence/' + str(evidence['id']) + '/' + name + '?token=' + self.userdata['token']
                elif tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(raw_url) + '/' + self.userdata['s5token']
                else:
                    data['url'] = raw_url
            else:
                data['url'] = raw_url

            return itempostid, data
        except Exception as e:
            print(f"Error en upload_file: {e}")
            return None, None

    def upload_file_blog(self, file, blog=None, itemid=None, progressfunc=None, args=(), tokenize=False):
        try:
            fileurl = self.path + 'blog/edit.php?action=add&userid=' + self.userid
            resp = self.session.get(fileurl, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
            
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            client_id = self.getclientid(resp.text)

            itempostid = itemid if itemid else query['itemid']

            of = open(file, 'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title': (None, ''),
                'author': (None, 'ObysoftDev'),
                'license': (None, 'allrightsreserved'),
                'itemid': (None, itempostid),
                'repo_id': (None, str(self.repo_id)),
                'p': (None, ''),
                'page': (None, ''),
                'env': (None, query['env']),
                'sesskey': (None, sesskey),
                'client_id': (None, client_id),
                'maxbytes': (None, query['maxbytes']),
                'areamaxbytes': (None, query['areamaxbytes']),
                'ctx_id': (None, query['ctx_id']),
                'savepath': (None, '/')
            }
            upload_file = {
                'repo_upload_file': (file, of, 'application/octet-stream'),
                **upload_data
            }
            post_file_url = self.path + 'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file, boundary=b)
            progrescall = CallingUpload(progressfunc, file, args)
            monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
            
            resp2 = self.session.post(
                post_file_url,
                data=monitor,
                headers={"Content-Type": "multipart/form-data; boundary=" + b},
                proxies=self.proxy
            )
            of.close()

            data = self.parsejson(resp2.text)
            data['url'] = str(data.get('url', '')).replace('\\', '')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    data['url'] = str(data['url']).replace('pluginfile.php/', 'webservice/pluginfile.php/') + '?token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']
            return itempostid, data
        except Exception as e:
            print(f"Error en upload_file_blog: {e}")
            return None, None

    def upload_file_perfil(self, file, progressfunc=None, args=(), tokenize=False):
        try:
            file_edit = f'{self.path}user/edit.php?id={self.userid}&returnto=profile'
            resp = self.session.get(file_edit, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            client_id = str(soup.find('div', {'class': 'filemanager'})['id']).replace('filemanager-', '')

            upload_file_url = f'{self.path}repository/repository_ajax.php?action=upload'

            of = open(file, 'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title': (None, ''),
                'author': (None, 'ObysoftDev'),
                'license': (None, 'allrightsreserved'),
                'itemid': (None, query['itemid']),
                'repo_id': (None, str(self.repo_id)),
                'p': (None, ''),
                'page': (None, ''),
                'env': (None, query['env']),
                'sesskey': (None, sesskey),
                'client_id': (None, client_id),
                'maxbytes': (None, query['maxbytes']),
                'areamaxbytes': (None, query['areamaxbytes']),
                'ctx_id': (None, query['ctx_id']),
                'savepath': (None, '/')
            }
            upload_file = {
                'repo_upload_file': (file, of, 'application/octet-stream'),
                **upload_data
            }
            encoder = rt.MultipartEncoder(upload_file, boundary=b)
            progrescall = CallingUpload(progressfunc, file, args)
            monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
            
            resp2 = self.session.post(upload_file_url, data=monitor, headers={"Content-Type": "multipart/form-data; boundary=" + b}, proxies=self.proxy)
            of.close()
            
            data = self.parsejson(resp2.text)
            data['url'] = str(data.get('url', '')).replace('\\', '')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    data['url'] = str(data['url']).replace('pluginfile.php/', 'webservice/pluginfile.php/') + '?token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']

            payload = {
                'returnurl': file_edit,
                'sesskey': sesskey,
                '_qf__user_files_form': '.jpg',
                'submitbutton': 'Guardar+cambios'
            }
            self.session.post(file_edit, data=payload, proxies=self.proxy, timeout=10)

            return None, data
        except Exception as e:
            print(f"Error en upload_file_perfil: {e}")
            return None, None

    def upload_file_draft(self, file, progressfunc=None, args=(), tokenize=False):
        try:
            file_edit = f'{self.path}user/files.php'
            resp = self.session.get(file_edit, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
            
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            client_id = str(soup.find('div', {'class': 'filemanager'})['id']).replace('filemanager-', '')

            of = open(file, 'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title': (None, ''),
                'author': (None, 'ObysoftDev'),
                'license': (None, 'allrightsreserved'),
                'itemid': (None, query['itemid']),
                'repo_id': (None, str(self.repo_id)),
                'p': (None, ''),
                'page': (None, ''),
                'env': (None, query['env']),
                'sesskey': (None, sesskey),
                'client_id': (None, client_id),
                'maxbytes': (None, query['maxbytes']),
                'areamaxbytes': (None, query['areamaxbytes']),
                'ctx_id': (None, query['ctx_id']),
                'savepath': (None, '/')
            }
            upload_file = {
                'repo_upload_file': (file, of, 'application/octet-stream'),
                **upload_data
            }
            post_file_url = self.path + 'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file, boundary=b)
            progrescall = CallingUpload(progressfunc, file, args)
            monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
            
            resp2 = self.session.post(
                post_file_url,
                data=monitor,
                headers={"Content-Type": "multipart/form-data; boundary=" + b},
                proxies=self.proxy
            )
            of.close()

            data = self.parsejson(resp2.text)
            raw_url = str(data.get('url', '')).replace('\\', '')
            
            # Reemplazar a webservice y codificar espacios para que Telegram no corte el enlace
            if 'draftfile.php/' in raw_url and 'webservice/draftfile.php/' not in raw_url:
                raw_url = raw_url.replace('draftfile.php/', 'webservice/draftfile.php/')
            elif 'pluginfile.php/' in raw_url and 'webservice/pluginfile.php/' not in raw_url:
                raw_url = raw_url.replace('pluginfile.php/', 'webservice/pluginfile.php/')

            raw_url = raw_url.replace(' ', '%20')

            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    sep = '&' if '?' in raw_url else '?'
                    data['url'] = f"{raw_url}{sep}token={self.userdata['token']}"
                elif tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(raw_url) + '/' + self.userdata['s5token']
                else:
                    data['url'] = raw_url
            else:
                data['url'] = raw_url

            return None, data
        except Exception as e:
            print(f"Error en upload_file_draft: {e}")
            return None, None

    def upload_file_calendar(self, file, progressfunc=None, args=(), tokenize=False):
        try:
            file_edit = f'{self.path}calendar/managesubscriptions.php'
            resp = self.session.get(file_edit, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            client_id = str(soup.find('input', {'name': 'importfilechoose'})['id']).replace('filepicker-button-', '')

            upload_file_url = f'{self.path}repository/repository_ajax.php?action=upload'

            of = open(file, 'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'title': (None, ''),
                'author': (None, 'ObysoftDev'),
                'license': (None, 'allrightsreserved'),
                'itemid': (None, query['itemid']),
                'repo_id': (None, str(self.repo_id)),
                'p': (None, ''),
                'page': (None, ''),
                'env': (None, query['env']),
                'sesskey': (None, sesskey),
                'client_id': (None, client_id),
                'maxbytes': (None, query['maxbytes']),
                'areamaxbytes': (None, query['maxbytes']),
                'ctx_id': (None, query['ctx_id']),
                'savepath': (None, '/')
            }
            upload_file = {
                'repo_upload_file': (file, of, 'application/octet-stream'),
                **upload_data
            }
            encoder = rt.MultipartEncoder(upload_file, boundary=b)
            progrescall = CallingUpload(progressfunc, file, args)
            monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
            
            resp2 = self.session.post(upload_file_url, data=monitor, headers={"Content-Type": "multipart/form-data; boundary=" + b}, proxies=self.proxy)
            of.close()
            
            data = self.parsejson(resp2.text)
            data['url'] = str(data.get('url', '')).replace('\\', '')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    data['url'] = str(data['url']).replace('pluginfile.php/', 'webservice/pluginfile.php/') + '?token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']
            return None, data
        except Exception as e:
            print(f"Error en upload_file_calendar: {e}")
            return None, None
    
    def parsejson(self, raw_json):
        try:
            return json.loads(raw_json)
        except:
            data = {}
            tokens = str(raw_json).replace('{', '').replace('}', '').split(',')
            for t in tokens:
                split = str(t).split(':', 1)
                if len(split) == 2:
                    data[str(split[0]).replace('"', '').strip()] = str(split[1]).replace('"', '').strip()
            return data

    def getclientid(self, html):
        try:
            index = str(html).index('client_id')
            max_len = 25
            ret = html[index:(index + max_len)]
            return str(ret).replace('client_id":"', '').split('"')[0]
        except:
            return ""

    def extractQuery(self, url):
        retQuery = {}
        try:
            tokens = str(url).split('?')[1].split('&')
            for q in tokens:
                qspl = q.split('=')
                retQuery[qspl[0]] = qspl[1] if len(qspl) > 1 else None
        except: pass
        return retQuery

    def getFiles(self):
        try:
            urlfiles = self.path + 'user/files.php'
            resp = self.session.get(urlfiles, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
            client_id = self.getclientid(resp.text)
            filepath = '/'
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            
            payload = {'sesskey': sesskey, 'client_id': client_id, 'filepath': filepath, 'itemid': query['itemid']}
            postfiles = self.path + 'repository/draftfiles_ajax.php?action=list'
            resp = self.session.post(postfiles, data=payload, proxies=self.proxy, timeout=10)
            jsondec = json.loads(resp.text)
            return jsondec.get('list', [])
        except Exception as e:
            print(f"Error en getFiles: {e}")
            return []

    def delteFile(self, name):
        try:
            urlfiles = self.path + 'user/files.php'
            resp = self.session.get(urlfiles, proxies=self.proxy, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            _qf__core_user_form_private_files = soup.find('input', {'name': '_qf__core_user_form_private_files'})['value']
            sesskey = self.sesskey or soup.find('input', attrs={'name': 'sesskey'})['value']
            client_id = self.getclientid(resp.text)
            filepath = '/'
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            
            payload = {'sesskey': sesskey, 'client_id': client_id, 'filepath': filepath, 'itemid': query['itemid'], 'filename': name}
            postdelete = self.path + 'repository/draftfiles_ajax.php?action=delete'
            self.session.post(postdelete, data=payload, proxies=self.proxy, timeout=10)

            # Guardar cambios
            saveUrl = self.path + 'lib/ajax/service.php?sesskey=' + sesskey + '&info=core_form_dynamic_form'
            savejson = [{
                "index": 0,
                "methodname": "core_form_dynamic_form",
                "args": {
                    "formdata": f"sesskey={sesskey}&_qf__core_user_form_private_files={_qf__core_user_form_private_files}&files_filemanager={query['itemid']}",
                    "form": "core_user\\form\\private_files"
                }
            }]
            headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
            return self.session.post(saveUrl, json=savejson, headers=headers, proxies=self.proxy, timeout=10)
        except Exception as e:
            print(f"Error en delteFile: {e}")
            return None

    # Alias para compatibilidad
    deleteFile = delteFile

    def logout(self):
        try:
            logouturl = self.path + 'login/logout.php?sesskey=' + self.sesskey
            self.session.post(logouturl, proxies=self.proxy, timeout=5)
        except: pass
