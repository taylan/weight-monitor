$(document).ready(function(){
    $('#input-date').pickadate({
        format: 'yyyy-mm-dd',
        formatSubmit: 'yyyy-mm-dd',
        firstDay: 1,
        clear: false
    });
});