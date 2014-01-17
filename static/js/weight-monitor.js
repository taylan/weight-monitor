function saveWeight(u, d) {
    $.post(u, d)
        .done(function (data) {
            console.log('save done', data)
        });
}

$(document).ready(function () {
    $('#input-date').pickadate({
        format: 'yyyy-mm-dd',
        formatSubmit: 'yyyy-mm-dd',
        firstDay: 1,
        clear: false
    });

    $("#weight-form").submit(function (e) {
        e.preventDefault();
        saveWeight($(this).attr('action'), $(this).serialize());
    });

    $(".weight-table .weight-value").editable({
        url: '/save',
        ajaxOptions: {
            type: 'post',
            dataType: 'json'
        },
        escape: false,
        defaultValue: 0,
        showbuttons: false,
        onblur: 'submit'
    });
});