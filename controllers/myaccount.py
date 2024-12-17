# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import OrderedDict
from operator import itemgetter

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.osv.expression import AND, OR
from odoo.tools import groupby as groupbyelem

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class CustomerPortalDogomail(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "dogomail_count" in counters:
            dogomail_model = request.env["sale.dogomail.domain"]
            dogomail_count = (
                dogomail_model.search_count([])
                if dogomail_model.check_access_rights("read", raise_exception=False)
                else 0
            )
            values["dogomail_count"] = dogomail_count
        return values

    @http.route(
        ["/my/dogomail", "/my/dogomail/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_dogomail(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in=None,
        groupby=None,
        **kw
    ):
        DogmailDomain = request.env["sale.dogomail.domain"]
        # Avoid error if the user does not have access.
        if not DogmailDomain.check_access_rights("read", raise_exception=False):
            return request.redirect("/my")

        values = self._prepare_portal_layout_values()

        searchbar_sortings = self._dogomail_get_searchbar_sortings()
        searchbar_sortings = dict(
            sorted(
                self._dogomail_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )

        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        for stage in request.env["sale.dogomail.domain.stage"].search([]):
            searchbar_filters[str(stage.id)] = {
                "label": stage.name,
                "domain": [("stage_id", "=", stage.id)],
            }

        searchbar_inputs = self._dogomail_get_searchbar_inputs()
        searchbar_groupby = self._dogomail_get_searchbar_groupby()

        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        if not filterby:
            filterby = "all"
        domain = searchbar_filters.get(filterby, searchbar_filters.get("all"))["domain"]

        if not groupby:
            groupby = "none"

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        if not search_in:
            search_in = "all"
        if search:
            domain += self._dogomail_get_search_domain(search_in, search)

        domain = AND(
            [
                domain,
                request.env["ir.rule"]._compute_domain(DogmailDomain._name, "read"),
            ]
        )

        # count for pager
        dogomail_count = DogmailDomain.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/dogomail",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "groupby": groupby,
                "search": search,
                "search_in": search_in,
            },
            total=dogomail_count,
            page=page,
            step=self._items_per_page,
        )

        order = self._dogomail_get_order(order, groupby)
        dogomail = DogmailDomain.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        request.session["my_dogomail_history"] = dogomail.ids[:100]

        groupby_mapping = self._dogomail_get_groupby_mapping()
        group = groupby_mapping.get(groupby)
        if group:
            grouped_dogomail = [
                request.env["sale.dogomail.domain"].concat(*g)
                for k, g in groupbyelem(dogomail, itemgetter(group))
            ]
        elif dogomail:
            grouped_dogomail = [dogomail]
        else:
            grouped_dogomail = []

        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "grouped_dogomail": grouped_dogomail,
                "page_name": "dogomail",
                "default_url": "/my/dogomail",
                "pager": pager,
                "searchbar_sortings": searchbar_sortings,
                "searchbar_groupby": searchbar_groupby,
                "searchbar_inputs": searchbar_inputs,
                "search_in": search_in,
                "search": search,
                "sortby": sortby,
                "groupby": groupby,
                "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
                "filterby": filterby,
            }
        )
        return request.render("sale_dogomail.portal_my_dogomail", values)

    @http.route(
        ["/my/dogomail/<int:dogomail_id>"], type="http", auth="user", website=True
    )
    def portal_my_dogomail_domain(self, dogomail_id, access_token=None, **kw):
        try:
            dogomail_sudo = self._document_check_access(
                "sale.dogomail.domain", dogomail_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        values = self._dogomail_get_page_view_values(dogomail_sudo, access_token, **kw)
        return request.render("sale_dogomail.portal_dogomail_domain_page", values)

    def _dogomail_get_page_view_values(self, dogomail, access_token, **kwargs):
        closed_stages = request.env["sale.dogomail.domain.stage"].search(
            [("fold", "=", True)]
        )
        values = {
            "closed_stages": closed_stages,
            "page_name": "dogomail",
            "dogomail": dogomail,
            "user": request.env.user,
        }
        return self._get_page_view_values(
            dogomail, access_token, values, "my_dogomail_history", False, **kwargs
        )

    def _dogomail_get_searchbar_sortings(self):
        return {
            "date": {
                "label": _("Newest"),
                "order": "create_date desc",
                "sequence": 1,
            },
            "name": {"label": _("Name"), "order": "name", "sequence": 2},
            "stage": {"label": _("Stage"), "order": "stage_id", "sequence": 3},
        }

    def _dogomail_get_searchbar_groupby(self):
        values = {
            "none": {"input": "none", "label": _("None"), "order": 1},
            "stage": {"input": "stage", "label": _("Stage"), "order": 3},
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _dogomail_get_searchbar_inputs(self):
        values = {
            "all": {"input": "all", "label": _("Search in All"), "order": 1},
            "name": {
                "input": "name",
                "label": _("Search in Title"),
                "order": 3,
            },
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _dogomail_get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ("name", "all"):
            search_domain.append([("name", "ilike", search)])
        return OR(search_domain)

    def _dogomail_get_groupby_mapping(self):
        return {
            "stage": "stage_id",
        }

    def _dogomail_get_order(self, order, groupby):
        groupby_mapping = self._dogomail_get_groupby_mapping()
        field_name = groupby_mapping.get(groupby, "")
        if not field_name:
            return order
        return "%s, %s" % (field_name, order)
