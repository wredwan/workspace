import logging

from odoo import http, models
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)
class HelpdeskTicketController(http.Controller):

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


    def _prepare_submit_ticket_vals(self, **kw):
        """
        Prepare dictionary containing values for creating a new Helpdesk ticket
        """
        vals = {
            'company_id': request.env.company.id,
            'partner_id': request.env.user.partner_id.id,
            'partner_name': request.env.user.partner_id.name,
            'partner_email': request.env.user.partner_id.email,
            # ... other relevant ticket fields (name, description, etc.)
            'name': kw.get('name'),
            'description': plaintext2html(kw.get('description')),
        }

        # Extract data from form submission
        ticket_type_id = int(kw.get('ticket_type', 0))
        product_id = int(kw.get('sla_product_id', 0))

        # Set SLA and ticket type based on form selection (and potential validation)
        if ticket_type_id:
            vals['ticket_type_id'] = ticket_type_id
        if product_id:
            sla_product = request.env['project.sla.line'].sudo().search([('id', '=', product_id)], limit=1)
            if sla_product:
                vals['sla_product_id'] = sla_product.id
        return vals

    @http.route('/submitted/ticket', type='http', auth='user', website=True, csrf=True)
    def helpdesk_submit_ticket(self, **kw):
        """
        Handle form submission and create a new Helpdesk ticket
        """
        # Extract and validate data from form (assuming validation in template or code)
        vals = self._prepare_submit_ticket_vals(**kw)
        if vals:
            ticket = request.env['helpdesk.ticket'].sudo().create(vals)
            # Redirect to success page or ticket details (modify as needed)
            return request.redirect('/helpdesk/ticket/%s' % ticket.id)  # Replace with your desired URL
        else:
            # Handle validation errors (optional: display error message in template)
            return request.redirect('/new/ticket')  # Redirect back to form
