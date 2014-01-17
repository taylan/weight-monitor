$(document).ready(function(){
    $('#input-date').pickadate({
        format: 'yyyy-mm-dd',
        formatSubmit: 'yyyy-mm-dd',
        firstDay: 1,
        clear: false
    });

    $("#weight-form").submit(function(e){
        e.preventDefault();
        $.post($(this).attr('action'), $(this).serialize())
            .done(function(data){
                console.log('save done', data)
            });
    });
});