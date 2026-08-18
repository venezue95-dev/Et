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
import traceback


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
            clock_time = (monitor.len - monitor.bytes_read) / (self.speed) if self.speed > 0 else 0
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

    def parsejson(self, json_text):
        try:
            return json.loads(json_text)
        except Exception:
            try:
                cleaned = re.sub(r'^[^{\[]*', '', json_text)
                cleaned = re.sub(r'[^}\]]*$', '', cleaned)
                return json.loads(cleaned)
            except Exception:
                return {}

    def getUserData(self):
        """Obtiene el token de WebService usando peticiones POST limpias sin arrastrar cookies de sesión"""
        try:
            tokenUrl = f"{self.path}login/token.php"
            payload = {
                'username': self.username,
                'password': self.password,
                'service': 'moodle_mobile_app'
            }
            # Se usa requests directo (sin self.session) para evitar redirecciones al dashboard web
            resp = requests.post(tokenUrl, data=payload, proxies=self.proxy, timeout=15)
            data = self.parsejson(resp.text)

            # Fallback por GET si la Moodle no soporta POST en token.php
            if not data or 'token' not in data:
                tokenUrlGet = f"{self.path}login/token.php?service=moodle_mobile_app&username={urllib.parse.quote(self.username)}&password={urllib.parse.quote(self.password)}"
                resp = requests.get(tokenUrlGet, proxies=self.proxy, timeout=15)
                data = self.parsejson(resp.text)

            if data and isinstance(data, dict) and 'token' in data:
                data['s5token'] = S5Crypto.tokenize([self.username, self.password])
                return data
            return None
        except Exception as e:
            print(f"[Error getUserData]: {e}")
            return None

    def getDirectUrl(self, url):
        tokens = str(url).split('/')
        token = self.userdata.get('token', '') if self.userdata else ''
        direct = self.path + 'webservice/pluginfile.php/' + tokens[4] + '/user/private/' + tokens[-1] + '?token=' + token
        return direct

    def getSessKey(self):
        try:
            fileurl = self.path + 'my/#'
            resp = self.session.get(fileurl, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey_input = soup.find('input', attrs={'name': 'sesskey'})
            if sesskey_input and sesskey_input.get('value'):
                return sesskey_input['value']
            m = re.search(r'["\']sesskey["\']\s*:\s*["\']([^"\']+)["\']', resp.text)
            if m:
                return m.group(1)
        except Exception:
            pass
        return self.sesskey

    def login(self):
        try:
            login = self.path + 'login/index.php'
            resp = self.session.get(login, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            logintoken = ''
            try:
                lt_el = soup.find('input', attrs={'name': 'logintoken'})
                if lt_el and lt_el.get('value'):
                    logintoken = lt_el['value']
            except Exception:
                pass

            payload = {
                'anchor': '',
                'logintoken': logintoken,
                'username': self.username,
                'password': self.password,
                'rememberusername': 1
            }
            loginurl = self.path + 'login/index.php'
            resp2 = self.session.post(loginurl, data=payload, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp2.text, 'html.parser')
            
            counter = 0
            for i in resp2.text.splitlines():
                if "loginerrors" in i or (0 < counter <= 3):
                    counter += 1
            if counter > 0:
                return False
            else:
                try:
                    self.userid = soup.find('div', {'id': 'nav-notification-popover-container'})['data-userid']
                except Exception:
                    try:
                        self.userid = soup.find('a', {'title': 'Enviar un mensaje'})['data-userid']
                    except Exception:
                        m_uid = re.search(r'["\']userId["\']\s*:\s*["\']?(\d+)["\']?', resp2.text)
                        if m_uid:
                            self.userid = m_uid.group(1)

                self.userdata = self.getUserData()
                try:
                    self.sesskey = self.getSessKey()
                except Exception:
                    pass
                return True
        except Exception:
            return False

    def getclientid(self, html):
        m = re.search(r'client_id["\']?\s*:\s*["\']([^"\']+)["\']', html)
        if m:
            return m.group(1)
        m2 = re.search(r'filemanager-([a-zA-Z0-9]+)', html)
        if m2:
            return m2.group(1)
        return uuid.uuid4().hex[:10]

    def extractQuery(self, url):
        retQuery = {}
        if not url or '?' not in url:
            return retQuery
        tokens = str(url).split('?')[1].split('&')
        for q in tokens:
            qspl = q.split('=')
            try:
                retQuery[qspl[0]] = qspl[1]
            except Exception:
                retQuery[qspl[0]] = None
        return retQuery

    def extract_filemanager_params(self, html, soup):
        params = {
            'itemid': '',
            'ctx_id': '1',
            'env': 'filemanager',
            'maxbytes': '0',
            'areamaxbytes': '-1',
            'client_id': self.getclientid(html)
        }

        # 1. <object>
        obj = soup.find('object', attrs={'type': 'text/html'})
        if obj and obj.get('data') and '?' in obj['data']:
            query = self.extractQuery(obj['data'])
            params.update({k: v for k, v in query.items() if v is not None})
            return params

        # 2. Inputs
        itemid_input = soup.find('input', {'name': re.compile(r'itemid|draftitemid|_filemanager')})
        if itemid_input and itemid_input.get('value'):
            params['itemid'] = itemid_input['value']

        # 3. Scripts JS
        itemid_match = re.search(r'["\']itemid["\']\s*:\s*["\']?(\d+)["\']?', html)
        if itemid_match and not params['itemid']:
            params['itemid'] = itemid_match.group(1)

        ctx_match = re.search(r'["\']ctx_id["\']\s*:\s*["\']?(\d+)["\']?', html)
        if ctx_match:
            params['ctx_id'] = ctx_match.group(1)

        maxbytes_match = re.search(r'["\']maxbytes["\']\s*:\s*["\']?(-?\d+)["\']?', html)
        if maxbytes_match:
            params['maxbytes'] = maxbytes_match.group(1)

        areamax_match = re.search(r'["\']areamaxbytes["\']\s*:\s*["\']?(-?\d+)["\']?', html)
        if areamax_match:
            params['areamaxbytes'] = areamax_match.group(1)

        return params

    def createEvidence(self, name, desc=''):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidenceurl, proxies=self.proxy, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')

        sesskey = self.sesskey or (soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else '')
        params = self.extract_filemanager_params(resp.text, soup)
        files = params.get('itemid', '')

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
        resp = self.session.post(saveevidence, data=payload, proxies=self.proxy, timeout=15)
        evidenceid = str(resp.url).split('?')[1].split('=')[1] if '?' in resp.url and '=' in resp.url else ''
        return {'name': name, 'desc': desc, 'id': evidenceid, 'url': resp.url, 'files': []}

    def createBlog(self, name, itemid, desc="<p dir=\"ltr\" style=\"text-align: left;\">Archivo adjunto</p>"):
        try:
            post_attach = f'{self.path}blog/edit.php?action=add&userid=' + self.userid
            resp = self.session.get(post_attach, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            attach_el = soup.find('input', {'id': 'id_attachment_filemanager'})
            attachment_filemanager = attach_el['value'] if attach_el else ''
            
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
            resp2 = self.session.post(post_url, data=payload, proxies=self.proxy, timeout=15)
            
            entryid = None
            if 'entryid=' in resp2.url:
                entryid = resp2.url.split('entryid=')[1].split('&')[0]
            else:
                soup2 = BeautifulSoup(resp2.text, 'html.parser')
                del_link = soup2.find('a', href=re.compile(r'blog/edit\.php\?action=delete&entryid=(\d+)'))
                if del_link:
                    entryid = re.search(r'entryid=(\d+)', del_link['href']).group(1)
            
            return entryid
        except Exception:
            return None

    def getBlogs(self):
        try:
            blog_url = f'{self.path}blog/index.php?userid={self.userid}'
            resp = self.session.get(blog_url, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            entries = []
            
            del_links = soup.find_all('a', href=re.compile(r'blog/edit\.php\?action=delete&entryid=(\d+)'))
            for a in del_links:
                m = re.search(r'entryid=(\d+)', a['href'])
                if not m:
                    continue
                eid = m.group(1)
                
                container = a.find_parent('div', class_=re.compile(r'blog_entry|forumpost|post|card|box|entry'))
                if not container:
                    container = a.find_parent('div')
                
                title = ""
                if container:
                    for tag in container.find_all(['h3', 'h4', 'h2', 'div', 'a']):
                        txt = tag.get_text().strip()
                        if txt and not any(k in txt.lower() for k in ['editar', 'borrar', 'enlace permanente', 'comentarios', 'de ']):
                            title = txt
                            break
                
                if not title:
                    title = f"Entrada de Blog #{eid}"
                
                entries.append({'id': eid, 'name': title})
            return entries
        except Exception as e:
            print(f"Error getBlogs: {e}")
            return []

    def deleteBlog(self, entryid):
        try:
            delete_url = f'{self.path}blog/edit.php?action=delete&entryid={entryid}'
            resp = self.session.get(delete_url, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            sesskey = self.sesskey
            sesskey_input = soup.find('input', attrs={'name': 'sesskey'})
            if sesskey_input and sesskey_input.get('value'):
                sesskey = sesskey_input['value']
                self.sesskey = sesskey
            
            post_url = f'{self.path}blog/edit.php'
            payload = {
                'action': 'delete',
                'entryid': str(entryid),
                'sesskey': sesskey,
                'confirm': '1',
                'submitbutton': 'Continuar'
            }
            
            form = soup.find('form', action=re.compile(r'blog/edit\.php|edit\.php'))
            if form:
                for inp in form.find_all('input'):
                    name = inp.get('name')
                    val = inp.get('value', '')
                    if name:
                        payload[name] = val
                payload['confirm'] = '1'
            
            self.session.post(post_url, data=payload, proxies=self.proxy, timeout=15)
            return True
        except Exception as e:
            print(f"Error deleteBlog: {e}")
            return False

    def saveEvidence(self, evidence):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?id=' + evidence['id'] + '&userid=' + self.userid + '&return=list'
        resp = self.session.get(evidenceurl, proxies=self.proxy, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        sesskey = soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else self.sesskey
        files = evidence['files']
        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=' + evidence['id'] + '&userid=' + self.userid + '&return=list'
        payload = {
            'userid': self.userid,
            'sesskey': sesskey,
            '_qf__tool_lp_form_user_evidence': 1,
            'name': evidence['name'],
            'description[text]': evidence['desc'],
            'description[format]': 1,
            'url': '',
            'files': files,
            'submitbutton': 'Guardar+cambios'
        }
        self.session.post(saveevidence, data=payload, proxies=self.proxy, timeout=15)
        return evidence

    def getEvidences(self):
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_list.php?userid=' + self.userid 
        resp = self.session.get(evidencesurl, proxies=self.proxy, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        nodes = soup.find_all('tr', {'data-region': 'user-evidence-node'})
        list_ev = []
        for n in nodes:
            nodetd = n.find_all('td')
            if not nodetd:
                continue
            a_tag = nodetd[0].find('a')
            if not a_tag:
                continue
            evurl = a_tag['href']
            evname = a_tag.text.strip()
            evid = evurl.split('?')[1].split('=')[1] if '?' in evurl and '=' in evurl else ''
            nodefiles = nodetd[1].find_all('a')
            nfilelist = []
            for f in nodefiles:
                url = str(f['href'])
                directurl = url
                try:
                    if self.userdata and 'token' in self.userdata:
                        directurl = url + ('&' if '?' in url else '?') + 'token=' + self.userdata['token']
                        directurl = str(directurl).replace('pluginfile.php', 'webservice/pluginfile.php')
                except Exception:
                    pass
                nfilelist.append({'name': f.text.strip(), 'url': url, 'directurl': directurl})
            list_ev.append({'name': evname, 'desc': '', 'id': evid, 'url': evurl, 'files': nfilelist})
        return list_ev

    def deleteEvidence(self, evidence):
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidencesurl, proxies=self.proxy, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        sesskey = soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else self.sesskey
        deleteUrl = self.path + 'lib/ajax/service.php?sesskey=' + sesskey + '&info=core_competency_delete_user_evidence,tool_lp_data_for_user_evidence_list_page'
        savejson = [
            {"index": 0, "methodname": "core_competency_delete_user_evidence", "args": {"id": evidence['id']}},
            {"index": 1, "methodname": "tool_lp_data_for_user_evidence_list_page", "args": {"userid": self.userid}}
        ]
        headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
        resp = self.session.post(deleteUrl, json=savejson, headers=headers, proxies=self.proxy, timeout=15)
        return resp

    def upload_file(self, file, evidence=None, itemid=None, progressfunc=None, args=(), tokenize=False):
        try:
            fileurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
            resp = self.session.get(fileurl, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or (soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else '')
            params = self.extract_filemanager_params(resp.text, soup)
        
            itempostid = itemid if itemid else params['itemid']
            filename_only = os.path.basename(file)

            with open(file, 'rb') as of:
                b = uuid.uuid4().hex
                upload_data = {
                    'title': (None, filename_only),
                    'author': (None, 'ObysoftDev'),
                    'license': (None, 'allrightsreserved'),
                    'itemid': (None, str(itempostid)),
                    'repo_id': (None, str(self.repo_id)),
                    'p': (None, ''),
                    'page': (None, ''),
                    'env': (None, str(params['env'])),
                    'sesskey': (None, str(sesskey)),
                    'client_id': (None, str(params['client_id'])),
                    'maxbytes': (None, str(params['maxbytes'])),
                    'areamaxbytes': (None, str(params['areamaxbytes'])),
                    'ctx_id': (None, str(params['ctx_id'])),
                    'savepath': (None, '/')
                }
                upload_file = {'repo_upload_file': (filename_only, of, 'application/octet-stream'), **upload_data}
                post_file_url = self.path + 'repository/repository_ajax.php?action=upload'
                encoder = rt.MultipartEncoder(upload_file, boundary=b)
                progrescall = CallingUpload(progressfunc, file, args)
                monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
                resp2 = self.session.post(post_file_url, data=monitor, headers={"Content-Type": "multipart/form-data; boundary=" + b}, proxies=self.proxy)

            if evidence:
                evidence['files'] = itempostid

            data = self.parsejson(resp2.text)
            if 'url' in data:
                data['url'] = str(data['url']).replace('\\', '')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    name = str(data.get('url', filename_only)).split('/')[-1]
                    data['url'] = self.path + 'webservice/pluginfile.php/' + str(params['ctx_id']) + '/core_competency/userevidence/' + str(evidence.get('id', '')) + '/' + name + '?token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data.get('url', '')) + '/' + self.userdata.get('s5token', '')
            return itempostid, data
        except Exception as e:
            print(f"Error upload_file (Evidence): {e}")
            return None, None

    def upload_file_blog(self, file, blog=None, itemid=None, progressfunc=None, args=(), tokenize=False):
        try:
            fileurl = self.path + 'blog/edit.php?action=add&userid=' + self.userid
            resp = self.session.get(fileurl, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or (soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else '')
            params = self.extract_filemanager_params(resp.text, soup)
        
            itempostid = itemid if itemid else params['itemid']
            filename_only = os.path.basename(file)

            with open(file, 'rb') as of:
                b = uuid.uuid4().hex
                upload_data = {
                    'title': (None, filename_only),
                    'author': (None, 'ObysoftDev'),
                    'license': (None, 'allrightsreserved'),
                    'itemid': (None, str(itempostid)),
                    'repo_id': (None, str(self.repo_id)),
                    'p': (None, ''),
                    'page': (None, ''),
                    'env': (None, str(params['env'])),
                    'sesskey': (None, str(sesskey)),
                    'client_id': (None, str(params['client_id'])),
                    'maxbytes': (None, str(params['maxbytes'])),
                    'areamaxbytes': (None, str(params['areamaxbytes'])),
                    'ctx_id': (None, str(params['ctx_id'])),
                    'savepath': (None, '/')
                }
                upload_file = {'repo_upload_file': (filename_only, of, 'application/octet-stream'), **upload_data}
                post_file_url = self.path + 'repository/repository_ajax.php?action=upload'
                encoder = rt.MultipartEncoder(upload_file, boundary=b)
                progrescall = CallingUpload(progressfunc, file, args)
                monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
                self.session.post(post_file_url, data=monitor, headers={"Content-Type": "multipart/form-data; boundary=" + b}, proxies=self.proxy)

            return itempostid, {
                'filename': filename_only,
                'ctx_id': params['ctx_id'],
                'itemid': itempostid
            }
        except Exception as e:
            print(f"Error upload_file_blog: {e}")
            return None, None

    def upload_file_draft(self, file, progressfunc=None, args=(), tokenize=False):
        try:
            # Asegurar token activo
            if not self.userdata or 'token' not in self.userdata:
                self.userdata = self.getUserData()

            file_edit = f'{self.path}user/files.php'
            resp = self.session.get(file_edit, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            sesskey_input = soup.find('input', attrs={'name': 'sesskey'})
            sesskey = sesskey_input['value'] if sesskey_input else self.sesskey
            if not sesskey:
                sesskey = self.getSessKey()

            params = self.extract_filemanager_params(resp.text, soup)
            filename_only = os.path.basename(file)

            upload_file_url = f'{self.path}repository/repository_ajax.php?action=upload'

            with open(file, 'rb') as of:
                b = uuid.uuid4().hex
                upload_data = {
                    'title': (None, filename_only),
                    'author': (None, 'ObysoftDev'),
                    'license': (None, 'allrightsreserved'),
                    'itemid': (None, str(params['itemid'])),
                    'repo_id': (None, str(self.repo_id)),
                    'p': (None, ''),
                    'page': (None, ''),
                    'env': (None, str(params['env'])),
                    'sesskey': (None, str(sesskey)),
                    'client_id': (None, str(params['client_id'])),
                    'maxbytes': (None, str(params['maxbytes'])),
                    'areamaxbytes': (None, str(params['areamaxbytes'])),
                    'ctx_id': (None, str(params['ctx_id'])),
                    'savepath': (None, '/')
                }
                upload_file = {'repo_upload_file': (filename_only, of, 'application/octet-stream'), **upload_data}
                encoder = rt.MultipartEncoder(upload_file, boundary=b)
                progrescall = CallingUpload(progressfunc, file, args)
                monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
                
                headers = {
                    "Content-Type": "multipart/form-data; boundary=" + b,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "X-Requested-With": "XMLHttpRequest"
                }
                
                resp2 = self.session.post(upload_file_url, data=monitor, headers=headers, proxies=self.proxy)
            
            data = self.parsejson(resp2.text)
            
            if 'error' in data:
                print(f"[Error Moodle Draft]: {data.get('error')}")
                return None, None

            # Construir URL directa
            if 'url' in data and data['url']:
                url_str = str(data['url']).replace('\\', '')
            else:
                ctx = params.get('ctx_id') or '5'
                itemid = params.get('itemid') or ''
                url_str = f"{self.path}draftfile.php/{ctx}/user/draft/{itemid}/{urllib.parse.quote(filename_only)}"

            # Aplicar /webservice/ y concatenar token
            if self.userdata and 'token' in self.userdata and not tokenize:
                if '/draftfile.php/' in url_str:
                    url_str = url_str.replace('/draftfile.php/', '/webservice/draftfile.php/')
                elif '/pluginfile.php/' in url_str:
                    url_str = url_str.replace('/pluginfile.php/', '/webservice/pluginfile.php/')
                
                sep = '&' if '?' in url_str else '?'
                url_str = f"{url_str}{sep}token={self.userdata['token']}"
            elif tokenize and self.userdata:
                url_str = self.host_tokenize + S5Crypto.encrypt(url_str) + '/' + self.userdata.get('s5token', '')

            data['url'] = url_str
            data['filename'] = filename_only
            return params['itemid'], data

        except Exception as e:
            print(f"[Excepción upload_file_draft]: {e}")
            traceback.print_exc()
            return None, None

    def upload_file_perfil(self, file, progressfunc=None, args=(), tokenize=False):
        try:
            file_edit = f'{self.path}user/edit.php?id={self.userid}&returnto=profile'
            resp = self.session.get(file_edit, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or (soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else '')
            params = self.extract_filemanager_params(resp.text, soup)
            filename_only = os.path.basename(file)

            upload_file_url = f'{self.path}repository/repository_ajax.php?action=upload'

            with open(file, 'rb') as of:
                b = uuid.uuid4().hex
                upload_data = {
                    'title': (None, filename_only),
                    'author': (None, 'ObysoftDev'),
                    'license': (None, 'allrightsreserved'),
                    'itemid': (None, str(params['itemid'])),
                    'repo_id': (None, str(self.repo_id)),
                    'p': (None, ''),
                    'page': (None, ''),
                    'env': (None, str(params['env'])),
                    'sesskey': (None, str(sesskey)),
                    'client_id': (None, str(params['client_id'])),
                    'maxbytes': (None, str(params['maxbytes'])),
                    'areamaxbytes': (None, str(params['areamaxbytes'])),
                    'ctx_id': (None, str(params['ctx_id'])),
                    'savepath': (None, '/')
                }
                upload_file = {'repo_upload_file': (filename_only, of, 'application/octet-stream'), **upload_data}
                encoder = rt.MultipartEncoder(upload_file, boundary=b)
                progrescall = CallingUpload(progressfunc, file, args)
                monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
                resp2 = self.session.post(upload_file_url, data=monitor, headers={"Content-Type": "multipart/form-data; boundary=" + b}, proxies=self.proxy)
            
            data = self.parsejson(resp2.text)
            if 'url' in data:
                data['url'] = str(data['url']).replace('\\', '')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    clean_url = str(data.get('url', '')).replace('/pluginfile.php/', '/webservice/pluginfile.php/')
                    sep = '&' if '?' in clean_url else '?'
                    data['url'] = clean_url + sep + 'token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data.get('url', '')) + '/' + self.userdata.get('s5token', '')

            return None, data
        except Exception:
            return None, None

    def upload_file_calendar(self, file, progressfunc=None, args=(), tokenize=False):
        try:
            file_edit = f'{self.path}calendar/managesubscriptions.php'
            resp = self.session.get(file_edit, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or (soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else '')
            params = self.extract_filemanager_params(resp.text, soup)
            filename_only = os.path.basename(file)

            upload_file_url = f'{self.path}repository/repository_ajax.php?action=upload'

            with open(file, 'rb') as of:
                b = uuid.uuid4().hex
                upload_data = {
                    'title': (None, filename_only),
                    'author': (None, 'ObysoftDev'),
                    'license': (None, 'allrightsreserved'),
                    'itemid': (None, str(params['itemid'])),
                    'repo_id': (None, str(self.repo_id)),
                    'p': (None, ''),
                    'page': (None, ''),
                    'env': (None, str(params['env'])),
                    'sesskey': (None, str(sesskey)),
                    'client_id': (None, str(params['client_id'])),
                    'maxbytes': (None, str(params['maxbytes'])),
                    'areamaxbytes': (None, str(params['maxbytes'])),
                    'ctx_id': (None, str(params['ctx_id'])),
                    'savepath': (None, '/')
                }
                upload_file = {'repo_upload_file': (filename_only, of, 'application/octet-stream'), **upload_data}
                encoder = rt.MultipartEncoder(upload_file, boundary=b)
                progrescall = CallingUpload(progressfunc, file, args)
                monitor = MultipartEncoderMonitor(encoder, callback=partial(progrescall))
                resp2 = self.session.post(upload_file_url, data=monitor, headers={"Content-Type": "multipart/form-data; boundary=" + b}, proxies=self.proxy)
            
            data = self.parsejson(resp2.text)
            if 'url' in data:
                data['url'] = str(data['url']).replace('\\', '')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    clean_url = str(data.get('url', '')).replace('/pluginfile.php/', '/webservice/pluginfile.php/')
                    sep = '&' if '?' in clean_url else '?'
                    data['url'] = clean_url + sep + 'token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data.get('url', '')) + '/' + self.userdata.get('s5token', '')
            return None, data
        except Exception:
            return None, None

    def getFiles(self):
        try:
            urlfiles = self.path + 'user/files.php'
            resp = self.session.get(urlfiles, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey or (soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else '')
            params = self.extract_filemanager_params(resp.text, soup)
            filepath = '/'
            payload = {'sesskey': sesskey, 'client_id': params['client_id'], 'filepath': filepath, 'itemid': params['itemid']}
            postfiles = self.path + 'repository/draftfiles_ajax.php?action=list'
            resp = self.session.post(postfiles, data=payload, proxies=self.proxy, timeout=15)
            data = self.parsejson(resp.text)
            return data.get('list', [])
        except Exception as e:
            print(f"Error getFiles: {e}")
            return []
   
    def delteFile(self, name):
        try:
            urlfiles = self.path + 'user/files.php'
            resp = self.session.get(urlfiles, proxies=self.proxy, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            _qf_el = soup.find('input', {'name': '_qf__core_user_form_private_files'})
            _qf__core_user_form_private_files = _qf_el['value'] if _qf_el else "1"
            sesskey = self.sesskey or (soup.find('input', attrs={'name': 'sesskey'})['value'] if soup.find('input', attrs={'name': 'sesskey'}) else '')
            params = self.extract_filemanager_params(resp.text, soup)
            filepath = '/'
            payload = {'sesskey': sesskey, 'client_id': params['client_id'], 'filepath': filepath, 'itemid': params['itemid'], 'filename': name}
            postdelete = self.path + 'repository/draftfiles_ajax.php?action=delete'
            self.session.post(postdelete, data=payload, proxies=self.proxy, timeout=15)

            saveUrl = self.path + 'lib/ajax/service.php?sesskey=' + sesskey + '&info=core_form_dynamic_form'
            savejson = [{"index": 0, "methodname": "core_form_dynamic_form", "args": {"formdata": "sesskey=" + sesskey + "&_qf__core_user_form_private_files=" + _qf__core_user_form_private_files + "&files_filemanager=" + str(params['itemid']) + "", "form": "core_user\\form\\private_files"}}]
            headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
            resp3 = self.session.post(saveUrl, json=savejson, headers=headers, proxies=self.proxy, timeout=15)
            return resp3
        except Exception as e:
            print(f"Error delteFile: {e}")
            return None

    def logout(self):
        try:
            logouturl = self.path + 'login/logout.php?sesskey=' + self.sesskey
            self.session.post(logouturl, proxies=self.proxy, timeout=10)
        except Exception:
            pass
