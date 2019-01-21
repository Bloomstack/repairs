/* global frappe, erpnext, __ */
/* eslint camelcase: ["error", { properties: "never"} ] */

frappe.ui.form.on("Sales Invoice", {
	refresh: (frm) => {
		let warranty_claims = frm.doc.items
			.map(item => item.warranty_claim)
			.filter(claim => claim)

		if (frm.is_new() && warranty_claims.length > 0) {
			frappe.db.get_value('Repair Settings', { name: 'Repair Settings' }, 'invoice_naming_series', (r) => {
				if (r.invoice_naming_series) {
					frm.doc.naming_series = r.invoice_naming_series;
				}
			});
		}
	}
});