// site.js

// tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip();
});

$("#results-print-button").click(function(evt) {
	window.print();
});