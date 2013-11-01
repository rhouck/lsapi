+function($){
  var dp = $.datepicker;
  var billingSection = $('.billing-info');
  billingSection.animate({height: 'toggle'}, 0);
  $('.billing-header input').click(function(){billingSection.animate({height: 'toggle'});});
  $('.range').each(
    function(i, el){
      var arr = el.innerHTML.split('-'),
          d1 = parseFloat(arr[0]),
          d2 = parseFloat(arr[1]),
          str = dp.formatDate('m/d/yy', new Date(d1))+' - '+dp.formatDate('m/d/yy', new Date(d2));
      el.innerHTML=str;
    });
  $('.date').each(
    function(i,el){
      el.innerHTML=dp.formatDate('m/d/yy', new Date(parseFloat(el.innerHTML)));});

  $('.nav-tabs a').click(function (e) {e.preventDefault(); $(this).tab('show');});

}(window.jQuery);