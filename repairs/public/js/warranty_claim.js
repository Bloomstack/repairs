frappe.ui.form.on("Warranty Claim", {
	refresh: (frm) => {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Quotation'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_quotation",
					frm: frm
				});
			}, __("Make"));

			frm.add_custom_button(__('Stock Receipt'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_stock_entry",
					frm: frm
				});
			}, __("Make"));

			frm.add_custom_button(__('Repair'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_production_order",
					frm: frm,
					run_link_triggers: true
				});
			}, __("Make"));

			frm.add_custom_button(__('Invoice'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_invoice",
					frm: frm
				});
			}, __("Make"));

			frm.add_custom_button(__('Delivery'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_delivery_note",
					frm: frm
				});
			}, __("Make"));
		};
	},
});
