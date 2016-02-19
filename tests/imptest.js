casper.test.begin('Test that all routes return 200', function(test) {
    casper.start('http://localhost:8888/', function() {
        test.assertHttpStatus(200, 'The root page should load');
    });

    casper.run(function() {
        test.done();
    });
});
