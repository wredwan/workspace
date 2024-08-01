from odoo import fields, models, api, _
from odoo.exceptions import UserError

class Project(models.Model):
    _inherit = "project.project"
    _parent_store = True
    _parent_name = "parent_id"


    is_contract = fields.Boolean("SLA", default=False)
    sla_policy_ids = fields.Many2many('helpdesk.sla', string='SLA Policies', domain=[("is_contract", "=", True)])


    parent_path = fields.Char(index=True)
    parent_id = fields.Many2one(
        comodel_name="project.project",
        string="Parent Project",
        index=True,
        tracking=True,
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        comodel_name="project.project",
        string="Sub-projects",
        inverse_name="parent_id",
        copy=True,
    )
    child_ids_count = fields.Integer(compute="_compute_child_ids_count", store=True)
    #ticket_count = fields.Integer(compute='_compute_ticket_count', string="Ticket Count")

    sla_line = fields.One2many(
        'project.sla.line',
        'project_id',
        string='Project Details',
        auto_join=True,
        copy=True,
    )

    opportunity_id = fields.Many2one(
        'crm.lead',
        'Opportunity',
        copy=False,
        tracking=True,
    )
    opp_user_id = fields.Many2one(
        'res.users',
        'Sale Owner',
        copy=False,
        tracking=True,
    )
    opp_industry_id = fields.Many2one(
        'res.partner.industry',
        'Sector',
        copy=False,
        tracking=True,
    )
    opp_project_user_id = fields.Many2one(
        'res.users',
        'Opportunity PM',
        copy=False,
        tracking=True,
    )
    support_type = fields.Selection(
        [('remote', 'Remotely'), ('onsite', 'Onsite'), ('both', 'Both')],
        string='Support Type',
        tracking=True,
    )
    sle_cover_time = fields.Selection(
        [('standard', '8 hours a day, 5 days a week'), ('prime', '24 hours a day, 7 days a week')],
        string='Coverage Time',
        default="standard",
        tracking=True
    )
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
                                          related='company_id.currency_id')
    company_currency_amount = fields.Monetary(string='Company Currency Total', compute='_compute_company_currency_rate',
                                              currency_field='company_currency_id')
    project_currency_id = fields.Many2one('res.currency', string='Contract Currency', tracking=True)
    project_amount_untaxed = fields.Monetary(string='Untaxed Amount', tracking=True, currency_field='project_currency_id')

    def _compute_company_currency_rate(self):
        for project in self:
            price = project.project_currency_id._convert(project.project_amount_untaxed, project.company_currency_id, project.company_id,
                                                       project.date_start or fields.Date.today())
            project.company_currency_amount = price

#    @api.depends('date', 'type_id', 'partner_id')
#    def _compute_project_code(self):
#        if self.date and self.is_fsm:
#            x_day = str(self.date.day)
#            x_month = str(self.date.month)
#            x_year = str(self.date.year)
#            x_sla = x_year + x_month + x_day
#            type = self.type_id.code or '-'
#            partner = self.partner_id.ref or '-'
#            self.sequence_code = partner + type + x_sla
#        else:
#            self.sequence_code = '/'


 #   @api.constrains('partner_id')
 #   def _check_project_sla(self):
 #       if self.is_fsm:
 #           if not self.partner_id:
 #               raise ValidationError('The customer must be selected first !')
 #           elif not self.partner_id.ref:
 #               raise ValidationError('You must add the customer code !')
 #           elif not self.date:
 #               raise ValidationError('Please add the expiration date for the project !')
 #           elif not self.type_id:
 #               raise ValidationError('Please add the project type !')


    @api.depends("child_ids")
    def _compute_child_ids_count(self):
        for project in self:
            project.child_ids_count = len(project.child_ids)

    @api.constrains("parent_id")
    def check_recursion(self):
        for rec in self:
            if not super(Project, rec)._check_recursion():
                raise UserError(_("You can not create recursive projects."))
        return True

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        for project in self:
            project.partner_id = project.parent_id.partner_id


    @api.constrains("active")
    def check_parent_active(self):
        for account in self.filtered(
            lambda a: a.active
            and a.parent_id
            and a.parent_id not in self
            and not a.parent_id.active
        ):
            raise UserError(
                _("Please activate first parent account %s")
                % account.parent_id.complete_name
            )



    def action_open_child_project(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({
            'default_stage_id': self.stage_id.id,
            'default_parent_id': self.id,
            'default_partner_id': self.partner_id,
            'default_analytic_account_id': self.analytic_account_id.id,
            'default_date_start': self.date_start,
            'default_date': self.date,
            'default_sle_cover_time': self.sle_cover_time,
            'default_opportunity_id': self.opportunity_id.id,
            'default_opp_project_user_id': self.opp_project_user_id,
            'default_opp_user_id': self.opp_user_id,
            'default_opp_industry_id': self.opp_industry_id,
            'default_allow_billable': False,
        })
        domain = [("parent_id", "=", self.id)]
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "name": "Sub of %s" % self.name,
            "view_mode": "tree,form,graph",
            "res_model": "project.project",
            "target": "current",
            "context": ctx,
            "domain": domain,
        }


    @api.onchange('opportunity_id')
    def onchange_opportunity_id(self):
        if self.opportunity_id:
            self.opp_project_user_id = self.opportunity_id.project_user_id
            #self.analytic_account_id = self.opportunity_id.analytic_account_id
            self.opp_industry_id = self.opportunity_id.industry_id
            self.opp_user_id = self.opportunity_id.user_id
            self.allow_billable = False
            self.allow_timesheets = False