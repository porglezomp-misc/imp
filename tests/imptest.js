casper.test.begin('Test the critical paths of the application from a fresh start', 52, function(test) {
    function assertNavBar() {
        test.assertSelectorHasText('nav a[href="/"]', 'Home',
                                   'The home button should exist');
        test.assertSelectorHasText('nav a[href="/tags"]', 'Tags',
                                   'The tags button should exist');
        test.assertSelectorHasText('nav a[href="/categories"]', 'Categories',
                                   'The categories button should exist');
    }

    casper.on('remote.message', function(msg) {
        this.echo('Remote log: ' + msg);
    });

    casper.on('page.error', function(msg) {
        this.warn(msg);
    });

    var x = require('casper').selectXPath;

    casper.start('http://localhost:8888/', function() {
        test.assertHttpStatus(200, 'The root page should load successfully');
        assertNavBar();
        test.assertElementCount('main li a', 0,
                                "There shouldn't be any images yet");
        test.assertSelectorHasText('a[href="/images/new"]', '+ New Image',
                                   'There should be a button to add a new image');
        this.clickLabel('+ New Image');
    });

    casper.waitForUrl('/images/new', function() {
        test.assertHttpStatus(200, 'The new image page should load successfully');
        test.assertExists('form[action="/images/new"]',
                          'The page should have a form to describe the image');
        this.fill('form[action="/images/new"]', {
            name: 'My Steven Universe Poster!',
            url: 'https://i.imgur.com/Cy0QxaE.jpg',
            description: 'An extremely cool poster',
        }, true);
    });

    casper.waitForUrl('/images/Cy0QxaE', function() {
        test.assertHttpStatus(200, 'The image we created should load successfully');
        test.assertTitle('My Steven Universe Poster!',
                         'The page should have the title we entered');
        test.assertSelectorHasText('h1', 'My Steven Universe Poster!',
                                   'The header should also have the title we entered');
        test.assertExists('img[src="https://i.imgur.com/Cy0QxaE.jpg"]',
                          'The image we chose should be on the page');
    });

    casper.thenOpen('http://localhost:8888/images', function() {
        test.assertHttpStatus(200, 'The image list should load successfully');
        assertNavBar();
        test.assertElementCount('main li a', 1,
                                'There should be one item in the image list');
        test.assertSelectorHasText('main li a', 'My Steven Universe Poster!',
                                   'The image we added should be in the image list');
        this.clickLabel('Tags');
    });

    casper.waitForUrl('/tags', function() {
        test.assertHttpStatus(200, 'The tags list should load successfully');
        assertNavBar();
        test.assertElementCount('main li a', 0,
                                "There shouldn't be any tags yet");
        test.assertSelectorHasText('a[href="/tags/new"]', '+ New Tag',
                                   'There should be a new tag button');
        this.clickLabel('+ New Tag');
    });

    casper.waitForUrl('/tags/new', function() {
        test.assertHttpStatus(200, 'The new tag page should load succesfully');
        test.assertExists('form[action="/tags/new"]',
                          'There should be a form to add tag data');
        this.fill('form[action="/tags/new"]', {
            name: 'Steven Universe',
        }, true);
    });

    casper.waitForUrl('/tags/Steven+Universe', function() {
        test.assertHttpStatus(200, 'The tag page should load succesfully');
        test.assertTitle('Steven Universe',
                         'The page title should be our tag name');
        test.assertSelectorHasText('h1', 'Steven Universe',
                                   'The heading should be our tag name');
        test.assertElementCount('main li a', 0,
                                "There shouldn't be any images with this tag");
        this.clickLabel('Tags');
    });

    casper.waitForUrl('/tags', function() {
        test.assertHttpStatus(200, 'The tag list should load successfully');
        test.assertElementCount('main li a', 1, 'There should be one tag');
        test.assertSelectorHasText('main li a', 'Steven Universe',
                                   'The tag link should have the name we added');
        this.clickLabel('Categories');
    });

    casper.waitForUrl('/categories', function() {
        test.assertHttpStatus(200, 'The category list should load successfully');
        assertNavBar();
        test.assertElementCount('main li a', 0,
                                "There shouldn't be any categories yet");
        test.assertExists('a[href="/categories/new"]',
                          'There should be a button to create a new category');
        this.clickLabel('+ New Category');
    });

    casper.waitForUrl('/categories/new', function() {
        test.assertHttpStatus(200, 'The new category page should load successfully');
        test.assertExists('form[action="/categories/new"]',
                          'There should be a form to create a new category');
        this.fill('form[action="/categories/new"]', {
            name: 'Character',
        }, true);
    });

    casper.waitForUrl('/categories/Character', function() {
        test.assertHttpStatus(200, 'The category should load succesfully');
        test.assertTitle('Character', 'The page be titled with the category name');
        test.assertSelectorHasText('h1', 'Character',
                                   'The heading should contain the category name');
        test.assertElementCount('main li a', 0,
                                "There shouldn't be any tags in the category yet");
        this.clickLabel('Categories');
    });

    casper.waitForUrl('/categories', function() {
        test.assertHttpStatus(200, 'The category list should still load successfully');
        test.assertElementCount('main li a', 1, 'There should be one tag now');
        test.assertSelectorHasText('main li a', 'Character',
                                   'The Character category should be in the list');
        this.clickLabel('Home');
    });

    casper.waitForUrl('/', function() {
        test.assertHttpStatus(200, 'The root page should still load successfully');
        this.clickLabel('My Steven Universe Poster!');
    });

    casper.waitForUrl('/images/Cy0QxaE', function() {
        test.assertHttpStatus(200, 'The image should load successfully');
        test.assertExists('form#newtag', 'There should be a form to create new tags');
        this.fill('form#newtag', {
            name: 'Steven Universe',
        }, true);
    });

    casper.waitForSelector('#tags li a', function() {
        test.assertElementCount('#tags li a', 1,
                                'There should be one tag on the image');
        test.assertSelectorHasText('#tags li a', 'Steven Universe',
                                   'The tag should have the correct name');
        this.clickLabel('Steven Universe');
    });

    casper.waitForUrl('/tags/Steven+Universe', function() {
        test.assertHttpStatus(200, 'The tag should load successfully');
        test.assertElementCount('main li a', 1,
                                'There should be one image in the tag');
        test.assertSelectorHasText('main li a', 'My Steven Universe Poster!',
                                  'The image link should have its title');
    });

    casper.thenOpen('http://localhost:8888/tags/new', function() {
        test.assertHttpStatus(200, 'The tag creation page should still load successfully');
        this.fill('form[action="/tags/new"]', {
            name: 'Connie',
            category: 'Character',
        }, true);
    });

    casper.waitForUrl('/tags/Connie', function() {
        test.assertHttpStatus(200, 'The tag should load successfully');
        test.assertTitle('Connie (Character)');
        var text = this.evaluate(function() {
            return document.getElementsByTagName('h1')[0].innerText;
        });
        test.assertEqual(text, 'Connie (Character)',
                         'The header should have the tag name and parenthetical category');
    });

    casper.thenOpen('http://localhost:8888/categories/Character', function() {
        test.assertHttpStatus(200, 'The category page should load successfully');
        test.assertElementCount('main li a', 1,
                                'There should be one tag in the category');
        test.assertSelectorHasText('main li a[href="/tags/Connie"]', 'Connie',
                                   'The tag link should be titled with the tag name');
    });

    casper.thenOpen('http://localhost:8888/images/Cy0QxaE', function() {
        this.fill('#newtag', {
            name: 'fan art',
        }, true);
    });

    casper.waitForSelector('#tags li:nth-child(2) a', function() {
        test.assertSelectorHasText('#tags li:nth-child(2) a', 'Fan Art',
                                   'Tags should automatically recieve title capitalization');
        this.clickLabel('Fan Art');
    });

    casper.waitForUrl('/tags/Fan+Art', function() {
        test.assertHttpStatus(200, 'The tag should load successfully');
    });

    casper.thenOpen('http://localhost:8888/tags', function() {
        test.assertElementCount('main li a', 3, 'There should be 3 tags now');
    });

    casper.thenOpen('http://localhost:8888/images/Cy0QxaE', function() {
        this.fill('#newtag', {
            name: 'character:garnet',
        }, true);
        this.fill('#newtag', {
            name: 'character:peridot',
        }, true);
        casper.waitForText('Garnet');
        casper.waitForText('Peridot');
    });

    casper.thenOpen('http://localhost:8888/tags', function() {
        test.assertElementCount('main li a', 5, 'We should have 5 tags by now');
        this.click(x('//*[normalize-space(text())="Garnet"]'));
    });

    casper.waitForUrl('/tags/Garnet', function() {
        test.assertTitle('Garnet (Character)');
        test.assertSelectorHasText('h1', 'Garnet (Character)');
    });

    casper.thenOpen('http://localhost:8888/categories/Character', function() {
        test.assertElementCount('main li a', 3,
                                'We should have 3 tags in the category');
    });

    casper.run(function() {
        test.done();
    });
});
