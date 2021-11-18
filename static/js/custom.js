function modalOpen(){
    jQuery('[data-toggle="modal"]').on('touchstart click',function (e) {
        console.log('open here');
        e.preventDefault();
        var modalTarget = jQuery(this).data('target');
        jQuery(modalTarget).addClass('show').siblings().removeClass('show');
        $('body').addClass('modal-open');
        $('body').append('<div class="modal-backdrop fade show"></div>');
    });
    $('[data-dismiss="modal"]').on('touchstart click', function(){
        console.log('open here');
        $('.modal').removeClass('show');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();
    });
    $(document).on('touchstart click','.modal', function(e){
        console.log('open here');
        var closearea = jQuery(".modal-content");
        if (closearea.has(e.target).length === 0) {
            $('.modal').removeClass('show');
            $('body').removeClass('modal-open');
            $('.modal-backdrop').remove();
        }
    });
}


function suggestionCheck() {
    $( ".suggestion-list .suggestion-item label" ).on( "click", function() {
        $('.suggestion-list .suggestion-item label').removeClass('active');
        $(this).addClass('active');
    });
}

function scrollToTarget() {
    jQuery(document).on('click', '.scroll-target', function(event) {
        event.preventDefault();
        var target = "#" + this.getAttribute('data-target');
        jQuery('html, body').animate({
            scrollTop: jQuery(target).offset().top
        }, 1000);
    });
}

