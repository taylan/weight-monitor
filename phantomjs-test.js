var page = require('webpage').create();
var args = require('system').args;
var sourceFile = args[1];
var destFile = args[2];
console.log(args[1], args[2]);
page.open(sourceFile, function () {
    page.render(destFile);
    phantom.exit();
});
