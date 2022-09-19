# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

from odoo import _, api, fields, models
from odoo.addons.odoope_ruc_validation.models import sunatconstants
import requests
from requests.exceptions import HTTPError
import json
from zipfile import ZipFile
from bs4 import BeautifulSoup
from io import BytesIO
from odoo.exceptions import Warning, UserError
class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _default_country(self):
        return self.env.company.country_id.id

    country_id = fields.Many2one(default=_default_country)
    commercial_name = fields.Char(string="Commercial Name")
    state = fields.Selection([('habido','Habido'),('nhabido','No Habido')], string="State")
    alert_warning_vat= fields.Boolean(string="Alert warning vat", default=False)

    @api.onchange('vat','l10n_latam_identification_type_id')
    def onchange_vat(self):
        res = {}
        self.name = False
        self.commercial_name = False
        self.street = False
        if self.vat: 
            if self.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                if len(self.vat) != 11 :
                    res['warning'] = {'title': _('Warning'), 'message': _('The Ruc must be 11 characters long.')}
                else:
                    company = self.env['res.company'].browse(self.env.company.id) 
                    if company.l10n_pe_ruc_validation == True:
                        self.get_data_ruc()
            elif self.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                if len(self.vat) != 8 :
                    res['warning'] = {'title': _('Warning'), 'message': _('The Dni must be 8 characters long.')}
                else:
                    company = self.env['res.company'].browse(self.env.company.id) 
                    if company.l10n_pe_dni_validation == True:
                        self.get_data_dni()
        if res:
            return res

    def get_data_ruc(self):
        result = self.l10n_pe_ruc_connection(self.vat)
        vals_to_write = {}
        if result:
            vals_to_write['alert_warning_vat'] = False
            vals_to_write['company_type'] = 'company'
            vals_to_write['name'] = str(result['business_name']).strip()
            vals_to_write['commercial_name'] = str(result['commercial_name'] or result['business_name']).strip()
            vals_to_write['street'] = str(result['residence']).strip()
            if result['contributing_condition'] == 'HABIDO':
                vals_to_write['state'] = 'habido'
            else:
                vals_to_write['state'] = 'nhabido'
            if result['value']:
                vals_to_write['l10n_pe_district'] = result['value']['district_id']
                vals_to_write['city_id'] = result['value']['city_id'] 
                vals_to_write['state_id'] = result['value']['state_id'] 
                vals_to_write['country_id'] = result['value']['country_id']
        self.write(vals_to_write)
                
    def get_data_dni(self):
        result = self.l10n_pe_dni_connection(self.vat)
        if result:
            self.write({
                'alert_warning_vat': False,
                'name': str(result['nombre'] or '').strip(),
                'company_type': 'person',
            })

    def l10n_pe_action_query_document_from_ruc_dot_com(self):
        self.ensure_one()
        self = self.with_context(vat_query_service='consulta_web', safe_mode=False)
        vat = (self.vat or '').strip()
        if vat: 
            if self.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                self.get_data_ruc()
            elif self.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                self.get_data_dni()
        return {}

    @api.model
    def sunat_connection(self, ruc):
        session = requests.Session()
        url_sunat = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"
        headers = requests.utils.default_headers()
        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36' 
        data = {}
        try:
            url_numRnd = session.get('https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias?accion=consPorRazonSoc&razSoc=BVA%20FOODS', headers=headers,timeout=12).content
            html_content = BeautifulSoup(url_numRnd, 'html.parser')
            content_form = html_content.find_all('form')
            numRnd = content_form[0].find_all('input')[3].get('value')
            data_ruc = {'accion':'consPorRuc','nroRuc':ruc,'numRnd':numRnd,'actReturn':'1','modo':'1'}
            html_doc = session.post(url=url_sunat,data=data_ruc,headers=headers,timeout=(15,20))
            html_info = BeautifulSoup(html_doc.content, 'html.parser')
            div_info = html_info.find_all("div", {"class": "list-group"})
            div_p_info = div_info[0].find_all("p", {"class": "list-group-item-text"})
            div_h4_info = div_info[0].find_all("h4", {"class": "list-group-item-heading"})
            sunat_cons = None
            if ruc[0] == '1':
                sunat_cons = sunatconstants.PersonaNaturalConstant
                
            elif ruc[0] == '2':
                sunat_cons = sunatconstants.PersonaJuridicaConstant

            number_ruc = (div_h4_info[sunat_cons.number_ruc.value].contents[0])
            data['ruc'] = number_ruc.split(' - ')[0]
            data['business_name'] = number_ruc.split(' - ')[1]
            data['type_of_taxpayer'] = (div_p_info[sunat_cons.type_of_taxpayer.value].contents[0])
            data['estado'] = (div_p_info[sunat_cons.taxpayer_state.value].contents[0])
            data['contributing_condition'] = (div_p_info[sunat_cons.contributing_condition.value].contents[0]).replace('\r', '') \
            .replace('\n', '').strip()
            data['commercial_name'] = (div_p_info[sunat_cons.commercial_name.value].contents[0]).replace('-','').strip()

            residence = (div_p_info[sunat_cons.tax_residence.value].contents[0])
            district = (" ".join(residence.split("-")[-1].split())).title()
            province = (" ".join(residence.split("-")[-2].split())).title()
            address = " ".join(residence.split())
            address = " ".join(residence.split("-")[0:-2])
            prov_ids = self.env['res.city'].search([('name', '=', province),('state_id','!=',False)])
            dist_id = self.env['l10n_pe.res.city.district'].search([('name', '=', district),('city_id', 'in', [x.id for x in prov_ids])], limit=1)
            dist_short_id = self.env['l10n_pe.res.city.district'].search([('name', '=', district)], limit=1)
            if dist_id:
                l10n_pe_district = dist_id
            else:
                l10n_pe_district = dist_short_id

            vals = {}
            if l10n_pe_district:
                vals['district_id'] = l10n_pe_district.id
                vals['city_id'] = l10n_pe_district.city_id.id
                vals['state_id'] = l10n_pe_district.city_id.state_id.id
                vals['country_id'] = l10n_pe_district.city_id.state_id.country_id.id
            data['value'] = vals
            data['residence']  = str(address).strip()

        except Exception:
            self.alert_warning_vat = True
            data = False
        return data

    def _extract_csv_from_zip(self, url_zip,name_zip):
        nombre_txt = name_zip.replace('.zip', '.txt')
        res = requests.get(url_zip)
        zipfile = ZipFile(BytesIO(res.content))
        lineas = list()
        for linea in zipfile.open(nombre_txt).readlines():
            lineas.append(linea.decode('utf-8'))
        json_datos = dict()
        cabeceras = lineas[0].split('|')
        valores = lineas[1].split('|')
        for indice, cabecera in enumerate(cabeceras):
            if indice != len(cabeceras) - 1:
                json_datos[cabecera.strip().lower().replace('-', '').replace('ó', '').replace(' ', '_')] = valores[
                    indice].strip()          
        return json_datos

    def sunat_connection_multi(self, ruc):
        session = requests.Session()
        if self.env.company.l10n_pe_use_proxy:
            url_proxy = "http://%s:%s" % (self.env.company.l10n_pe_proxy_ip, self.env.company.l10n_pe_proxy_port)
            session.proxies = {
                "http": url_proxy,
                "https": url_proxy,
            }
        url_sunat = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsmulruc/jrmS00Alias"
        headers = requests.utils.default_headers()
        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36' 
        data = {}
        try:
            captcha = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsmulruc/captcha"
            text_captcha =session.post(url=captcha,data={'accion':'random'},headers=headers)
            data_ruc = {'accion':'consManual','selRuc':ruc,'numRnd':text_captcha}
            html_doc = session.post(url=url_sunat,data=data_ruc,headers=headers,timeout=(15,20))
            html_info = BeautifulSoup(html_doc.content, 'html.parser')
            table_info = html_info.find_all('a',href=True)
            url_zip = table_info[0]['href']
            name_zip = table_info[0].contents[0]
            json_datos = self._extract_csv_from_zip(url_zip,name_zip)
            data['ruc'] = json_datos['numeroruc']
            data['business_name'] = json_datos['nombre__razonsocial']
            data['type_of_taxpayer'] =  json_datos['tipo_de_contribuyente'] 
            data['estado'] = json_datos['estado_del_contribuyente']
            data['contributing_condition'] = json_datos['condicion_del_contribuyente']
            data['commercial_name'] = json_datos['nombre_comercial']
            provincia = json_datos['provincia'].title()
            distrito = json_datos['distrito'].title()
            prov_ids = self.env['res.city'].search([('name', '=', provincia),('state_id','!=',False)])
            dist_id = self.env['l10n_pe.res.city.district'].search([('name', '=',distrito ),('city_id', 'in', [x.id for x in prov_ids])], limit=1)
            dist_short_id = self.env['l10n_pe.res.city.district'].search([('name', '=', json_datos['distrito'])], limit=1)
            if dist_id:
                l10n_pe_district = dist_id
            else:
                l10n_pe_district = dist_short_id

            vals = {}
            if l10n_pe_district:
                vals['district_id'] = l10n_pe_district.id
                vals['city_id'] = l10n_pe_district.city_id.id
                vals['state_id'] = l10n_pe_district.city_id.state_id.id
                vals['country_id'] = l10n_pe_district.city_id.state_id.country_id.id
            data['value'] = vals
            data['residence']  = json_datos['direccion']
        except Exception:
            self.alert_warning_vat = True
            data = False
        return data


    def _l10n_pe_send_request_to_ruc_com(self, document, type_document):
        settings = self.env['ir.config_parameter'].sudo()
        TOKEN = settings.get_param('odoope_ruc_validation.l10n_pe_ruc_dot_com_token', False)
        TOKEN = (TOKEN or '').strip()
        URL = 'https://ruc.com.pe/api/v1/consultas'
        safe_mode = self.env.context.get('safe_mode', True)

        headers = {
            'Content-Type':'application/json',
            }

        assert type_document in ('ruc', 'dni'), 'Wrong value for type document argument.'

        data = {
            'token': TOKEN,
            type_document : document,
        }

        if not TOKEN:
            raise UserError(' No ha configurado su token para usar el servicio de consulta de ruc y dni con "ruc.com.pe"')

        resp = requests.request('POST', URL, data=json.dumps(data), headers=headers)
        status_code = resp.status_code
        error_msg = False
        if not resp.ok or status_code != 200:
            try:
                resp.raise_for_status()
            except HTTPError:
                if status_code >= 500:
                    error_msg = ('Ocurrió un error interno en el servicio de ruc.com.pe, intente de nuevo en unos minutos')
                else:
                    error = resp.json().get('error', 'Error desconocido')
                    error_msg = ('Error al realizar la consulta con ruc.com.pe.\nDetalle: %s' % error)
        if error_msg:
            if not safe_mode:
                raise UserError(error_msg)
            return {}
        return resp.json()

    @api.model
    def l10n_pe_get_ruc_data_from_ruc_com(self, ruc):
        # TODO ver si es necesario refactorizar el nombre del método
        data = self._l10n_pe_send_request_to_ruc_com(ruc, 'ruc')
        if not data:
            return {}
        top_vals = {}
        if data.get('ubigeo'):
            top_vals.update(self._l10n_pe_get_toponyms_vals_from_zip_code(data['ubigeo']))
            top_vals['district_id'] = top_vals.get('l10n_pe_district', False)
        # parse data:
        result = {
            'business_name': data['nombre_o_razon_social'],
            'commercial_name': data['nombre_o_razon_social'],
            'residence': data['direccion'],
            'contributing_condition': data['condicion_de_domicilio'],
            'value': top_vals,
        }
        return result

    @api.model
    def l10n_pe_ruc_connection(self, ruc):
        data = {}
        ruc_connection = self._context.get('vat_query_service', self.env.user.company_id.l10n_pe_api_ruc_connection) 
        if ruc_connection == 'sunat':
            data = self.sunat_connection(ruc)   
        elif ruc_connection == 'sunat_multi':  
            data = self.sunat_connection_multi(ruc)
        elif ruc_connection == 'consulta_web':
            data = self.l10n_pe_get_ruc_data_from_ruc_com(ruc)
        return data
    
    @api.model
    def reniec_connection(self, dni):
        session = requests.Session()
        headers = requests.utils.default_headers()
        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        url_reniec = 'https://api.reniec.cloud/dni/{dni}'
        data = {}
        try:
            response= session.get(url=url_reniec.format(dni=dni),verify = False,headers=headers).text
            values_response = response.replace('&Ntilde;','Ñ')
            result = json.loads(values_response)
            data['nombre'] = (result['nombres'] + " " +result['apellido_paterno'] + " " + result['apellido_materno'])
        except Exception:
            self.alert_warning_vat = True
            data = False 
        return data

    @api.model
    def jne_connection(self, dni):
        session = requests.Session()
        headers = requests.utils.default_headers()
        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        headers['Content-Type'] = 'application/json;chartset=utf-8'
        headers['Requestverificationtoken'] = 'Dmfiv1Unnsv8I9EoXEzbyQExSD8Q1UY7viyyf_347vRCfO-1xGFvDddaxDAlvm0cZ8XgAKTaWclVFnnsGgoy4aLlBGB5m-E8rGw_ymEcCig1:eq4At-H2zqgXPrPnoiDGFZH0Fdx5a-1UiyVaR4nQlCvYZzAhzmvWxLwkUk6-yORYrBBxEnoG5sm-Hkiyc91so6-nHHxIeLee5p700KE47Cw1'
        url_reniec = 'https://aplicaciones007.jne.gob.pe/srop_publico/Consulta/api/AfiliadoApi/GetNombresCiudadano'
        dni_value = {"CODDNI":dni}
        data = {}
        try:
            response = session.post(url=url_reniec,json=dni_value,headers=headers,timeout=(15)).text
            values_response = response.replace('|',' ')
            result = json.loads(values_response)
            data['nombre'] = result['data']
        except Exception :
            self.alert_warning_vat = True
            data = False 
        return data 

    @api.model     
    def free_api_connection(self, dni):
        url = 'https://dni.optimizeperu.com/api/prod/persons/{dni}'.format(dni=dni)
        headers = {'authorization': 'token 48b5594ab9a37a8c3581e5e71ed89c7538a36f11'}
        data = {}
        try:
            r = requests.get(url, headers=headers,timeout=(15))
            result = r.json()
            name = result.get('first_name') +" "+ result.get('last_name') + " " + result.get('name')
            data['nombre'] = name
        except Exception :
            self.alert_warning_vat = True
            data = False 
        return data  

    @api.model     
    def facturacion_electronica_dni_connection(self, dni):
        url = 'https://www.facturacionelectronica.us/facturacion/controller/ws_consulta_rucdni_v2.php'
        params = {
            'usuario': '10447915125',
            'password': '985511933',
            'documento': 'DNI',
            'nro_documento': dni
        }
        data = {}
        try:
            r = requests.get(url, params, timeout=(15))
            result = r.json()
            name = result.get('result').get('Paterno') +" "+ result.get('result').get('Materno') + " " + result.get('result').get('Nombre')
            data['nombre'] = name
        except Exception :
            self.alert_warning_vat = True
            data = False 

        return data

    @api.model
    def l10n_pe_get_dni_data_from_ruc_com(self, dni):
        # TODO ver si es necesario refactorizar el nombre del método
        data = self._l10n_pe_send_request_to_ruc_com(dni, 'dni')
        if not data:
            return {}
        result = {
            'nombre': data['nombre_completo'],
        }
        return result

    @api.model     
    def l10n_pe_dni_connection(self, dni):
        data = {}
        company = self.env.user.company_id
        dni_connection = self._context.get('vat_query_service', company.l10n_pe_api_dni_connection)
        if dni_connection == 'jne':
            data = self.jne_connection(dni)
        elif dni_connection == 'facturacion_electronica':
            data = self.facturacion_electronica_dni_connection(dni)
        elif dni_connection == 'free_api':
            data = self.free_api_connection(dni)
        elif dni_connection == 'consulta_web':
            data = self.l10n_pe_get_dni_data_from_ruc_com(dni)
        else:
            data = False
        
        return data   

    @api.onchange('l10n_pe_district')
    def _onchange_l10n_pe_district(self):
        if self.l10n_pe_district and self.l10n_pe_district.city_id:
            self.city_id = self.l10n_pe_district.city_id

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id and self.city_id.state_id:
            self.state_id = self.city_id.state_id
        res = {}
        res['domain'] = {}
        res['domain']['l10n_pe_district'] = []
        if self.city_id:
            res['domain']['l10n_pe_district'] += [('city_id','=',self.city_id.id)]
        return res

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id and self.state_id.country_id:
            self.country_id = self.state_id.country_id
        res = {}
        res['domain'] = {}
        res['domain']['city_id'] = []
        if self.state_id:
            res['domain']['city_id'] += [('state_id','=',self.state_id.id)]
        return res

    @api.model
    def _l10n_pe_get_toponyms_vals_from_zip_code(self, zip_code):
        # Meditech
        PE_COUNTRY = self.env.ref('base.pe', False)
        if not zip_code or not PE_COUNTRY:
            return {}

        self._cr.execute('''
        SELECT 
        T.country_id, T.state_id, T.city_id, T.l10n_pe_district, T.zip
        FROM
        (SELECT
            country_id,
            id AS state_id,
            NULL::integer AS city_id,
            NULL::integer AS l10n_pe_district,
            code::text AS zip
            FROM
            res_country_state
            WHERE country_id = %(pe_id)s
            UNION
            SELECT
            country_id,
            state_id,
            id AS city_id,
            NULL::integer AS l10n_pe_district,
            l10n_pe_code::text AS zip
            FROM
            res_city
            WHERE country_id = %(pe_id)s
            UNION
            SELECT
            p.country_id,
            p.state_id,
            p.id AS city_id,
            d.id AS l10n_pe_district,
            d.code::text AS zip
            FROM
            l10n_pe_res_city_district d
            JOIN res_city p ON p.id = d.city_id
            WHERE p.country_id = %(pe_id)s
            )T
        WHERE T.zip::integer = %(zip)s 
        LIMIT 1 ;''', {'pe_id': PE_COUNTRY.id, 'zip': int(zip_code)})

        vals = self._cr.dictfetchall()
        return vals and vals[0] or {}
