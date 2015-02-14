/*
 * Module dependencies
 */
var express = require('express')
  , stylus = require('stylus')
  , nib = require('nib')
  , fs = require("fs")
  , url = require('url')
  , Parse = require('parse').Parse;


var app = express()
function compile(str, path) {
  return stylus(str)
    .set('filename', path)
    .use(nib())
}
app.set('views', __dirname + '/views')
app.set('view engine', 'jade')
app.use(express.logger('dev'))
app.use(stylus.middleware(
  { src: __dirname + '/public'
  , compile: compile
  }
))
app.use(express.static(__dirname + '/public'))

app.engine('html', require('ejs').renderFile);

app.use(express.basicAuth('hamet', 'h7R56fY6'));

app.get('/', function (req, res) {
  res.render('index.html')
})

/*
 Loads the actual graph for the query that we place in the overall view
 and calls my query parsing API so this is the individual query handler.
 */
app.get('/part', function (req, res) {
  var url_parts = url.parse(req.url, true);
  var query = url_parts.query;
  var s=query['s']
  res.render('part.html',
  { sentence : s }
  )
})

app.get('/test', function (req, res) {
  var url_parts = url.parse(req.url, true);
  var query = url_parts.query;
  var s=query['s']
  res.render('test.html',
  { query : s }
  )
})

app.get('/test2', function (req, res) {
  res.render('test2.html',
  { title : 'Home' }
  )
})

// API to recognize organic natural language queries against the database with an expanding set of sentence parse comprehension
app.get('/query', function (req, res) {
  var url_parts = url.parse(req.url, true);
  var query = url_parts.query;
  var sentence=query['s']
  console.log(sentence) 
  var spawn = require('child_process').spawn
  var python    = spawn('python', ['processQuery.py', sentence]);
  res.writeHead(200, {'content-type':'text/html'});
  python.stdout.on('data', function (data) {
    res.write(data);
  });
  python.stderr.on('data', function (data) {
    console.log('stderr: ' + data);
  });
  python.on('close', function (code) {
    res.end();
  });
})

// API to recognize a set of fixed natural language queries that have known database schema lookups
app.get('/query2', function (req, res) {
  var url_parts = url.parse(req.url, true);
  var query = url_parts.query;
  var sentence=query['s']
  console.log(sentence)
  var spawn = require('child_process').spawn
  var python    = spawn('python', ['fixedQuery.py', sentence]);
  res.writeHead(200, {'content-type':'text/html'});
  python.stdout.on('data', function (data) {
    res.write(data);
  });
  python.stderr.on('data', function (data) {
    console.log('stderr: ' + data);
  });
  python.on('close', function (code) {
    res.end();
  });
})



//});
app.listen(3000)




