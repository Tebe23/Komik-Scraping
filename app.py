from flask import Flask, render_template, request, jsonify, url_for, redirect
import requests
import json
from bs4 import BeautifulSoup
from flask_caching import Cache
import time
from datetime import datetime

app = Flask(__name__)

# Konfigurasi cache
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Fungsi helper untuk menghapus cache
def clear_manga_cache():
    """Hapus cache untuk semua fungsi scraping manga"""
    cache.delete_memoized(scrape_komik)
    cache.delete_memoized(scrape_detail_komik)
    cache.delete_memoized(scrape_chapter)

# Fungsi untuk format timestamp
def format_time_ago(timestamp):
    try:
        if isinstance(timestamp, str):
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            timestamp = dt.timestamp()
        
        current_time = time.time()
        time_diff = current_time - float(timestamp)
        
        if time_diff < 60:
            return "Baru saja"
        elif time_diff < 3600:
            minutes = int(time_diff / 60)
            return f"{minutes} menit yang lalu"
        elif time_diff < 86400:
            hours = int(time_diff / 3600)
            return f"{hours} jam yang lalu"
        else:
            days = int(time_diff / 86400)
            return f"{days} hari yang lalu"
    except Exception as e:
        print(f"Error formatting time: {str(e)}")
        return timestamp

# Fungsi scraping komik dengan parameter force refresh
@cache.memoize(timeout=300)
def scrape_komik(url, force_refresh=False):
    if force_refresh:
        cache.delete_memoized(scrape_komik, url)
    
    response = requests.get(url)
    response.encoding = 'utf-8'  
    soup = BeautifulSoup(response.text, 'html.parser')

    komik_data = []
    komiks = soup.select('.list-update_item')

    for komik in komiks:
        title = komik.select_one('.title').text.strip()
        full_link = komik.select_one('a')['href']
        
        relative_link = full_link.replace('https://komikcast.bz/komik/', '')
        relative_link = relative_link.replace('https://komikcast.bz/', '')
        
        while '//' in relative_link:
            relative_link = relative_link.replace('//', '/')
            
        image = komik.select_one('img')['src']
        chapter = komik.select_one('.chapter').text.strip() if komik.select_one('.chapter') else "N/A"
        score = komik.select_one('.numscore').text.strip() if komik.select_one('.numscore') else "N/A"
        time_elem = komik.select_one('.timeago')
        update_time = time_elem['datetime'] if time_elem else None
        
        types = komik.select_one('.type').text.strip() if komik.select_one('.type') else "N/A"
        status = komik.select_one('.status').text.strip() if komik.select_one('.status') else "N/A"

        komik_data.append({
            'title': title,
            'link': relative_link,
            'image': image,
            'chapter': chapter,
            'score': score,
            'update_time': update_time,
            'type': types,
            'status': status
        })

    next_page = soup.select_one('a.next.page-numbers')
    next_page_url = next_page['href'] if next_page else None

    return komik_data, next_page_url

# Fungsi scraping detail komik dengan parameter force refresh
@cache.memoize(timeout=300)
def scrape_detail_komik(url, force_refresh=False):
    if force_refresh:
        cache.delete_memoized(scrape_detail_komik, url)
        
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'  
        soup = BeautifulSoup(response.text, 'html.parser')

        # Data detail komik
        # ... (kode detail komik yang sama seperti sebelumnya)
        
        return {
            'thumbnail': thumbnail,
            'title': title,
            'native_title': native_title,
            'synopsis': synopsis,
            'genres': genres,
            'release': release,
            'author': author,
            'status': status,
            'type': komik_type,
            'total_chapter': total_chapter,
            'updated_on': updated_on,
            'rating': rating,
            'chapters': chapters
        }
    except Exception as e:
        print(f"Error scraping detail: {str(e)}")
        return None

