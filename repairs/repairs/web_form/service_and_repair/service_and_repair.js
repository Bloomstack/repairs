// Dirty hack to remap the "New" button on the portal, since
// there is no framework provision to do so
frappe.ready(function () {
	$(".page-header-actions-block a.btn-new").attr("href", "/fit_correction");
})