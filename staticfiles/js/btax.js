// btax.js

// sidebar - scrollspy
$('body').scrollspy({
  target: '.inputs-sidebar'
});


asset_yr_str = ["3", "5", "7", "10", "15", "20", "25", "27_5", "39"]
radio_tags = ['gds', 'ads', 'tax']
$.each(asset_yr_str, function(index, value){

  $("input[name='btax_depr_allyr']").click(function () {
    var name_str = 'btax_depr_' + value + 'yr';
    var adjust_all_for_click = function(tag, idx){
      //var id_str = '#' + 'btax_depr_' + value + 'yr_' + value2 + '_Switch';
      bbb = $('input[name=' + name_str + ']')
      console.log(bbb);
      bbb[idx].click();
    };
    if (this.value === 'btax_depr_allyr_ads_Switch') {
      console.log('ADS');
      adjust_all_for_click('ads', 1);
    } else if(this.value === 'btax_depr_allyr_gds_Switch') {
      console.log("GDS");
      adjust_all_for_click('gds', 0);
    }else{
      console.log("Economic");
      adjust_all_for_click('tax', 2);
    }
  });
});

$('#start-year-select').change(function() {
  $('#current-year-link').attr('href', '/ccc/?start_year=' + $(this).val());
  $('#current-year-alert').removeClass('hidden');
});

$(document).ready(function(){
  $('.form-group > input.form-control').each(function() {
    input = $(this)
    value = input.val()
    value_default = input.prop('placeholder');
    value_changed = (value != '') && (value != value_default);
    group = input.closest('.form-group')
    if (value_changed) {
      group.addClass('edited');
    } else {
      input.val('');
      group.removeClass('edited');
    }
  })
})
