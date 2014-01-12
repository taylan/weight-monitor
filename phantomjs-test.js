var page = require('webpage').create();
var args = require('system').args;
var destFile = args[1];
console.log(args);
console.log(args[1]);
page.open('http://github.com/', function () {
    page.render(destFile);
    phantom.exit();
});
