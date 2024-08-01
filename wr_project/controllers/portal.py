import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)


class HelpdeskTicketController(http.Controller):

    def _get_default_team(self):
        return (
            http.request.env["helpdesk.team"]
            .with_company(request.env.company.id)
            .search([], limti=1)
        )

    def _get_ticket_type(self):
        return (
            http.request.env["helpdesk.ticket.type"]
            .with_company(request.env.company.id)
            .search([])
            if request.env["helpdesk.ticket.type"].check_access_rights('read', raise_exception=False) else 0
        )

    def _get_sla_products(self):
        partner = request.env.user.partner_id.commercial_partner_id
        return (
            http.request.env["project.sla.line"]
            .with_company(request.env.company.id)
            .search(
                [
                    ("project_id.active", "=", True),
                    ("project_id.is_contract", "=", True),
                    ("partner_id", "=", partner.id),
                ])
            if request.env["project.sla.line"].check_access_rights('read', raise_exception=False) else 0
        )
    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        email = http.request.env.user.email
        name = http.request.env.user.name
        company = request.env.company
        return http.request.render(
            "wr_project.portal_create_ticket",
            {
                "sla_products": self._get_sla_products(),
                "email": email,
                "name": name,
                "ticket_type": self._get_ticket_type(),
                "team": self._get_default_team(),
            },
        )

    def _prepare_submit_ticket_vals(self, **kw):
        company = http.request.env.company
        vals = {
            "company_id": company.id,
            "team_id": team.id,
            "description": plaintext2html(kw.get("description")),
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env.ref(
                "helpdesk_mgmt.helpdesk_ticket_channel_web", False
            ).id,
            "partner_id": request.env.user.partner_id.id,
            "partner_name": request.env.user.partner_id.name,
            "partner_email": request.env.user.partner_id.email,
        }
        return vals