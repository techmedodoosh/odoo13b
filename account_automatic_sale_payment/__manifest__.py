# © 2016 Akretion (<https://www.akretion.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Autiomatic Sale Payment",
    "version": "13.0.1.2.0",
    "development_status": "Production/Stable",
    "license": "AGPL-3",
    "author": "Meditech",
    "website": "",
    "category": "Sale",
    "depends": ["account_payment_sale", "sale_automatic_workflow", "l10n_pe_edi_odoofact", "sale_management"],
    "data": [
        "security/groups.xml",
        #"security/ir.model.access.csv",
        "views/sale_order.xml",
        #"views/account_payment_mode.xml",
        #"views/res_partner_bank.xml",
        #"views/res_partner.xml",
        #"views/account_journal.xml",
    ],
    #"demo": ["demo/payment_demo.xml"],
    "installable": True,
}
