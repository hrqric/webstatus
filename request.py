from flask import Flask, request, jsonify, render_template
import requests
import time
import socket
import os
import csv
import datetime
from urllib.parse import urlparse

app = Flask(__name__,static_folder="static", template_folder='templates')

SITES_csv = "sites_database.csv"

def initialize_csv():
    if not os.path.exists(SITES_csv):
        with open(SITES_csv, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'url', 'status','last_check', 'response_time'])
            writer.writerow(['Google', 'https://www.google.com', 'online', '', ''])
            writer.writerow(['Facebook', 'https://www.facebook.com', 'online', '', ''])
            writer.writerow(['Twitter', 'https://www.twitter.com', 'online', '', ''])
            writer.writerow(['GitHub', 'https://www.github.com', 'online', '', ''])
            writer.writerow(['Stack Overflow', 'https://www.stackoverflow.com', 'online', '', ''])

@app.route('/get-sites', methods=['GET'])
def get_all_sites():
    sites = []
    if os.path.exists(SITES_csv):
        with open(SITES_csv,'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                sites.append({
                    'name': row['name'],
                    'url': row['url'],
                    'status': row['status'],
                    'last_check': row['last_check'],
                    'response_time': row['response_time']
                })
    return sites

def add_or_update_site(url,status,response_time=''):
    now = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    sites = get_all_sites()
    site_exists = False
    updated_sites = []

    parsed_url = urlparse(url)
    name = parsed_url.netloc.replace('www.', '')
    name = name.replace('.com','')


    for site in sites:
        if site['url'] == url:
            site_exists = True
            site['status'] = status
            site['last_check'] = now
            site['response_time'] = response_time
        updated_sites.append(site)

    if not site_exists:
        updated_sites.append({
            'name': name,
            'url': url,
            'status': status,
            'last_check': now,
            'response_time': response_time
            })


    with open(SITES_csv, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['name','url','status','last_check','response_time'])
        writer.writeheader()
        writer.writerows(updated_sites)

    return True

@app.route('/')
def index():
    initialize_csv()
    sites = get_all_sites()
    return render_template('index.html', sites=sites)

@app.route('/check-website', methods=['POST'])
def check_website():
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({'status': 'offline', 'error': 'URL NAO FORNECIDA'})
    
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    
    try:

        start_time = time.time()

        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        socket.gethostbyname(domain)

        response = requests.get(url,timeout=5,allow_redirects=True)

        response_time = round((time.time() - start_time) * 1000)
        
        if response.status_code < 400:
            add_or_update_site(url,'online',response_time)
            return jsonify({
                'status': 'online',
                'response_time': response_time,
                'status_code': response.status_code
                
            })
            
        else:
            add_or_update_site(url,'offline',response_time)
            return jsonify({
                'status': 'offline',
                'error': f'Código de status: {response.status_code}',
                'response_time': response_time
            })
        

    except socket.gaierror:
        return jsonify({
            'status': 'offline',
            'error': 'Não foi possivel resolver o nome do dominio'
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            'status': 'offline',
            'error': 'Falha na conexão'
        })
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'offline',
            'error': 'A requisição excedeu o tempo limite'
        })
    except requests.exceptions.TooManyRedirects:
        return jsonify({
            'status': 'offline',
            'error': 'Muitos redirecionamentos'
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'offline',
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)