import io
from threading import Thread

import flask
from apkutils.apkfile import BadZipFile, LargeZipFile

from mapadroid.mad_apk import (APKArch, APKType, APKWizard, MADapks,
                               PackageImporter, WizardError, get_apk_status,
                               stream_package)
from mapadroid.madmin.functions import auth_required
from mapadroid.utils import global_variables

from .apkHandler import APKHandler


class APIMadAPK(APKHandler):
    component = 'mad_apk'
    default_sort = None
    description = 'GET/Delete MAD APKs'
    uri_base = 'mad_apk'

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[
            1].lower() in global_variables.MAD_APK_ALLOWED_EXTENSIONS

    @auth_required
    def get(self, apk_type: APKType, apk_arch: APKArch):
        if flask.request.url.split('/')[-1] == 'download':
            return stream_package(self.dbc, self.storage_obj, apk_type, apk_arch)
        elif flask.request.url.split('/')[-1] == 'reload':
            self.storage_obj.reload()
            return (None, 200)
        else:
            data = get_apk_status(self.storage_obj)
            if apk_type is None and apk_arch is APKArch.noarch:
                return (get_apk_status(self.storage_obj), 200)
            else:
                try:
                    return (data[apk_type][apk_arch], 200)
                except KeyError:
                    return (data[apk_type], 200)

    @auth_required
    def post(self, apk_type: APKType, apk_arch: APKArch):
        is_upload: bool = False
        apk: io.BytesIO = None
        filename: str = None
        if 'multipart/form-data' in self.api_req.content_type:
            filename = self.api_req.data['data'].get('filename', None)
            try:
                apk = io.BytesIO(self.api_req.data['files'].get('file').read())
            except AttributeError:
                return ('No file present', 406)
            is_upload = True
        if self.api_req.content_type == 'application/octet-stream':
            filename = self.api_req.headers.get('filename', None)
            apk = io.BytesIO(self.api_req.data)
            is_upload = True
        if is_upload:
            if filename is None:
                return ('filename must be specified', 406)
            elems: MADapks = get_apk_status(self.storage_obj)
            try:
                elems[apk_type][apk_arch]
            except KeyError:
                return ('Non-supported Type / Architecture', 406)
            filename_split = filename.rsplit('.', 1)
            if filename_split[1] in ['zip', 'apks']:
                mimetype = 'application/zip'
            elif filename_split[1] == 'apk':
                mimetype = 'application/vnd.android.package-archive'
            else:
                return ('Unsupported extension', 406)
            try:
                PackageImporter(apk_type, apk_arch, self.storage_obj, apk, mimetype)
                if 'multipart/form-data' in self.api_req.content_type:
                    return flask.redirect(None, code=201)
                return (None, 201)
            except (BadZipFile, LargeZipFile) as err:
                return (str(err), 406)
            except WizardError as err:
                self._logger.warning(err)
                return (str(err), 406)
            except Exception:
                self._logger.opt(exception=True).critical("An unhandled exception occurred!")
                return (None, 500)
        else:
            try:
                call = self.api_req.data['call']
                wizard = APKWizard(self.dbc, self.storage_obj, self._args.maddev_api_token)
                if call == 'import':
                    thread_args = (apk_type, apk_arch)
                    upload_thread = Thread(name='PackageWizard', target=wizard.apk_download, args=thread_args)
                    upload_thread.start()
                    return (None, 204)
                elif call == 'search':
                    wizard.apk_search(apk_type, apk_arch)
                    return (None, 204)
                elif call == 'search_download':
                    try:
                        wizard.apk_all_actions()
                        return (None, 204)
                    except TypeError:
                        return (None, 404)
                else:
                    return (call, 501)
            except KeyError:
                import traceback
                traceback.print_exc()
                return (call, 501)

        return (None, 500)

    @auth_required
    def delete(self, apk_type: APKType, apk_arch: APKArch):
        if apk_type is None:
            return (None, 404)
        resp = self.storage_obj.delete_file(apk_type, apk_arch)
        if type(resp) == flask.Response:
            return resp
        if resp:
            del_where = {
                "usage": apk_type.value
            }
            self.dbc.autoexec_delete("mad_apk_autosearch", del_where)
            return (None, 202)
        return (None, 404)
