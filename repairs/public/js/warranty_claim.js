frappe.ui.form.on("Warranty Claim", {
	refresh: () => {
		if (!cur_frm.doc.__islocal) {
			// TODO: functionify
			cur_frm.add_custom_button(__('Quotation'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_quotation",
					frm: cur_frm
				});
			}, __("Make"));

			cur_frm.add_custom_button(__('Stock Receipt'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_stock_entry",
					frm: cur_frm
				});
			}, __("Make"));

			cur_frm.add_custom_button(__('Invoice'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_invoice",
					frm: cur_frm
				});
			}, __("Make"));

			cur_frm.add_custom_button(__('Payment'), () => {
				frappe.model.open_mapped_doc({
					method: "repairs.utils.make_invoice",
					frm: cur_frm
				});
			}, __("Make"));
		};
	},
});
