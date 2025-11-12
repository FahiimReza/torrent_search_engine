from flask import Flask, render_template, request, jsonify
import requests
import requests.exceptions
import re
import time
from urllib.parse import quote, urlparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from bs4 import BeautifulSoup
import hashlib
import os
from datetime import datetime, timedelta
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache configuration
cache = {}
cache_timeout = 300  # 5 minutes

# Tor SOCKS proxy configuration (if Tor is running locally)
TOR_SOCKS_PROXY = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}

class TorrentSearchEngine:
    def __init__(self):
        self.sources = [
            '1337x',
            'thepiratebay',
            'yts',
            'eztv',
            'torlock',
            'limetorrents',
            'rarbg',
            'nyaa',
            'zooqle',
            'btdb',
            'glodls',
            'magnetdl',
            'torrentfunk',
            'idope',
            'torrentgalaxy',
            'yourbittorrent',
            'bitsearch',
            'sumotorrent'
        ]
        self.onion_sources = [
            'thepiratebay_onion',
            '1337x_onion',
            'rarbg_onion'
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Configure session timeout
        self.session.timeout = 15
        
        # Configure retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_cache_key(self, query, source=None):
        return f"{query}_{source}_{datetime.now().strftime('%Y%m%d%H%M')}"
    
    def is_cached(self, cache_key):
        if cache_key in cache:
            cached_time, data = cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=cache_timeout):
                return data
            else:
                del cache[cache_key]
        return None
    
    def set_cache(self, cache_key, data):
        cache[cache_key] = (datetime.now(), data)
    
    def search_1337x(self, query):
        try:
            cache_key = self.get_cache_key(query, '1337x')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://1337x.to/search/{quote(query)}/1/"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[0].find('a')
                        if name_link and name_link.get('href'):
                            name = name_link.text.strip()
                            detail_url = "https://1337x.to" + name_link['href']
                            
                            # Get detailed info
                            detail_response = self.session.get(detail_url, timeout=10)
                            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            # Try to find seeds, peers, and size from detail page
                            info_rows = detail_soup.find_all('div', class_='row')
                            for info_row in info_rows:
                                if 'Seeds:' in info_row.text:
                                    seeds = int(re.search(r'Seeds:\s*(\d+)', info_row.text).group(1))
                                elif 'Peers:' in info_row.text:
                                    peers = int(re.search(r'Peers:\s*(\d+)', info_row.text).group(1))
                                elif 'Total size:' in info_row.text:
                                    size = re.search(r'Total size:\s*([\d.]+\s*[A-Z]+)', info_row.text).group(1)
                            
                            magnet_link = None
                            magnet_links = detail_soup.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': '1337x',
                                'magnet': magnet_link,
                                'url': detail_url
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching 1337x: {str(e)}")
            return []
    
    def search_thepiratebay(self, query):
        try:
            cache_key = self.get_cache_key(query, 'thepiratebay')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://thepiratebay.org/search/{quote(query)}/0/99/0"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', id='searchResult')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        name_link = cols[1].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[2].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[3].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[4].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'The Pirate Bay',
                                'magnet': magnet_link,
                                'url': f"https://thepiratebay.org{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching The Pirate Bay: {str(e)}")
            return []
    
    def search_yts(self, query):
        try:
            cache_key = self.get_cache_key(query, 'yts')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://yts.mx/api/v2/list_movies.json?query_term={quote(query)}"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            torrents = []
            if data.get('status') == 'ok' and data.get('data', {}).get('movies'):
                for movie in data['data']['movies'][:20]:  # Limit to 20 results
                    for torrent in movie.get('torrents', []):
                        torrents.append({
                            'name': f"{movie['title']} ({movie['year']}) - {torrent['quality']}",
                            'seeds': torrent.get('seeds', 0),
                            'peers': torrent.get('peers', 0),
                            'size': torrent.get('size', 'Unknown'),
                            'source': 'YTS',
                            'magnet': torrent.get('url'),
                            'url': f"https://yts.mx/movie/{movie['id']}-{movie['slug']}"
                        })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching YTS: {str(e)}")
            return []
    
    def search_eztv(self, query):
        try:
            cache_key = self.get_cache_key(query, 'eztv')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://eztv.re/search/{quote(query)}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', class_='forum_header_border')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        name_link = cols[1].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            # Get magnet link
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            # Get size from the name or elsewhere
                            size = "Unknown"
                            size_match = re.search(r'\(([\d.]+\s*[A-Z]+)\)', name)
                            if size_match:
                                size = size_match.group(1)
                            
                            torrents.append({
                                'name': name,
                                'seeds': 0,  # EZTV doesn't show seeds/peers
                                'peers': 0,
                                'size': size,
                                'source': 'EZTV',
                                'magnet': magnet_link,
                                'url': f"https://eztv.re{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching EZTV: {str(e)}")
            return []
    
    def search_torlock(self, query):
        try:
            cache_key = self.get_cache_key(query, 'torlock')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://www.torlock2.com/all/torrents/{quote(query)}.html"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[0].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[2].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[1].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'TorLock',
                                'magnet': magnet_link,
                                'url': f"https://www.torlock2.com{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching TorLock: {str(e)}")
            return []
    
    def search_nyaa(self, query):
        try:
            cache_key = self.get_cache_key(query, 'nyaa')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://nyaa.si/?f=0&c=0_0&q={quote(query)}&s=seeders&o=desc"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', class_='torrent-list')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[1].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[5].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[6].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[3].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = cols[2].find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'Nyaa',
                                'magnet': magnet_link,
                                'url': f"https://nyaa.si{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching Nyaa: {str(e)}")
            return []
    
    def search_zooqle(self, query):
        try:
            cache_key = self.get_cache_key(query, 'zooqle')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://zooqle.com/search?q={quote(query)}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            rows = soup.find_all('tr', class_='res')
            for row in rows[:20]:  # Limit to 20 results
                name_div = row.find('div', class_='zl')
                if name_div:
                    name_link = name_div.find('a')
                    if name_link:
                        name = name_link.text.strip()
                        
                        seeds = 0
                        peers = 0
                        size = "Unknown"
                        
                        # Get seeds and peers
                        seed_div = row.find('div', class_='progress-seed')
                        if seed_div:
                            try:
                                seeds = int(seed_div.text.strip().replace(',', ''))
                            except:
                                pass
                        
                        peer_div = row.find('div', class_='progress-leech')
                        if peer_div:
                            try:
                                peers = int(peer_div.text.strip().replace(',', ''))
                            except:
                                pass
                        
                        # Get size
                        size_span = row.find('span', class_='small')
                        if size_span:
                            size_text = size_span.text.strip()
                            size_match = re.search(r'([\d.]+\s*[A-Z]+)', size_text)
                            if size_match:
                                size = size_match.group(1)
                        
                        magnet_link = None
                        magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                        if magnet_links:
                            magnet_link = magnet_links[0]['href']
                        
                        torrents.append({
                            'name': name,
                            'seeds': seeds,
                            'peers': peers,
                            'size': size,
                            'source': 'Zooqle',
                            'magnet': magnet_link,
                            'url': f"https://zooqle.com{name_link['href']}" if name_link.get('href') else None
                        })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching Zooqle: {str(e)}")
            return []
    
    def search_thepiratebay_onion(self, query):
        try:
            cache_key = self.get_cache_key(query, 'thepiratebay_onion')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            # Note: This requires Tor to be running locally
            session = requests.Session()
            session.proxies.update(TOR_SOCKS_PROXY)
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            url = f"http://piratebayo3klnzokct3wt5yyxb2vpebbuyjl7m623iaxmqhsd52coid.onion/search/{quote(query)}/0/99/0"
            response = session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', id='searchResult')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        name_link = cols[1].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[2].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[3].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[4].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'The Pirate Bay (Onion)',
                                'magnet': magnet_link,
                                'url': f"http://piratebayo3klnzokct3wt5yyxb2vpebbuyjl7m623iaxmqhsd52coid.onion{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching The Pirate Bay (Onion): {str(e)}")
            return []
    
    def search_btdb(self, query):
        try:
            cache_key = self.get_cache_key(query, 'btdb')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://btdb.to/q/{quote(query)}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            cards = soup.find_all('div', class_='card')
            for card in cards[:20]:  # Limit to 20 results
                title_elem = card.find('h5', class_='card-title')
                if title_elem:
                    name = title_elem.text.strip()
                    
                    seeds = 0
                    peers = 0
                    size = "Unknown"
                    
                    # Get stats
                    stats = card.find_all('span', class_='badge')
                    if len(stats) >= 2:
                        try:
                            seeds = int(stats[0].text.strip())
                            peers = int(stats[1].text.strip())
                        except:
                            pass
                    
                    # Get size
                    size_elem = card.find('span', text=re.compile(r'[0-9.]+\s*[A-Z]+'))
                    if size_elem:
                        size = size_elem.text.strip()
                    
                    magnet_link = None
                    magnet_links = card.find_all('a', href=re.compile(r'magnet:'))
                    if magnet_links:
                        magnet_link = magnet_links[0]['href']
                    
                    torrents.append({
                        'name': name,
                        'seeds': seeds,
                        'peers': peers,
                        'size': size,
                        'source': 'BTDB',
                        'magnet': magnet_link,
                        'url': f"https://btdb.to{title_elem.find('a')['href']}" if title_elem.find('a') else None
                    })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching BTDB: {str(e)}")
            return []
    
    def search_glodls(self, query):
        try:
            cache_key = self.get_cache_key(query, 'glodls')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://glodls.to/search_results.php?search={quote(query)}&cat=0"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[0].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[2].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[3].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[1].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'GloDLS',
                                'magnet': magnet_link,
                                'url': f"https://glodls.to{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching GloDLS: {str(e)}")
            return []
    
    def search_magnetdl(self, query):
        try:
            cache_key = self.get_cache_key(query, 'magnetdl')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://www.magnetdl.com/{quote(query)}/se/desc/1/"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[1].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[3].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[4].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[2].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'MagnetDL',
                                'magnet': magnet_link,
                                'url': f"https://www.magnetdl.com{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching MagnetDL: {str(e)}")
            return []
    
    def search_torrentfunk(self, query):
        try:
            cache_key = self.get_cache_key(query, 'torrentfunk')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://www.torrentfunk.com/torrent/{quote(query)}.html"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[0].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[2].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[1].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'TorrentFunk',
                                'magnet': magnet_link,
                                'url': f"https://www.torrentfunk.com{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching TorrentFunk: {str(e)}")
            return []
    
    def search_idope(self, query):
        try:
            cache_key = self.get_cache_key(query, 'idope')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://idope.se/search/{quote(query)}/"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        name_link = cols[0].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            size = "Unknown"
                            
                            # iDope shows seeds in a different format
                            seed_text = cols[1].text.strip()
                            seed_match = re.search(r'(\d+)', seed_text)
                            if seed_match:
                                seeds = int(seed_match.group(1))
                            
                            size = cols[2].text.strip()
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': 0,  # iDope doesn't show peers
                                'size': size,
                                'source': 'iDope',
                                'magnet': magnet_link,
                                'url': f"https://idope.se{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching iDope: {str(e)}")
            return []
    
    def search_torrentgalaxy(self, query):
        try:
            cache_key = self.get_cache_key(query, 'torrentgalaxy')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://torrentgalaxy.to/torrents.php?search={quote(query)}&lang=0"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', class_='tgxtable')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[0].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[5].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[6].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[3].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'TorrentGalaxy',
                                'magnet': magnet_link,
                                'url': f"https://torrentgalaxy.to{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching TorrentGalaxy: {str(e)}")
            return []
    
    def search_yourbittorrent(self, query):
        try:
            cache_key = self.get_cache_key(query, 'yourbittorrent')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://yourbittorrent.com/?q={quote(query)}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[1].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[4].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[5].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[2].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'YourBittorrent',
                                'magnet': magnet_link,
                                'url': f"https://yourbittorrent.com{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching YourBittorrent: {str(e)}")
            return []
    
    def search_bitsearch(self, query):
        try:
            cache_key = self.get_cache_key(query, 'bitsearch')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://bitsearch.to/search?q={quote(query)}&category=all"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[0].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[2].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[3].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[1].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'BitSearch',
                                'magnet': magnet_link,
                                'url': f"https://bitsearch.to{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching BitSearch: {str(e)}")
            return []
    
    def search_sumotorrent(self, query):
        try:
            cache_key = self.get_cache_key(query, 'sumotorrent')
            cached_result = self.is_cached(cache_key)
            if cached_result:
                return cached_result
            
            url = f"https://www.sumotorrent.sx/search/{quote(query)}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            torrents = []
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Limit to 20 results
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        name_link = cols[0].find('a')
                        if name_link:
                            name = name_link.text.strip()
                            
                            seeds = 0
                            peers = 0
                            size = "Unknown"
                            
                            try:
                                seeds = int(cols[2].text.strip())
                            except:
                                pass
                            
                            try:
                                peers = int(cols[3].text.strip())
                            except:
                                pass
                            
                            try:
                                size = cols[1].text.strip()
                            except:
                                pass
                            
                            magnet_link = None
                            magnet_links = row.find_all('a', href=re.compile(r'magnet:'))
                            if magnet_links:
                                magnet_link = magnet_links[0]['href']
                            
                            torrents.append({
                                'name': name,
                                'seeds': seeds,
                                'peers': peers,
                                'size': size,
                                'source': 'SumoTorrent',
                                'magnet': magnet_link,
                                'url': f"https://www.sumotorrent.sx{name_link['href']}" if name_link.get('href') else None
                            })
            
            self.set_cache(cache_key, torrents)
            return torrents
            
        except Exception as e:
            logger.error(f"Error searching SumoTorrent: {str(e)}")
            return []
    
    def search_all_sources(self, query, include_onion=False):
        all_results = []
        
        # Regular sources
        regular_sources = {
            '1337x': self.search_1337x,
            'thepiratebay': self.search_thepiratebay,
            'yts': self.search_yts,
            'eztv': self.search_eztv,
            'torlock': self.search_torlock,
            'nyaa': self.search_nyaa,
            'zooqle': self.search_zooqle,
            'btdb': self.search_btdb,
            'glodls': self.search_glodls,
            'magnetdl': self.search_magnetdl,
            'torrentfunk': self.search_torrentfunk,
            'idope': self.search_idope,
            'torrentgalaxy': self.search_torrentgalaxy,
            'yourbittorrent': self.search_yourbittorrent,
            'bitsearch': self.search_bitsearch,
            'sumotorrent': self.search_sumotorrent
        }
        
        # Onion sources
        onion_sources = {
            'thepiratebay_onion': self.search_thepiratebay_onion
        }
        
        sources_to_search = regular_sources.copy()
        if include_onion:
            sources_to_search.update(onion_sources)
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            future_to_source = {
                executor.submit(search_func, query): source_name
                for source_name, search_func in sources_to_search.items()
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    results = future.result(timeout=20)
                    all_results.extend(results)
                    logger.info(f"Got {len(results)} results from {source}")
                except Exception as e:
                    logger.error(f"Error in {source}: {str(e)}")
        
        # Remove duplicates based on name similarity
        unique_results = []
        seen_names = set()
        
        for torrent in all_results:
            # Create a normalized name for comparison
            normalized_name = re.sub(r'[^a-zA-Z0-9]', '', torrent['name'].lower())
            if normalized_name not in seen_names:
                seen_names.add(normalized_name)
                unique_results.append(torrent)
        
        # Sort by seeds (descending)
        unique_results.sort(key=lambda x: x['seeds'], reverse=True)
        return unique_results[:100]  # Limit to 100 results total

# Initialize search engine
search_engine = TorrentSearchEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    include_onion = request.args.get('onion', 'false').lower() == 'true'
    
    if not query:
        return jsonify({'error': 'Query parameter is required'})
    
    try:
        results = search_engine.search_all_sources(query, include_onion)
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'sources_searched': len(search_engine.sources) + (len(search_engine.onion_sources) if include_onion else 0)
        })
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed. Please try again.'})

@app.route('/api/sources')
def get_sources():
    return jsonify({
        'regular_sources': search_engine.sources,
        'onion_sources': search_engine.onion_sources
    })

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'cache_size': len(cache),
        'cache_timeout': cache_timeout,
        'total_regular_sources': len(search_engine.sources),
        'total_onion_sources': len(search_engine.onion_sources)
    })

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    global cache
    cache.clear()
    return jsonify({'message': 'Cache cleared successfully'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)