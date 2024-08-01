import base64
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers import form
from odoo.tools import plaintext2html


class WebsiteForm(form.WebsiteForm):

    def _get_default_team(self):
        """Retrieves the first active team for the current user's company."""
        company = http.request.env.company
        return http.request.env['helpdesk.team'].with_company(company.id).search([], limit=1)

    def _get_ticket_type(self):
        """Retrieves all ticket types with access control for the current company."""
        return (
            http.request.env["helpdesk.ticket.type"]
            .with_company(http.request.env.company.id)
            .search([])
            if http.request.env["helpdesk.ticket.type"].check_access_rights('read', raise_exception=False) else []
        )

    def _get_sla_products(self):
        """Retrieves SLA products accessible to the current user's partner."""
        partner = http.request.env.user.partner_id.commercial_partner_id
        return (
            http.request.env["project.sla.line"]
            .with_company(http.request.env.company.id)
            .search(
                [
                    ("project_id.active", "=", True),
                    ("project_id.is_contract", "=", True),
                    ("partner_id", "=", partner.id),
                ])
        )

    @http.route('/new/ticket', type='http', auth='user', website=True)
    def helpdesk_new_ticket_form(self, **kw):
        """
        Render the Helpdesk ticket form for portal users
        """
        # Retrieve data for dropdown menus
        email = http.request.env.user.email
        name = http.request.env.user.name
        return http.request.render(
            'wr_project.portal_create_ticket',
            {
                'email': email,
                'name': name,
                'sla_products': self._get_sla_products(),
                'default_team': self._get_default_team(),
                'ticket_types': self._get_ticket_type(),
            },
        )

    def _handle_website_form(self, model_name, **kwargs):
        if model_name == 'helpdesk.ticket':
            # Get SLA product ID from request.params (handle potential absence)
            sla_product_id = request.params.get('sla_product_id')

            if sla_product_id:
                try:
                    # Convert sla_product_id to integer (handle potential ValueError)
                    sla_product_id = int(sla_product_id)
                except ValueError:
                    # Handle invalid SLA product ID format (e.g., print warning)
                    print("WARNING: Invalid SLA product ID format:", sla_product_id)
                    sla_product_id = None  # Or set a default value if needed

            # Update kwargs with SLA information (if valid)
            if sla_product_id:
                sla_product = request.env['project.sla.line'].sudo().search([('id', '=', sla_product_id)], limit=1)
                if sla_product:
                    kwargs['sla_product_id'] = sla_product.id  # Assuming 'sla_id' field on 'project.sla.line'

        # Call the parent method with potentially modified kwargs
        return super()._handle_website_form(model_name, **kwargs)





