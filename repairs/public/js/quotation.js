/* global frappe, erpnext, __ */
/* eslint camelcase: ["error", { properties: "never"} ] */

frappe.ui.form.on("Quotation", {
	refresh: (frm) => {
		frm.add_custom_button(__("Warranty Claim"), () => {
			frm.trigger("get_service_items");
		}, __("Get items from"));
	},

	onload_post_render: (frm) => {
		// Load the "Get Items" dialog if a Quotation is created
		// from a Warranty Claim to allow user to add other Claims
		// from the same Customer, if any
		if (frm.doc.__islocal && frm.doc.warranty_claim) {
			frappe.call({
				method: "repairs.api.get_customer_claim_count",
				args: {
					warranty_claim: frm.doc.warranty_claim
				},
				callback: (r) => {
					if (r.message.count > 1) {
						frm.trigger("get_service_items");
					}
				}
			});
		}
	},

	get_service_items: (frm) => {
		erpnext.utils.map_current_doc({
			method: "repairs.api.make_quotation",
			source_doctype: "Warranty Claim",
			target: frm,
			date_field: "complaint_date",
			setters: {
				customer: frm.doc.customer,
				status: ""
			},
			get_query_filters: {
				name: ["!=", frm.doc.warranty_claim],
				customer: frm.doc.customer,
				status: ["not in", ["Completed", "Offline", "Declined", "Cancelled"]],
				billing_status: "To Bill"
			}
		});
	}
});