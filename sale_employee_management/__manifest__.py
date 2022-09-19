# © 2016 Akretion (<https://www.akretion.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Gestión de ventas con empleados",
    "version": "13.0.1.2.0",
    "development_status": "Production/Stable",
    "license": "AGPL-3",
    "author": "Meditech",
    "website": "",
    "category": "Sale",
    "depends": ["hr", "sale", 'account'],
    "data": [
        #"security/account_payment_mode.xml",
        #"security/ir.model.access.csv",
        "views/sale_order.xml",
        'views/account_move.xml',
    ],
    #"demo": ["demo/payment_demo.xml"],
    "installable": True,
}
