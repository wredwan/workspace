import base64
import json
from psycopg2 import IntegrityError

from odoo import _

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers import form
from odoo.exceptions import ValidationError
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

    def _prepare_submit_ticket_vals(self, **kwargs):

        vals = {
            'company_id': request.env.company.id,
            'partner_id': request.env.user.partner_id.id,
            'partner_name': request.env.user.partner_id.name,
            'partner_email': request.env.user.partner_id.email,
            'name': kwargs.get('name'),
            'description': plaintext2html(kwargs.get('description')),
            'email_cc': kwargs.get('email_cc'),
            'partner_phone': kwargs.get('partner_phone'),
        }
        team_id = int(kwargs.get('team_id', 0))
        ticket_type_id = int(kwargs.get('ticket_type_id', 0))
        sla_product_id = int(kwargs.get('sla_product_id', 0))

        if team_id:
            vals['team_id'] = team_id

        if ticket_type_id:
            vals['ticket_type_id'] = ticket_type_id
        if sla_product_id:
            vals['sla_product_id'] = sla_product_id

        return vals

    def _handle_website_form(self, model_name, **kwargs):
        if model_name == 'helpdesk.ticket':
            vals = self._prepare_submit_ticket_vals(**kwargs)
            ticket_id = request.env['helpdesk.ticket'].sudo().create(vals)
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name)])
            data = self.extract_data(model_record, request.params)
            if 'ticket_attachment' in request.params \
                    or request.httprequest.files or data.get('attachments'):
                attached_files = data.get('attachments')
                for attachment in attached_files:
                    attached_file = attachment.read()
                    request.env['ir.attachment'].sudo().create({
                        'name': attachment.filename,
                        'res_model': 'helpdesk.ticket',
                        'res_id': ticket_id.id,
                        'type': 'binary',
                        'datas': base64.encodebytes(attached_file),
                    })
            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = ticket_id.id
            return json.dumps({'id': ticket_id.id})
        else:
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name)])
            if not model_record:
                return json.dumps({
                    'error': _("The form's specified model does not exist")
                })
            try:
                data = self.extract_data(model_record, request.params)
            # If we encounter an issue while extracting data
            except ValidationError as error:
                return json.dumps({'error_fields': error.args[0]})
            try:
                id_record = self.insert_record(request, model_record,
                                               data['record'], data['custom'],
                                               data.get('meta'))
                if id_record:
                    self.insert_attachment(model_record, id_record,
                                           data['attachments'])
                    # in case of an email, we want to send it immediately
                    # instead of waiting for the email queue to process
                    if model_name == 'mail.mail':
                        request.env[model_name].sudo().browse(id_record).send()
            # Some fields have additional SQL constraints that we can't check
            # generically Ex: crm.lead.probability which is a float between 0
            # and 1 TODO: How to get the name of the erroneous field ?
            except IntegrityError:
                return json.dumps(False)
            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = id_record
            return json.dumps({'id': id_record})

