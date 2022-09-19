# Copyright 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2013 Camptocamp SA (author: Guewen Baconnier)
# Copyright 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Automatic Workflow",
    "version": "13.0.1.2.2",
    "category": "Sales Management",
    "license": "AGPL-3",
    "author": "Akretion, "
    "Camptocamp, "
    "Sodexis, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "depends": ["sale_stock", "sales_team"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_view.xml",
        "views/sale_workflow_process_view.xml",
        "data/automatic_workflow_data.xml",
        "views/stock.xml",
    ],
}
