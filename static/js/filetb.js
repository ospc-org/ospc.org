// taxbrain.js

//
//  Input page
//

// sidebar - scrollspy
$('body').scrollspy({
  target: '.inputs-sidebar'
});

// Scroll to taxbrain form input areas, instead of jumping
$('.inputs-form a, .btn-explore').click(function(event) {
  if ($(this).attr('id') === 'current-year-link') {
    return;
  }
  // ensure link is indeed a hash link on current page <<-- Zach's stuff
  if (this.host == location.host && this.pathname == location.pathname) {
    event.preventDefault();
    var target = this.hash;
    if (this.href != '#') {
      $('body, html').animate({
        scrollTop: $(target).offset().top
      }, 700);
    }
  }

});

//
//  Results page
//

// Select behavior for dropdowns
$(".dropdown-select .dropdown-menu li a").click(function(){
  selection = $(this);
  dropdown_label = $(this).parents('.dropdown-select').find('.dropdown-toggle')
  dropdown_label.html(selection.text() + ' <span class="caret"></span>');
});

// Switch behavior for dropdowns
$(".data-switch .dropdown-menu li a").click(function(){
  switch_key = $(this).text().trim();

  /*
  //Without fade-out-in
  $( ".data-switchable" ).each(function(){
    $this = $(this)
    switch_value = $this.data("switch-options")[switch_key]
    $this.text(switch_value)
  })
  */

  // With fade-out-in
  $('.data-switchable').fadeOut('fast',function(){
    $this = $(this)
    switch_value = $this.data("switch-options")[switch_key]
    $this.text(switch_value).fadeIn('fast');
  });

});

$('input[name="growth_choice"]').click(function () {
  if ($(this).val() === 'factor_target') {
    $('#id_factor_adjustment').val('');
  } else {
    $('#id_factor_target').val('');
  }
});

$('#id_factor_adjustment, #id_factor_target').focus(function() {
  if ($(this).attr('id') === 'id_factor_target') {
    $('input[type="radio"][value="factor_target"]').click();
  } else {
    $('input[type="radio"][value="factor_adjustment"]').click();
  }
});

var currentYear = $('#start-year-select').val();
$('#start-year-select').change(function(e) {
  $('#current-year-link').attr('href', '/taxbrain/file/?start_year=' + $(this).val() + '&data_source=' + $('#data-source-select').val());
  $('#current-year-modal').modal('show');
});

$('#current-year-modal').on('hide.bs.modal', function (e) {
  $('#start-year-select option').removeAttr("selected");
  $('#start-year-select option[value="' + currentYear + '"]').attr("selected", "selected");
});

var dataSource = $('#data-source-select').val();
$('#data-source-select').change(function(e) {
    $('#data-source-link').attr('href', '/taxbrain/file/?start_year=' + $('#start-year-select').val() + '&data_source=' + $(this).val());
    $('#data-source-modal').modal('show');
});

$('#data-choice-modal').on('hide.bs.modal', function (e) {
  $('#data-source option').removeAttr("selected");
  $('#data-source option[value="' + dataSource + '"]').attr("selected", "selected");
});
