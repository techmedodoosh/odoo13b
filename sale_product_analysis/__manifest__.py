# © 2016 Akretion (<https://www.akretion.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Sales: Análisis de ventas por producto",
    "version": "13.0.1.2.0",
    "development_status": "Production/Stable",
    "license": "AGPL-3",
    "author": "Meditech",
    "website": "",
    "category": "Sale",
    "depends": ["sale_stock", "stock_account"],
    "data": [
        #"security/account_payment_mode.xml",
        "security/ir.model.access.csv",
        "views/product.xml",
        "views/product_analysis.xml",
        "views/stock_quant.xml",
        "views/stock_valuation_layer.xml",
        #"views/account_payment_mode.xml",
        #"views/res_partner_bank.xml",
        #"views/res_partner.xml",
        #"views/account_journal.xml",
    ],
    #"demo": ["demo/payment_demo.xml"],
    "installable": True,
}
