// pages.js

// highlight form on focus
$('.join input').on('blur', function(){
   $(this).closest('section').removeClass('join-active');
}).on('focus', function(){
  $(this).closest('section').addClass('join-active');
});
