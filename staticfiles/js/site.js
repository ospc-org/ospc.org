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
