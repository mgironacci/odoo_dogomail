import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)


class DogomailDomainController(http.Controller):
    @http.route("/dogomail/close", type="http", auth="user")
    def dogomail_close(self, **kw):
        values = {}
        for field_name, field_value in kw.items():
            if field_name.endswith("_id"):
                values[field_name] = int(field_value)
            else:
                values[field_name] = field_value
        dogomail = (
            http.request.env["sale.dogomail.domain"]
            .sudo()
            .search([("id", "=", values["dogomail_id"])])
        )
        dogomail.stage_id = values.get("stage_id")

        return werkzeug.utils.redirect("/my/dogomail/" + str(dogomail.id))

    # @http.route("/submitted/ticket", type="http", auth="user", website=True, csrf=True)
    # def submit_ticket(self, **kw):
    #     category = http.request.env["helpdesk.ticket.category"].browse(
    #         int(kw.get("category"))
    #     )
    #     company = category.company_id or http.request.env.user.company_id
    #     vals = {
    #         "company_id": company.id,
    #         "category_id": category.id,
    #         "description": plaintext2html(kw.get("description")),
    #         "name": kw.get("subject"),
    #         "attachment_ids": False,
    #         "channel_id": request.env["helpdesk.ticket.channel"]
    #         .sudo()
    #         .search([("name", "=", "Web")])
    #         .id,
    #         "partner_id": request.env.user.partner_id.id,
    #         "partner_name": request.env.user.partner_id.name,
    #         "partner_email": request.env.user.partner_id.email,
    #     }
    #     if company.helpdesk_mgmt_portal_select_team:
    #         team = http.request.env["helpdesk.ticket.team"].search(
    #             [("id", "=", int(kw.get("team"))), ("show_in_portal", "=", True)]
    #         )
    #         vals.update({"team_id": team.id})
    #     new_ticket = request.env["helpdesk.ticket"].sudo().create(vals)
    #     new_ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)
    #     if kw.get("attachment"):
    #         for c_file in request.httprequest.files.getlist("attachment"):
    #             data = c_file.read()
    #             if c_file.filename:
    #                 request.env["ir.attachment"].sudo().create(
    #                     {
    #                         "name": c_file.filename,
    #                         "datas": base64.b64encode(data),
    #                         "res_model": "helpdesk.ticket",
    #                         "res_id": new_ticket.id,
    #                     }
    #                 )
    #     return werkzeug.utils.redirect("/my/ticket/%s" % new_ticket.id)
