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

        """Website Help Desk Form"""
        if model_name == 'helpdesk.ticket':

            values = super()._handle_website_form(model_name, **kwargs)  # Get base values

            product = request.params.get('sla_product_id')

            if product:
                try:
                    product_id = int(product)  # Convert string ID to int
                    sla_product = request.env['project.sla.line'].sudo().search(
                        [('id', '=', product_id)])
                    if sla_product:
                        # Check if 'sla_product_id' exists in the values dictionary
                        if 'sla_product_id' in values and isinstance(values['sla_product_id'], dict):
                            values['sla_product_id']['id'] = sla_product.id  # Assuming a nested dictionary
                        else:
                            # Handle case where 'sla_product_id' is not a dictionary or missing (e.g., log a warning)
                            pass
                    else:
                        # Handle case where search doesn't find a record (e.g., log a warning)
                        pass
                except ValueError:
                    # Handle cases where product cannot be converted to int (e.g., log a warning)
                    pass

            return values  # Return updated values


    def _handle_website_form(self, model_name, **kwargs):

        """Website Help Desk Form"""
        if model_name == 'helpdesk.ticket':
            rec_val = {
                'company_id': request.env.company.id,
                'partner_id': request.env.user.partner_id.id,
                'partner_name': request.env.user.partner_id.name,
                'partner_email': request.env.user.partner_id.email,
                'name': kwargs.get('name'),
                'description': plaintext2html(kwargs.get('description')),
                'email_cc': kwargs.get('email_cc'),
                'partner_phone': kwargs.get('partner_phone'),
            }

            # Extract portal user selections from form data
            team_id = int(kwargs.get('team_id', 0))
            ticket_type_id = int(kwargs.get('ticket_type_id', 0))
            sla_product_id = int(kwargs.get('sla_product_id', 0))


            # Set team, ticket type, and SLA product based on selections
            if team_id:
                rec_val['team_id'] = team_id
            if ticket_type_id:
                rec_val['ticket_type_id'] = ticket_type_id
            if sla_product_id:
                rec_val['sla_product_id'] = sla_product_id  # Assuming SLA field is 'sla_id'

            new_ticket = request.env['helpdesk.ticket'].sudo().create(rec_val)

            if 'attachment' in request.params:
                for c_file in request.httprequest.files.getlist("attachment"):
                    data = c_file.read()
                    if c_file.filename:
                        request.env["ir.attachment"].sudo().create(
                            {
                                "name": c_file.filename,
                                "datas": base64.b64encode(data),
                                "res_model": "helpdesk.ticket",
                                "res_id": new_ticket.id,
                            }
                        )

            # Handle attachments (optional)
            # ... (Implement your logic for handling attachments from request.params or files)
            # Redirect to success page or ticket details (modify as needed)
            # return super()._handle_website_form(model_name, **kwargs)
            return request.redirect('/helpdesk/ticket/%s' % new_ticket.id)  # Replace with your desired URL











