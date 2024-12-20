from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from flask_caching import Cache

app = Flask(__name__)

# Konfigurasi cache
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Fungsi scraping
@cache.memoize(timeout=300)  # Cache hasil fungsi ini selama 300 detik (5 menit)
def scrape_komik(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    komik_data = []
    komiks = soup.select('.list-update_item')

    for komik in komiks:
        title = komik.select_one('.title').text.strip()
        link = komik.select_one('a')['href']
        image = komik.select_one('img')['src']
        chapter = komik.select_one('.chapter').text.strip() if komik.select_one('.chapter') else "N/A"
        score = komik.select_one('.numscore').text.strip() if komik.select_one('.numscore') else "N/A"

        komik_data.append({
            'title': title,
            'link': link,
            'image': image,
            'chapter': chapter,
            'score': score
        })

    next_page = soup.select_one('a.next.page-numbers')
    next_page_url = next_page['href'] if next_page else None

    return komik_data, next_page_url

# Halaman utama
@app.route('/')
def home():
    popular_url = "https://komikcast.bz/daftar-komik/?status=&type=&orderby=popular"
    latest_url = "https://komikcast.bz/daftar-komik/?status=&type=&orderby=update"

    # Scrape data populer dan terbaru
    popular_data, popular_next = scrape_komik(popular_url)
    latest_data, latest_next = scrape_komik(latest_url)

    return render_template(
        'home.html',
        popular_data=popular_data,
        popular_next=popular_next,
        latest_data=latest_data,
        latest_next=latest_next
    )

# Endpoint untuk load more
@app.route('/load_more', methods=['POST'])
def load_more():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    url = data['url']
    komik_data, next_page = scrape_komik(url)
    return jsonify({
        'komik_data': komik_data,
        'next_page': next_page
    })
    
@app.route('/popular')
def all_popular():
    all_popular_data = []
    base_url = "https://komikcast.bz/daftar-komik/?status=&type=&orderby=popular&page="
    
    # Loop untuk mendapatkan data dari page 1 sampai 5
    for i in range(1, 6):
        url = f"{base_url}{i}"
        komik_data, _ = scrape_komik(url)
        all_popular_data.extend(komik_data)
    
    return render_template('all_popular.html', komik_data=all_popular_data)

@app.route('/latest')
def all_latest():
    all_latest_data = []
    base_url = "https://komikcast.bz/daftar-komik/?status=&type=&orderby=update&page="
    
    # Loop untuk mendapatkan data dari page 1 sampai 5
    for i in range(1, 6):
        url = f"{base_url}{i}"
        komik_data, _ = scrape_komik(url)
        all_latest_data.extend(komik_data)
    
    return render_template('all_latest.html', komik_data=all_latest_data)

if __name__ == '__main__':
    app.run(debug=True)