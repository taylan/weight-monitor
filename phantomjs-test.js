console.log('a');
var page = require('webpage').create();
console.log('b');
page.open('http://github.com/', function () {
    page.render('github.png');
    console.log('c');
    phantom.exit();
});
console.log('d');