# Torrent Search Engine

A comprehensive web-based torrent search engine that aggregates results from multiple torrent sites, including support for onion sites via Tor network.

## Features

- 🔍 **Multi-source Search**: Searches across 7+ popular torrent sites simultaneously
- 🧅 **Onion Site Support**: Access torrent sites on the Tor network (requires Tor)
- 📊 **Detailed Information**: Shows seeds, peers, file size, and source for each torrent
- 🎯 **Smart Filtering**: Filter by category, size, and minimum seed count
- 🔄 **Real-time Sorting**: Sort results by seeds, size, or name
- 💾 **Caching System**: Intelligent caching for faster repeated searches
- 🌐 **Responsive Design**: Clean, modern UI that works on all devices
- ⚡ **Fast Performance**: Concurrent searching with timeout protection

## Supported Torrent Sites

### Regular Sites
- **1337x** - Popular general torrent site
- **The Pirate Bay** - One of the oldest and most well-known torrent sites
- **YTS** - Specialized in movie torrents
- **EZTV** - TV show torrents
- **TorLock** - Verified torrents only
- **Nyaa** - Anime and Asian content
- **Zooqle** - Large collection with verified torrents
- **BTDB** - BitTorrent Database with extensive collection
- **GloDLS** - General torrent tracker
- **MagnetDL** - Magnet link focused torrent site
- **TorrentFunk** - Various torrent categories
- **iDope** - Music and general torrents
- **TorrentGalaxy** - Community-driven torrent site
- **YourBittorrent** - Clean interface torrent search
- **BitSearch** - Torrent meta-search engine
- **SumoTorrent** - General torrent tracker

### Onion Sites (Tor Network)
- **The Pirate Bay (Onion)** - TPB's official onion site
- **1337x (Onion)** - 1337x onion mirror
- **RARBG (Onion)** - High-quality torrents (configurable)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- (Optional) Tor Browser or Tor service for onion sites

### Setup Instructions

1. **Clone or download the project**
   ```bash
   cd torrent_search_engine
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   Open your web browser and go to: `http://localhost:5000`

### Tor Setup (Optional)

To access onion sites, you need to have Tor running:

#### Option 1: Tor Browser (Recommended)
1. Download and install [Tor Browser](https://www.torproject.org/download/)
2. Launch Tor Browser
3. Keep it running in the background

#### Option 2: Tor Service
1. Install Tor:
   - **Windows**: Download from torproject.org
   - **macOS**: `brew install tor`
   - **Linux**: `sudo apt-get install tor` or `sudo yum install tor`

2. Start Tor service:
   ```bash
   # Linux/macOS
   sudo service tor start
   # or
   tor &
   ```

3. Verify Tor is running on port 9050

## Usage

### Basic Search
1. Enter your search query in the search box
2. Click "Search" or press Enter
3. Results will appear from all enabled sources

### Advanced Features

#### Filtering
- **Category**: Filter by Movies, TV Shows, Games, Software, Music, or Books
- **Size**: Set minimum file size requirements
- **Seeds**: Filter by minimum number of seeds

#### Sorting
- **Seeds**: Sort by number of seeds (default)
- **Size**: Sort by file size
- **Name**: Sort alphabetically

#### Onion Sites
- To include onion sites in search, add `?onion=true` to the URL
- Example: `http://localhost:5000/?onion=true`

### API Endpoints

#### Search
```
GET /search?q=<query>&onion=<true|false>
```

#### Get Sources
```
GET /api/sources
```

#### Get Statistics
```
GET /api/stats
```

#### Clear Cache
```
POST /api/cache/clear
```

## Configuration

The application can be configured via `config.json`:

- **Cache settings**: Adjust timeout and size limits
- **Search settings**: Configure timeouts and result limits
- **Tor settings**: Enable/disable onion sites and configure proxy
- **Source settings**: Enable/disable specific torrent sites
- **Headers**: Customize HTTP headers for requests

## Security and Privacy

- **No tracking**: The application doesn't track user searches
- **Local only**: All processing happens locally on your machine
- **Tor support**: Optional anonymity through Tor network
- **No logs**: Search queries are not logged permanently

## Troubleshooting

### Common Issues

1. **"Search failed" errors**
   - Check your internet connection
   - Some torrent sites may be temporarily down
   - Try again with a different search query

2. **Onion sites not working**
   - Ensure Tor is running on port 9050
   - Check that Tor Browser is open if using that method
   - Verify Tor service is running properly

3. **Slow search results**
   - Some sites may be slow to respond
   - Consider disabling slower sources in config.json
   - Check your internet connection speed

4. **"No results found"**
   - Try different search terms
   - Check spelling of your query
   - Some content may not be available on tracked sites

### Performance Tips

- The application caches results for 5 minutes by default
- Duplicate results are automatically removed
- Search is limited to 100 total results to maintain performance
- Concurrent searching speeds up multi-source queries

## Legal Notice

This application is for educational and research purposes only. The developers are not responsible for how users choose to use this software. Please respect copyright laws and only download content that you have the legal right to access.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this project.

## License

This project is open source and available under the MIT License.

## Changelog

### Version 1.0.0
- Initial release with multi-source torrent search
- Support for 7 regular torrent sites
- Onion site support via Tor
- Web-based interface with filtering and sorting
- Caching system for performance
- RESTful API endpoints