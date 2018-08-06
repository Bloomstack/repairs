frappe.ui.form.on("Warranty Claim", {
	refresh: (frm) => {
		cur_frm.fields_dict.item_code.get_query = (doc, cdt, cdn) => {
			return {
				filters: {
					"item_group": ["in", ["Custom", "Full Retail", "Universal"]],
					"is_sales_item": 1
				}
			};
		};

		cur_frm.fields_dict.services.grid.get_field("item_code").get_query = (doc, cdt, cdn) => {
			return { filters: { "item_group": "Services" } };
		};

		cur_frm.fields_dict.cable.get_query = (doc, cdt, cdn) => {
			return { filters: { "item_group": "Cables" } };
		};

		cur_frm.fields_dict.case.get_query = (doc, cdt, cdn) => {
			return { filters: { "item_group": "Cases" } };
		};

		if (!frm.doc.__islocal) {
			if (!frm.doc.item_received) {
				frm.add_custom_button(__("Stock Receipt"), () => {
					frappe.call({
						method: "repairs.api.make_stock_entry_from_warranty_claim",
						args: {
							doc: frm.doc.name
						},
						callback: (r) => {
							if (!r.exc) {
								frm.reload_doc();
							}
						}
					});
				}, __("Make"));
			};

			if (frm.doc.status == "To Test") {
				var repair_btn = frm.add_custom_button(__("Test Item"), () => {
					var d = new frappe.ui.Dialog({
						title: __("Testing Results"),
						fields: [
							{
								label: __("Enter Results"),
								fieldname: "testing_details",
								fieldtype: "Text",
								reqd: 1
							}
						],
						primary_action: () => {
							var data = d.get_values();

							frm.set_value("status", "To Repair");
							frm.set_value("billing_status", frm.doc.is_under_warranty ? "Under Warranty" : "To Bill");
							frm.set_value("tested_by", frappe.session.user);
							frm.set_value("testing_date", frappe.datetime.now_datetime());
							frm.set_value("testing_details", data.testing_details);
							frm.save();

							d.hide();
						},
						primary_action_label: __("Record")
					});
					d.show();
				});
				repair_btn.addClass('btn-primary');
			};

			if (frm.doc.billing_status == "To Bill") {
				frm.add_custom_button(__("Quotation"), () => {
					frappe.model.open_mapped_doc({
						method: "repairs.api.make_quotation",
						frm: frm,
						run_link_triggers: true
					});
				}, __("Make"));
			};

			if (frm.doc.status == "To Repair") {
				var repair_btn = frm.add_custom_button(__("Start Repair"), () => {
					frappe.model.open_mapped_doc({
						method: "repairs.api.start_repair",
						frm: frm,
						run_link_triggers: true
					});
				});
				repair_btn.addClass('btn-primary');
			};

			if (frm.doc.status == "Repairing") {
				var repair_btn = frm.add_custom_button(__("Finish Repair"), () => {
					var d = new frappe.ui.Dialog({
						title: __("Repair Results"),
						fields: [
							{
								label: __("With Items"),
								fieldname: "with_items",
								fieldtype: "Check",
								reqd: 0
							},
							{
								label: __("Enter Results"),
								fieldname: "resolution_details",
								fieldtype: "Text",
								reqd: 1
							}
						],
						primary_action: () => {
							var data = d.get_values();

							if (data.with_items) {
								frappe.model.open_mapped_doc({
									method: "repairs.api.finish_repair",
									frm: frm
								});
							}

							frappe.call({
								method: "repairs.api.complete_production_order",
								args: { doc: frm.doc.name },
								callback: (r) => {
									if (!r.exc) {
										frm.set_value("status", "To Deliver");
										frm.set_value("resolved_by", frappe.session.user);
										frm.set_value("resolution_date", frappe.datetime.now_datetime());
										frm.set_value("resolution_details", data.resolution_details);
										frm.save();

										d.hide();
									}
								}
							})
						},
						primary_action_label: __("Finish")
					});
					d.show();
				});
				repair_btn.addClass('btn-primary');
			};


			if (!in_list(["To Receive", "Closed", "Completed"], frm.doc.status)) {
				frm.add_custom_button(__("Delivery"), () => {
					frappe.model.open_mapped_doc({
						method: "repairs.api.make_delivery_note",
						frm: frm,
						run_link_triggers: true
					});
				}, __("Make"));
			};
		}
	},
});
