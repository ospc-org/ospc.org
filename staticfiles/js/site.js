// site.js

// tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip();
});

$(document).ready(function(){
	var urlToShare = window.location.href.indexOf('http://localhost:8000') > -1 ? 'http://www.ospc.org/taxbrain' :window.location.href;
	new ShareButton({
		title: 'TaxBrain Results',
		description: 'Check out my output from TaxBrain, an open-source tax policy simulator: ' + urlToShare,
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
