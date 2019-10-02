erpnext.work_order.make_se = function (frm, purpose) {
	if (!frm.doc.skip_transfer) {
		var max = (purpose === "Manufacture") ?
			flt(frm.doc.material_transferred_for_manufacturing) - flt(frm.doc.produced_qty) :
			flt(frm.doc.qty) - flt(frm.doc.material_transferred_for_manufacturing);
	} else {
		var max = flt(frm.doc.qty) - flt(frm.doc.produced_qty);
	}

	max = flt(max, precision("qty"));

	frappe.prompt({
		fieldtype: "Float", label: __("Qty for {0}", [purpose]), fieldname: "qty",
		description: __("Max: {0}", [max]), 'default': max
	},
	function (data) {
		if (data.qty > max) {
			frappe.msgprint(__("Quantity must not be more than {0}", [max]));
			return
		};

		let method, args;
		if (frm.doc.warranty_claim) {
			method = "repairs.api.make_stock_entry_for_repair";
			args = {
				"work_order_id": frm.doc.name,
				"repair_item": frm.doc.production_item,
				"serial_no": frm.doc.serial_number
			};
		} else {
			method = "erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry";
			args = {
				"work_order_id": frm.doc.name,
				"purpose": purpose,
				"qty": data.qty
			};
		};

		frappe.call({
			method: method,
			args: args,
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	}, __("Select Quantity"), __("Make"));
};