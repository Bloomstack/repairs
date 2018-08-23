frappe.listview_settings["Warranty Claim"] = {
	add_fields: ["status"],
	get_indicator: (doc) => {
		if (in_list(["Declined", "Cancelled"], doc.status)) {
			return [__(doc.status), "red", "status,=," + doc.status];
		} else if (doc.status == "Offline") {
			return [__(doc.status), "darkgrey", "status,=," + doc.status];
		} else if (in_list(["To Receive", "To Test", "To Repair", "To Deliver"], doc.status)) {
			return [__(doc.status), "orange", "status,=," + doc.status];
		} else if (in_list(["Completed", "Repairing"], doc.status)) {
			return [__(doc.status), "green", "status,=," + doc.status];
		}
	},
};