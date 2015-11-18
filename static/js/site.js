// site.js

// tooltips
$(function () {
  $('[data-toggle="tooltip"]').tooltip();
  $('[name="growth_choice"]').click(function () {
    if ($(this).val() === 'factor_target') {
      $('#id_factor_adjustment').val('');
    } else {
      $('#id_factor_target').val('');
    }
  });
});

$(document).ready(function(){
	var urlToShare = window.location.href.indexOf('http://localhost:8000') > -1 ? 'http://www.ospc.org/taxbrain' :window.location.href;
	new ShareButton({
		title: 'TaxBrain Results',
		description: 'This is an output from OSPC TaxBrains, a tax simulation: ' + urlToShare,
		url: urlToShare,
		networks: {
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
