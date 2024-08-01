# Copyright 2015 ADHOC SA (http://www.adhoc.com.ar)
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Custom Project & SLAs",
    "version": "15.0.0.4.3",
    "author": "Walid Redwan,",
    "license": "AGPL-3",
    "depends": [
        "website_helpdesk_form",
        "project_type",
        "crm_custom",
    ],
    "category": "Customizations",
    "data": [
        "security/ir.model.access.csv",
        "security/project_security.xml",
        "views/project_project_views.xml",
        "views/portal_custom_template.xml",
        "views/helpdesk_views.xml",
        "views/helpdesk_portal_templates.xml",
    ],
    "installable": True,
    "application": False,
}
