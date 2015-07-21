// taxbrain.js

//
//  Input page
//

// sidebar - affix
taxbrain_input_form = $('.inputs-form').first();

$('.inputs-sidebar').affix({
  offset: {
    top: function(){return (taxbrain_input_form.offset().top + 30);},
    bottom: 271
  }
});

// sidebar - scrollspy
$('body').scrollspy({
  target: '.inputs-sidebar'
});

// scroll to form
$('.inputs-form a, .btn-explore').click(function (e) {
  e.preventDefault();
  var target = this.hash;
  if (this.href != '#') {
    jQuery('html, body').animate({
      scrollTop: jQuery(target).offset().top
    }, 700);
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

// Form Inputs
// only allow values to be entered if not equal to default
// if new values entered, show info about default value
$('.form-group > input.form-control').blur(function() {

  input = $(this)
  value = input.val()
  value_default = input.prop('placeholder');
  value_changed = (value != '') && (value != value_default);
  group = input.closest('.form-group')

  //console.log('bluring ' + input  + ' with value ' + value + ' with default ' +
  //  value_default + ' changed ' + value_changed )

  if (value_changed) {
    group.addClass('edited');
  } else {
    input.val(''); // show placeholder instead of value entered that = default
    group.removeClass('edited');
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