from odoo import api, fields, models, _
from odoo.osv import expression

class ProjectSlaLine(models.Model):
    _name = 'project.sla.line'
    _description = 'SLA Project Details'

    project_id = fields.Many2one('project.project', string='Project', required=True, ondelete='cascade', index=True,
                                 copy=False)
    product_temp_id = fields.Many2one('product.template', string='Product', required=True)
    product_brand_id = fields.Many2one('product.brand', string='Brand', related='product_temp_id.product_brand_id')
    product_serial = fields.Char(string='Product Serial',)
    default_code = fields.Char(string='Part No.', store=True, related='product_temp_id.default_code')
    partner_id = fields.Many2one('res.partner', string='Customer', related='project_id.partner_id', store=True)

    def name_get(self):
        result = []
        for product in self:
            name = (("[%(brand)s] [%(code)s] %(name)s") %
                    {
                        "brand": product.product_temp_id.product_brand_id.name,
                        "code": product.product_temp_id.default_code,
                        "name": product.product_temp_id.name
                    }
                    )
            if product.product_serial:
                name = _("%(name)s Serial: %(serial)s") % {
                        "name": name,
                        "serial": product.product_serial,}
            result.append((product.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = [
                '|',
                '|',
                '|',
                ('product_temp_id.name', '=ilike', '%' + name + '%'),
                ('product_temp_id.default_code', '=ilike', '%' + name + '%'),
                ('product_serial', '=ilike', '%' + name + '%'),
                ('product_brand_id.name', '=ilike', '%' + name + '%')
            ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        prods = self.search(domain + args, limit=limit)
        return prods.name_get()

