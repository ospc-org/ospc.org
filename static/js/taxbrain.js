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
  if ($(this).attr('id') === 'data-source-link') {
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

// CPI buttons
$('.form-group > label.btn-cpi').click(function (e) {
  label = $(this)
  field = label.attr('for')
  prev_value = label.hasClass('active')

  // add button-toggle functionality without hijacking click
  prev_value ? label.removeClass('active') : label.addClass('active');
  value = !prev_value

  // find the default value
  select = label.siblings('.form-control');
  placeholder = select.attr('placeholder')
  placeholder_true = placeholder == 'True'
  placeholder_false = placeholder == 'False'
  has_boolean_default = placeholder_true || placeholder_false

  // default-based logic
  if (has_boolean_default) {
    default_value = placeholder_true;
    is_default = (value == default_value);
    console.log(
    'setting CPI field ' + field  +
    ' from value ' + prev_value +
    ' to value ' + value +
    ' with default ' + default_value +
    ' is default ' + is_default )

    // only allow values to be entered if not equal to default
    // if new values entered, show info about default value
    group = label.closest('.form-group')
    if (!is_default) {
      if (value) {select.val('2');} else {select.val('3');}
      group.addClass('edited');

    } else {
      select.val('1'); // set to "Unknown"
      group.removeClass('edited');
    }

  } else {
    // we don't recognize the placeholder value
    console.log('setting CPI field with no default ' + field  +
      ' to value ' + value )

    // pass changes directly to the select
    if (value) {select.val('2');} else {select.val('3');}
  }
});

$("#tax-submit[type='reset']").click(function(){
  $('.form-group.edited').each(function(){
    $(this).removeClass("edited")
  })
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
  $('#current-year-link').attr('href', '/taxbrain/?start_year=' + $(this).val() + '&data_source=' + $('#data-source-select').val());
  $('#current-year-modal').modal('show');
});

$('#current-year-modal').on('hide.bs.modal', function (e) {
  $('#start-year-select option').removeAttr("selected");
  $('#start-year-select option[value="' + currentYear + '"]').attr("selected", "selected");
});

var dataSource = $('#data-source-select').val();
$('#data-source-select').change(function(e) {
    $('#data-source-link').attr('href', '/taxbrain/?start_year=' + $('#start-year-select').val() + '&data_source=' + $(this).val());
    $('#data-source-modal').modal('show');
});

$('#data-choice-modal').on('hide.bs.modal', function (e) {
  $('#data-source option').removeAttr("selected");
  $('#data-source option[value="' + dataSource + '"]').attr("selected", "selected");
});
