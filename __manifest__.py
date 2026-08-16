{
    "name": "Devolución, Despacho y Exchange de Inventario desde Facturación (MBA Consultings)",
    "version": "18.0.1.2.1",
    "category": "Inventory/Accounting",
    "summary": "Devolución automática desde NC, despacho desde facturas directas y exchange mano a mano | MBA Consultings",
    "author": "MBA Consultings, Brooks Gonzalez",
    "website": "https://mbaconsultings.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "stock",
        "sale_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_invoice_stock_return_wizard_views.xml",
        "wizard/account_invoice_stock_delivery_wizard_views.xml",
        "wizard/account_invoice_stock_exchange_wizard_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
