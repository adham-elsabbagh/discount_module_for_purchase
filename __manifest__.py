{
    'name': 'purchase Discount on Total Amount',
    'version': '11.0',
    'category': 'purchase Management',
    'summary': "Discount on total purchase with Discount limit",
    'author': 'Raed Technology',
    'company': 'Raed Technology',
    'website': 'http://www.raedtechnology.com',

    'description': """

Sale and purchase Discount for Total Amount
=======================
Module to manage discount on total amount in purchase.
        as an specific amount or percentage
""",
    'depends': ['sale',
                'account',
                'purchase',
                'account_discount_total_adham',
                ],
    'data': [
        'views/purchase_view.xml',
        'views/purchase_order_report.xml',
        'views/purchase_discount_view.xml',

    ],
    'demo': [
    ],
    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}
