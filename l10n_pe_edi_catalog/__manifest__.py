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

{
    'name' : 'Factura electronica - Catalogos SUNAT',
    'version' : '1.0.1',
    'author' : 'OPeru',
    'category' : 'Accounting & Finance',
    'summary': 'Datos de Tablas para la factura electronica.',
    'license': 'LGPL-3',
    'contributors': [
        'Leonidas Pezo <leonidas@operu.pe>',
    ],
    'description' : """
Factura electronica - Datos Catalogos SUNAT.
====================================

Tablas:
--------------------------------------------
    * Tablas requeridas para los Documentos electronicos Peru

    """,
    'website': 'http://www.operu.pe/contabilidad',
    'depends' : ['base',
                 'account'],
    'data': ['views/catalog_views.xml',
             'security/ir.model.access.csv',   
            ],
    'qweb' : [
    ],
    'demo': [
        #'demo/account_demo.xml',
    ],
    'test': [
        #'test/account_test_users.yml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    "sequence": 1,
    "post_init_hook": "l10n_pe_edi_catalog_init",
    'uninstall_hook': 'l10n_pe_edi_catalog_unistall',
}
