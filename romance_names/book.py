import re
from bs4 import BeautifulSoup


def div_linebox_published(tag):
  return tag.name == 'div' and re.search('^published', tag.text)


class Book(object):

  def __init__(self, series_name, title, href, html_content):
    self.series_name = series_name
    self.title = title
    self.href = href

    soup = BeautifulSoup(html_content, "html5lib")

    self.publication_year = re.sub('published ', '', soup.find(div_linebox_published).text)

    self.synopsis = soup.find_all('span', class_='synopsis')[0].text

    # remove tabs and newlines
    self.synopsis = re.sub("\t", " ", self.synopsis)
    self.synopsis = re.sub("\n", " ", self.synopsis)

  def to_tsv(self):
    return "\t".join((self.series_name, self.title, self.href, self.publication_year, self.synopsis))
