function saveWeight(u, d, r) {
    $.post(u, d)
        .done(function(data) {
            console.log('save done', data);
            if (r) {
                window.location = '/';
            }
        });
}

$(document).ready(function() {
    $('#input-date').pickadate({
        format: 'yyyy-mm-dd',
        formatSubmit: 'yyyy-mm-dd',
        max: new Date(),
        firstDay: 1,
        clear: false
    });

    $("#weight-form").submit(function(e) {
        e.preventDefault();
        saveWeight($(this).attr('action'), $(this).serialize(), true);
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

    if ($('.weight-table').length > 0) {
        var chartData = [];
        $('.weight-table .weight-value').each(function() {
            chartData.push([$(this).data('pk').substr(2), parseFloat($(this).text())]);
        });
        chartData.reverse();
        chartData.unshift(['Date', 'Value']);

        var options = {
            title: $.trim($($('.weight-table th')[0]).text()),
            legend: { position: 'none' },
            chartArea: { right: 0, left: '12%', top: 30, width: "85%", height: '80%' }
        };

        function drawChart() {
            var data = google.visualization.arrayToDataTable(chartData, false);
            var chart = new google.visualization.LineChart(document.getElementById('chart-container'));
            chart.draw(data, options);
        }

        google.load("visualization", "1", {
            packages: ["corechart"],
            callback: drawChart
        });

        window.addEventListener('orientationchange', drawChart);
    }
});