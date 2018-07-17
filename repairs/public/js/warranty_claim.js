frappe.ui.form.on("Warranty Claim", {
	refresh: (frm) => {
		if (!frm.doc.__islocal) {
			var method_mappings = {
				'Quotation': 'make_quotation',
				'Stock Receipt': 'make_stock_entry',
				'Repair': 'make_production_order',
				'Invoice': 'make_invoice',
				'Delivery': 'make_delivery_note'
			};

			Object.keys(method_mappings).forEach(label => {
				frm.add_custom_button(__(`${label}`), () => {
					frappe.model.open_mapped_doc({
						method: `repairs.api.${method_mappings[label]}`,
						frm: frm
					});
				}, __("Make"));
			});
		};
	},
});
