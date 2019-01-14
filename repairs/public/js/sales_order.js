/* global frappe, erpnext, __ */
/* eslint camelcase: ["error", { properties: "never"} ] */

frappe.ui.form.on("Sales Order", {
	refresh: (frm) => {
		if (frm.doc.docstatus == 0) {
			frm.add_custom_button(__("Warranty Claim"), () => {
				frm.trigger("get_service_items");
			}, __("Get items from"));
		}
	},

	onload_post_render: (frm) => {
		// Load the "Get Items" dialog if a Sales Order is created
		// from a Warranty Claim to allow user to add other Claims
		// from the same Customer, if any
		let warranty_claims = frm.doc.items
			.map(item => item.warranty_claim)
			.filter(claim => claim)

		if (frm.is_new() && warranty_claims.length > 0) {
			frappe.call({
				method: "repairs.api.get_customer_claim_count",
				args: {
					customer: frm.doc.customer
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
		let warranty_claims = frm.doc.items
			.map(item => item.warranty_claim)
			.filter(claim => claim)

		erpnext.utils.map_current_doc({
			method: "repairs.api.make_sales_order",
			source_doctype: "Warranty Claim",
			target: frm,
			date_field: "complaint_date",
			setters: {
				customer: frm.doc.customer,
				status: ""
			},
			get_query_filters: {
				name: ["NOT IN", warranty_claims],
				customer: frm.doc.customer,
				status: ["NOT IN", ["Completed", "Offline", "Declined", "Cancelled"]],
				billing_status: "To Bill"
			}
		});
	}
});