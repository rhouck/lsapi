$(function() {
  $('div.select-date input').datepicker();

  $('div.flexibility-slider').slider({
    range: true,
    min: -3,
    max: 3,
    values: [ -1, 1 ],
    slide: function( event, ui ) {
      $(".slide-value.min").html(ui.values[0]);
      $(".slide-value.max").html(ui.values[1]);
    }
  });

  $('.slide-value.min').html($("div.flexibility-slider").slider("values", 0));
  $('.slide-value.max').html($("div.flexibility-slider").slider("values", 1));

  $('.hint').tooltip();

  $('.select-options .dropdown-menu').on('click', function(e) {
    e.stopPropagation();
  });

  $('.select-options .dropdown-menu .btn-group a').on('click', function(e){
    e.preventDefault();
    $this = $(this);
    $this.parent().find('.active').removeClass('active');
    $this.addClass('active');
  });

  $('.select-options .dropdown-menu label, .select-options .dropdown-menu input:radio').on('click', function(){
    $this = $(this);
    $parent = $this.parents('.nav-pills');
    $parent.find('.active').removeClass('active').end().find('.checked').removeClass('checked');
    $this.closest('li').addClass('active').find('.f-radio').addClass('checked');
  });

});
