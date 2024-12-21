# app.py
from flask import Flask, render_template, request, jsonify, url_for
import requests
import json
from bs4 import BeautifulSoup
from flask_caching import Cache
import time
from datetime import datetime

app = Flask(__name__)

# Konfigurasi cache
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Fungsi untuk format timestamp
def format_time_ago(timestamp):
    try:
        if isinstance(timestamp, str):
            # Convert string timestamp to datetime
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

# Fungsi scraping komik
@cache.memoize(timeout=300)
def scrape_komik(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    komik_data = []
    komiks = soup.select('.list-update_item')

    for komik in komiks:
        title = komik.select_one('.title').text.strip()
        full_link = komik.select_one('a')['href']
        
        # Format link untuk detail
        # Hapus domain dan 'komik' dari URL
        relative_link = full_link.replace('https://komikcast.bz/komik/', '')
        relative_link = relative_link.replace('https://komikcast.bz/', '')
        
        # Pastikan tidak ada slash ganda
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
            'link': relative_link,  # Link yang sudah diformat
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

# Fungsi scraping detail komik
@cache.memoize(timeout=300)
def scrape_detail_komik(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Data dasar
        thumbnail_elem = soup.select_one('.komik_info-content-thumbnail img')
        thumbnail = thumbnail_elem['src'] if thumbnail_elem else ''
        
        title_elem = soup.select_one('.komik_info-content-body-title')
        title = title_elem.text.strip() if title_elem else ''
        
        native_title_elem = soup.select_one('.komik_info-content-native')
        native_title = native_title_elem.text.strip() if native_title_elem else ''

        # Sinopsis
        synopsis_elem = soup.select_one('.komik_info-description-sinopsis')
        synopsis = synopsis_elem.text.strip() if synopsis_elem else ''
        
        # Genre
        genres = [genre.text for genre in soup.select('.komik_info-content-genre .genre-item')]
        
        # Informasi detail
        info_elements = soup.select('.komik_info-content-info')
        release = ''
        author = ''
        status = ''
        komik_type = ''
        total_chapter = ''
        
        for info in info_elements:
            text = info.text.strip()
            if 'Released:' in text:
                release = text.replace('Released:', '').strip()
            elif 'Author:' in text:
                author = text.replace('Author:', '').strip()
            elif 'Status:' in text:
                status = text.replace('Status:', '').strip()
            elif 'Total Chapter:' in text:
                total_chapter = text.replace('Total Chapter:', '').strip()

        type_elem = soup.select_one('.komik_info-content-info-type a')
        komik_type = type_elem.text.strip() if type_elem else ''

        updated_elem = soup.select_one('.komik_info-content-update time')
        updated_on = updated_elem['datetime'] if updated_elem and 'datetime' in updated_elem.attrs else ''

        rating_elem = soup.select_one('.data-rating')
        rating = rating_elem['data-ratingkomik'] if rating_elem else '0'

        # Chapter list
        chapters = []
        chapter_items = soup.select('.komik_info-chapters-item')
        for chapter in chapter_items:
            chapter_link_elem = chapter.select_one('.chapter-link-item')
            if chapter_link_elem:
                full_chapter_link = chapter_link_elem['href']
                relative_chapter_link = full_chapter_link.replace('https://komikcast.bz', '')
                if not relative_chapter_link.startswith('/'):
                    relative_chapter_link = '/' + relative_chapter_link
                
                time_elem = chapter.select_one('.chapter-link-time')
                update_time = time_elem['datetime'] if time_elem and 'datetime' in time_elem.attrs else ''
                    
                chapters.append({
                    'title': chapter_link_elem.text.strip(),
                    'link': relative_chapter_link,
                    'time': update_time
                })

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

# Fungsi scraping chapter
# ... (kode sebelumnya tetap sama sampai fungsi scraping chapter)

# Fungsi scraping chapter
@cache.memoize(timeout=300)
def scrape_chapter(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Ambil judul chapter
        title_elem = soup.select_one('.chapter_headpost h1')
        title = title_elem.text.strip() if title_elem else ''

        # Ambil navigasi chapter
        chapter_nav = soup.select_one('.chapter_nav-control')
        chapter_options = []
        
        if chapter_nav:
            select_elem = chapter_nav.select_one('select#slch')
            if select_elem:
                for option in select_elem.find_all('option'):
                    full_link = option['value']
                    relative_link = full_link.replace('https://komikcast.bz', '')
                    if not relative_link.startswith('/'):
                        relative_link = '/' + relative_link

                    chapter_options.append({
                        'title': option.text.strip(),
                        'link': relative_link,
                        'selected': 'selected' in option.attrs
                    })

        # Ambil link previous dan next chapter
        prev_chapter = soup.select_one('a[rel="prev"]')
        next_chapter = soup.select_one('a[rel="next"]')
        
        relative_prev_link = prev_chapter['href'].replace('https://komikcast.bz', '') if prev_chapter else None
        relative_next_link = next_chapter['href'].replace('https://komikcast.bz', '') if next_chapter else None
        
        # Ambil gambar chapter
        images = []
        for img in soup.find_all('img', class_='alignnone'):
            if img.get('src'):
                images.append(img['src'])
            elif img.get('data-src'):
                images.append(img['data-src'])

        return {
            'title': title,
            'chapter_options': chapter_options,
            'prev_chapter': relative_prev_link,
            'next_chapter': relative_next_link,
            'images': images
        }
            
    except Exception as e:
        print(f"Error scraping chapter: {str(e)}")
        return None


# Routes
@app.route('/')
def home():
    try:
        # Ambil manga populer
        popular_url = "https://komikcast.bz/daftar-komik/?status=&type=&orderby=popular"
        popular_data, _ = scrape_komik(popular_url)
        
        # Ambil manga terbaru
        latest_url = "https://komikcast.bz/daftar-komik/?status=&type=&orderby=update"
        latest_data, _ = scrape_komik(latest_url)
        
        # Ambil manga featured (misalnya 6 manga teratas dari populer)
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

@app.route('/popular')
def popular():
    page = request.args.get('page', 1, type=int)
    items_per_page = 10  # Sesuaikan dengan kebutuhan
    
    url = f"https://komikcast.bz/daftar-komik/?status=&type=&orderby=popular&page={page}"
    komik_data, next_page = scrape_komik(url)
    
    # Memastikan tidak ada duplikasi dengan tracking ID
    seen_ids = set()
    unique_komik = []
    
    for komik in komik_data:
        # Buat unique ID dari kombinasi judul dan chapter
        komik_id = f"{komik['title']}-{komik['chapter']}"
        if komik_id not in seen_ids:
            seen_ids.add(komik_id)
            unique_komik.append(komik)
    
    # Slice data sesuai pagination
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_komik = unique_komik[start_idx:end_idx]
    
    has_next = len(unique_komik) > end_idx
    
    return render_template(
        'popular.html',
        komik_data=paginated_komik,
        current_page=page,
        has_next=has_next,
        format_time_ago=format_time_ago
    )

@app.route('/latest')
def latest():
    page = request.args.get('page', 1, type=int)
    items_per_page = 10  # Sesuaikan dengan kebutuhan
    
    url = f"https://komikcast.bz/daftar-komik/?status=&type=&orderby=update&page={page}"
    komik_data, next_page = scrape_komik(url)
    
    # Memastikan tidak ada duplikasi dengan tracking ID
    seen_ids = set()
    unique_komik = []
    
    for komik in komik_data:
        # Buat unique ID dari kombinasi judul dan chapter
        komik_id = f"{komik['title']}-{komik['chapter']}"
        if komik_id not in seen_ids:
            seen_ids.add(komik_id)
            unique_komik.append(komik)
    
    # Slice data sesuai pagination
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_komik = unique_komik[start_idx:end_idx]
    
    has_next = len(unique_komik) > end_idx
    
    return render_template(
        'latest.html',
        komik_data=paginated_komik,
        current_page=page,
        has_next=has_next,
        format_time_ago=format_time_ago
    )

@app.route('/detail/<path:url>')
def detail(url):
    if not url.startswith('/'):
        url = '/' + url
    
    komik_url = f"https://komikcast.bz{url}"
    komik_detail = scrape_detail_komik(komik_url)
    
    if komik_detail is None:
        return render_template('error.html', error_message="Komik tidak ditemukan"), 404
        
    return render_template(
        'detail.html',
        komik_detail=komik_detail,
        format_time_ago=format_time_ago
    )

@app.route('/chapter/<path:url>')
def chapter(url):
    try:
        if not url.startswith('/'):
            url = '/' + url
        
        chapter_url = f"https://komikcast.bz{url}"
        chapter_data = scrape_chapter(chapter_url)
        
        if chapter_data is None:
            return render_template('error.html', error_message="Chapter tidak ditemukan"), 404
            
        return render_template('chapter.html', chapter_data=chapter_data)
    except Exception as e:
        print(f"Error in chapter route: {str(e)}")
        return render_template('error.html', error_message="Terjadi kesalahan saat memuat chapter"), 500


if __name__ == '__main__':
    app.run(debug=True)