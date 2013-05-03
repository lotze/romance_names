#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import mechanize
import re
import os
from urlparse import urljoin
import sys
import time

sys.path.append('romance_names')
from series import Series
from book_link import BookLink
from book import Book

import logging

logging.basicConfig(level=logging.DEBUG)


def html_line_to_series(base_href, line):
  """ Gets the name and href for the series page, if found in this line
  """
  matches = re.search('href="([^"]+)">([^>]+)<', line)
  if (matches):
    href = matches.group(1)
    name = matches.group(2)
    return Series(name, urljoin(base_href, href))
  else:
    return Series(None, None)


def includes_harlequin(string):
  """ Returns the search result, if the string includes 'harlequin' (case-insensitive)
  """
  return re.search('harlequin', string.lower())


def html_line_to_book(base_href, line):
  """ Gets the book href and title from the series page html
  """
  matches = re.search('href="../author/[^"]+">[^<]+</a></td><td><a href="([^"]+)">([^<]+)</a>', line)
  if (matches):
    book_href = matches.group(1)
    book_title = matches.group(2)
    return BookLink(book_title, urljoin(base_href, book_href))
  else:
    return BookLink(None, None)


def parse_book_links(base_href, series_list_html):
  """ Returns a list of BookLink objects parsed from a series' html
  """
  return [html_line_to_book(base_href, line) for line in series_list_html.split("\n")]

series_list_href = 'http://www.fictiondb.com/series/publisher-series.htm'
br = mechanize.Browser()

# Get the main page
main_page_file = 'data/html/main_page.html'
if os.path.exists(main_page_file):
  logging.info('Reading main page data from cached html file')
  with open(main_page_file) as f:
    main_page_html = f.read()
else:
  logging.info('Reading main page data from the web')
  r = br.open(series_list_href)
  main_page_html = r.read()
  with open(main_page_file, 'w') as f:
    f.write(main_page_html)

lines = main_page_html.split("\n")
lines_with_harlequin = filter(includes_harlequin, lines)
series_data = [html_line_to_series(series_list_href, line) for line in lines_with_harlequin]

logging.info("Parsed %d Harlequin series from around %d total series" % (len(series_data), len(lines)))

output_file = 'data/books.tsv'
with open(output_file, 'w') as f:
  f.write("\t".join(('series_name', 'title', 'href', 'publication_year', 'synopsis')))
  f.write("\n")

for series in series_data:
  if series.name is None:
    continue
  logging.info("Examining series %s at %s" % (series.name, series.href))

  series_page_file = 'data/html/%s.html' % re.sub(' ', '_', series.name)
  if os.path.exists(series_page_file):
    logging.info('Reading series page data from cached html file')
    with open(series_page_file) as f:
      series_page_html = f.read()
  else:
    logging.info('Reading series page data from the web')
    r = br.open(series.href)
    series_page_html = r.read()
    with open(series_page_file, 'w') as f:
      f.write(series_page_html)
    time.sleep(1)

  # get links for every book in the series
  book_links = parse_book_links(series.href, series_page_html)
  logging.info('Found %d books' % len(book_links))
  for book_link in book_links:
    # get and download the book html_line_to_series
    if book_link.title is None:
      continue
    logging.info('Examining book %s from %s' % (book_link.title, book_link.href))
    book_file = 'data/html/%s_%s.html' % (re.sub(' ', '_', series.name), re.sub(' ', '_', book_link.title))
    if os.path.exists(book_file):
      logging.info('Reading book data from cached html file')
      with open(book_file) as f:
        book_html = f.read()
    else:
      logging.info('Reading book data from the web')
      r = br.open(book_link.href)
      book_html = r.read()
      with open(book_file, 'w') as f:
        f.write(book_html)
      time.sleep(1)

    book = Book(series.name, book_link.title, book_link.href, book_html)
    with open(output_file, 'a') as f:
      f.write(book.to_tsv())
      f.write("\n")
