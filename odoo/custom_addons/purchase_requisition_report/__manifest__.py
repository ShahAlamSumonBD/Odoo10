{
    'name': 'Purchase Requisition Report',
    'author': 'Genweb2 Limited',
    'website': 'www.genweb2.com',
    "category": "Purchase Management",
    'version': '1.0',
    'depends': [
        "purchase_request",
        "purchase",
        "product"
    ],
    'data': [
        'report/purchase_requisition_report_template.xml',
        'report/report_paperformat.xml',
        'wizard/purchase_requisition_report_wizard_views.xml',
    ],

    'installable': True,
    'application': True,
}