# Fungsi scraping chapter dengan parameter force refresh
@cache.memoize(timeout=300)
def scrape_chapter(url, force_refresh=False):
    if force_refresh:
        cache.delete_memoized(scrape_chapter, url)
        
    try:
        # ... (kode chapter yang sama seperti sebelumnya)
        return chapter_data
    except Exception as e:
        print(f"Error in chapter: {str(e)}")
        return None

# Routes
@app.route('/')
def home():
    # Cek parameter refresh dari URL
    force_refresh = request.args.get('refresh', '0') == '1'
    
    try:
        # Ambil manga populer dengan parameter force_refresh
        popular_url = "https://komikcast.bz/daftar-komik/?status=&type=&orderby=popular"
        popular_data, _ = scrape_komik(popular_url, force_refresh)
        
        # Ambil manga terbaru dengan parameter force_refresh
        latest_url = "https://komikcast.bz/daftar-komik/?sortby=update"
        latest_data, _ = scrape_komik(latest_url, force_refresh)
        
        featured_data = popular_data[:6] if popular_data else []
        
        return render_template(
            'home.html',
            featured_manga=featured_data,
            latest_manga=latest_data[:12] if latest_data else [],
            popular_manga=popular_data[:12] if popular_data else [],
            format_time_ago=format_time_ago
        )
    except Exception as e:
        app.logger.error(f"Home page error: {str(e)}")
        return render_template('error.html', error="Terjadi kesalahan saat memuat halaman")

# Route untuk popular dengan parameter refresh
@app.route('/popular')
def popular():
    force_refresh = request.args.get('refresh', '0') == '1'
    page = request.args.get('page', 1, type=int)
    items_per_page = 10
    
    url = f"https://komikcast.bz/daftar-komik/?status=&type=&orderby=popular&page={page}"
    komik_data, next_page = scrape_komik(url, force_refresh)
    
    # ... (kode pagination yang sama)
    return render_template(
        'popular.html',
        komik_data=paginated_komik,
        current_page=page,
        has_next=has_next,
        format_time_ago=format_time_ago
    )

# Route untuk latest dengan parameter refresh
@app.route('/latest')
def latest():
    force_refresh = request.args.get('refresh', '0') == '1'
    page = request.args.get('page', 1, type=int)
    items_per_page = 10
    
    url = f"https://komikcast.bz/daftar-komik/?status=&type=&orderby=update&page={page}"
    komik_data, next_page = scrape_komik(url, force_refresh)
    
    # ... (kode pagination yang sama)
    return render_template(
        'latest.html',
        komik_data=paginated_komik,
        current_page=page,
        has_next=has_next,
        format_time_ago=format_time_ago
    )

# Route untuk detail dengan parameter refresh
@app.route('/detail/<path:url>')
def detail(url):
    force_refresh = request.args.get('refresh', '0') == '1'
    
    if not url.startswith('/'):
        url = '/' + url
    
    komik_url = f"https://komikcast.bz{url}"
    komik_detail = scrape_detail_komik(komik_url, force_refresh)
    
    if komik_detail is None:
        return render_template('error.html', error_message="Komik tidak ditemukan"), 404
        
    return render_template(
        'detail.html',
        komik_detail=komik_detail,
        format_time_ago=format_time_ago
    )

# Route untuk chapter dengan parameter refresh
@app.route('/chapter/<path:url>')
def chapter(url):
    force_refresh = request.args.get('refresh', '0') == '1'
    
    try:
        if not url.startswith('/'):
            url = '/' + url
        
        chapter_url = f"https://komikcast.bz{url}"
        chapter_data = scrape_chapter(chapter_url, force_refresh)
        
        if chapter_data is None:
            return render_template('error.html', error_message="Chapter tidak ditemukan"), 404
            
        return render_template('chapter.html', chapter_data=chapter_data)
    except Exception as e:
        print(f"Error in chapter route: {str(e)}")
        return render_template('error.html', error_message="Terjadi kesalahan saat memuat chapter"), 500

# Route khusus untuk clear cache
@app.route('/refresh')
def refresh_data():
    clear_manga_cache()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)