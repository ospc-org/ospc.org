// site.js

// tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip();
});

$(document).ready(function(){
	var urlToShare = window.location.href.indexOf('http://localhost:8000') > -1 ? 'http://www.ospc.org/taxbrain' :window.location.href;
	new ShareButton({
		title: 'TaxBrain Results',
		description: 'This is an output from OSPC TaxBrains, a tax simulation: ' + urlToShare,
		url: urlToShare,
		networks: {
			email: {
			  enabled: false
			},
			pinterest: {
			  enabled: false
			},
		    reddit: {
		      enabled: false
		    },
		    linkedin: {
		      enabled: false
		    },
		    whatsapp: {
		      enabled: false
		    }
		}
	});
});
