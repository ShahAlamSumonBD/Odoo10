# -*- coding: utf-8 -*-
# © 2013 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "GBS HR Calendar",
    "summary": """""",
    "version": "1.0.0",
    "author": "Genweb2 Limited",
    "website": "http://www.genweb2.com",
    "license": "AGPL-3",
    "category": "Human Resources",
    "depends": ["hr","hr_holidays"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_leave_fiscal_year_views.xml",
    ],
    'installable': True,
    'application': True
}
