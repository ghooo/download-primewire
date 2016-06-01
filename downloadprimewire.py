#! /usr/bin/python

# -*- coding: utf-8 -*-
# @Author: ghooo
# @Date:   2016-05-14 08:59:58
# @Last Modified by:   ghooo
# @Last Modified time: 2016-06-01 05:53:21
import mechanize
import urllib2
import urllib
import requests
import sys
from clint.textui import progress


from bs4 import BeautifulSoup

primewire = "http://www.primewire.ag"
import cookielib

# Browser
br = mechanize.Browser()

# Cookie Jar
cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)

# Browser options
br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)

# Follows refresh 0 but not hangs on refresh > 0
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

# Want debugging messages?
# br.set_debug_http(True)
# br.set_debug_redirects(True)
# br.set_debug_responses(True)

# User-Agent (this is cheating, ok?)
br.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')]

def load_from__url(url):
	while(True):
		try:
			r = br.open(url).read()
			return r
		except:
			print "Error loading %s, will try again!" % url

def get_episode_urls(url):
	r = load_from__url(url)
	soup = BeautifulSoup(r, "html.parser")

	episodes = soup.find_all("div", {"class":"tv_episode_item"})
	episodes = [primewire + episode.find("a")['href'] for episode in episodes]

	return episodes

def get_thevideo_url(episode_url):
	r = load_from__url(episode_url)
	soup = BeautifulSoup(r, "html.parser")

	sharing_sites_tables = soup.find_all("table", {"class":"movie_version"})
	thevideo_tables = [table for table in sharing_sites_tables if "thevideo" in table.find_all("span", {"class":"version_host"})[0].text]

	url = primewire + thevideo_tables[0].find("a")['href']

	while(True):
		try:
			r = br.open(url)
			ret = br.geturl()
			break
		except:
			print "Error redirecting %s, will try again!" % url

	return ret


def get_download_link(thevideo_url):
	thevideo_versions_url = thevideo_url[:19] + "download/getversions/" + thevideo_url[19:]

	r = load_from__url(thevideo_versions_url)
	soup = BeautifulSoup(r, "html.parser")

	parts = soup.find_all("tr")[-1].find("a")['onclick'].split("'")

	semi_final_download_link = thevideo_url[:19] + "download/" + thevideo_url[19:] + "/" + parts[3] + "/" + parts[5]

	while True:
		try:
			r = load_from__url(semi_final_download_link)
			soup = BeautifulSoup(r, "html.parser")
			with open("out.html", "w") as text_file:
				text_file.write(r)
			ret = soup.find_all("div", {"class":"container main-container"})[0].find("a")['href']
			break
		except:
			pass

	return ret

def download_file(url, filename):
	r = requests.get(url, stream=True)
	with open(filename, 'wb') as f:
		total_length = int(r.headers.get('content-length'))
		for chunk in progress.bar(r.iter_content(chunk_size=1024), label=filename+": ", expected_size=(total_length/1024) + 1): 
			if chunk:
				f.write(chunk)
				f.flush()

def download_series(series_url, start=None, end=None):
	episodes = get_episode_urls(series_url)

	if start == None: start = 1
	if end == None: end = len(episodes)

	assert start <= len(episodes) and start >= 1
	assert end <= len(episodes) and end >= start

	print "Series URL: %s" % series_url
	print "Downloading from episode %d to episode %d." % (start+1, end)
	print 100*'-'

	for i in range(start-1,end):
		thevideo_url = get_thevideo_url(episodes[i])

		download_link = get_download_link(thevideo_url)

		filename = download_link.split("/")[-1]

		download_file(download_link, filename)


download_series("http://www.primewire.ag/watch-5207-Seinfeld-online-free", start=7)

