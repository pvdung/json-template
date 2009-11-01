#!/usr/bin/python -S
"""
makedocs.py
"""

__author__ = 'Andy Chu'


import glob
import os
import re
import shutil
import sys
import subprocess

if __name__ == '__main__':
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import jsontemplate
from pan.core import json


# TDOO: don't hotlink it
_PRETTYPRINT_BASE = 'http://google-code-prettify.googlecode.com/svn/trunk/src/'

TOC_TEMPLATE = """
{.repeated section headings}
  <a href="#{target}">{name}</a><br>
{.end}
"""

TEST_CASE_INDEX_HTML_TEMPLATE = """
{.repeated section @}
  {@|plain-url}<br>
{.end}
"""

_HEADING_RE = re.compile(
  '<a name="(?P<target>[^"]+)"><h3>(?P<name>[^<]+)</h3></a>')

def MakeToc(blog_template):
  """
  """
  headings = []
  for match in _HEADING_RE.finditer(blog_template):
    headings.append(
        dict(target=match.group('target'), name=match.group('name')))

  print headings
  toc = jsontemplate.expand(TOC_TEMPLATE, {'headings': headings})
  print toc
  return toc


def BlogPosts(directory):
  assert directory.endswith('/')

  posts = []
  for filename in glob.glob(directory + '*.html.jsont'):
    title = filename[len(directory):-len('.html.jsont')].replace('-', ' ')
    outfilename = filename[:-len('.jsont')]

    blog_template = open(filename).read()

    dictionary = {}
    if 'Introducing' in title:
      dictionary['example1'] = open(
          'test-cases/testTableExample-01.html').read()

    if 'Minimalism' in title:
      dictionary['table-of-contents'] = MakeToc(blog_template)

    body = jsontemplate.FromString(blog_template).expand(dictionary)

    pretty_print = 'Minimalism' in title

    posts.append(dict(
        filename=filename, title=title, body=body, outfilename=outfilename,
        pretty_print=pretty_print))
  return posts


def PythonExamples(directory):
  assert directory.endswith('/')

  examples = []
  for path in glob.glob(directory + '*.py'):
    filename = os.path.basename(path)
    title = filename
    outfilename = 'doc/' + filename + '.html'

    RAW_BASE = 'http://json-template.googlecode.com/svn/trunk/python/examples/'
    LIVE_BASE = 'http://www.chubot.org/json-template/cgi-bin/examples/'

    dictionary = {
        'code': open(path).read(),
        'live': LIVE_BASE + filename + '/',  # Important trailing slash!
        'raw': RAW_BASE + filename,
        }

    body = jsontemplate.FromFile(
        open('doc/python-examples.jsont')).expand(dictionary)

    examples.append(dict(
        filename=filename, title=title, body=body, outfilename=outfilename,
        pretty_print=True))
  return examples


def ExpandHtmlShell(title, body, pretty_print=False):
  dictionary = {
      'title': title,
      'body': body,
      }

  if 'Minimalism' in title:
    dictionary['img-right'] = {
        'src': 'thagomizer.jpg',
        'href': 'http://en.wikipedia.org/wiki/Thagomizer',
        }

  # Pretty print
  if pretty_print:
    dictionary['include-js'] = [_PRETTYPRINT_BASE + 'prettify.js']
    dictionary['include-css'] = [_PRETTYPRINT_BASE + 'prettify.css']
    dictionary['onload-js'] = 'prettyPrint();'
  
  # For now, every page generated by this script is under the same analytics
  # account
  dictionary['google-analytics-id'] = 'UA-7815217-2'

  return jsontemplate.FromFile(
      open('doc/html.jsont')).expand(dictionary)


def MakeIndexHtml(directory):
  files = os.listdir(directory)
  files.sort()
  html = jsontemplate.expand(TEST_CASE_INDEX_HTML_TEMPLATE, files)
  open(directory + 'index.html', 'w').write(html)


def main(argv):

  # For now, leave off '-l' 'documentation', 
  argv = ['python', 'jsontemplate_test.py', '-d', 'test-cases']
  subprocess.call(argv)

  argv = ['python', 'jsontemplate_test.py', '-b', 'browser-tests']
  subprocess.call(argv)

  MakeIndexHtml('test-cases/')

  shutil.copy('test-cases/testTableExample-01.js.html', 'doc/')

  for post in BlogPosts('doc/'):

    body = ExpandHtmlShell(
        post['title'], post['body'], pretty_print=post['pretty_print'])

    open(post['outfilename'], 'w').write(body)


  for example in PythonExamples('python/examples/'):

    body = ExpandHtmlShell(
        example['title'], example['body'], pretty_print=True)

    open(example['outfilename'], 'w').write(body)


  # Required epydoc to be installed
  # Don't show private variables, and don't assume the docstrings have epydoc
  # markup.
  argv = [
      'epydoc', 'python/jsontemplate/_jsontemplate.py', '--html', '-v',
      '--docformat=plaintext', '--no-private', '--include-log', '--no-frames',
      '--name', 'JSON Template',
      '-o', 'epydoc']
  subprocess.call(argv)

  print 'Docs generated in epydoc/ and test-cases/ -- now rsync it'


if __name__ == '__main__':
  sys.exit(main(sys.argv))
