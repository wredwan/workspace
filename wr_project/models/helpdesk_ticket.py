from odoo import api, fields, models, _

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    partner_id = fields.Many2one(store=True)
    commercial_partner_id = fields.Many2one(store=True)
    sla_project_id = fields.Many2one(
        string='SLA Contract',
        related='sla_product_id.project_id',
        store=True,)
    sla_product_id = fields.Many2one(
        'project.sla.line',
        string='Product',
        tracking=True,)