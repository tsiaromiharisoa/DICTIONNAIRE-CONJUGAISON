from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ---------------------- SCRAPING DEFINITION ----------------------
def get_definition_url(mot):
    """Récupère l'URL Larousse pour un mot donné"""
    search_url = f"https://www.larousse.fr/dictionnaires/francais/{mot}"
    response = requests.get(search_url)
    if response.status_code == 200:
        return response.url
    else:
        return None

def scrape_definitions(url):
    """Scrape les définitions du mot"""
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        word = soup.find('h2', class_='AdresseDefinition').text.strip()
        category = soup.find('p', class_='CatgramDefinition').text.strip()
        definitions = [li.text.strip() for li in soup.find_all('li', class_='DivisionDefinition')]
        
        return {
            "word": word,
            "category": category,
            "definitions": definitions
        }
    else:
        return None

# ---------------------- SCRAPING CONJUGAISON ----------------------
def get_conjugaison_url(verbe):
    """Récupère l'URL Larousse pour la conjugaison du verbe"""
    search_url = f"https://www.larousse.fr/conjugaison/francais/{verbe}"
    response = requests.get(search_url)
    if response.status_code == 200:
        return response.url
    else:
        return None

def scrape_conjugaison(url):
    """Scrape les conjugaisons d'un verbe"""
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        verb = soup.find('h1').text.strip()
        
        conjugaison = {}
        sections = soup.find_all('section', id=True)
        
        for section in sections:
            mode = section.find('h2').text.strip()
            conjugaison[mode] = {}
            tenses = section.find_all('h3')
            for tense in tenses:
                tense_name = tense.text.strip()
                verbs = [li.text.strip() for li in tense.find_next('ul').find_all('li')]
                conjugaison[mode][tense_name] = verbs

        # Scraping des autres résultats potentiels (s'il y en a)
        other_results_section = soup.find('div', class_='hb-listresult')
        other_results = []
        if other_results_section:
            articles = other_results_section.find_all('article')
            for article in articles:
                result_title = article.find('h2').text.strip()
                result_description = article.find('p', class_='catgram').text.strip()
                other_results.append({
                    "title": result_title,
                    "description": result_description
                })
        
        return {
            "verb": verb,
            "conjugaison": conjugaison,
            "other_results": other_results
        }
    else:
        return None

# ---------------------- ROUTE DE RECHERCHE ----------------------
@app.route('/recherche', methods=['GET'])
def recherche():
    mot = request.args.get('dico')
    conjugaison_mot = request.args.get('conjugaison')

    # Vérifier si un mot est à rechercher
    if mot:
        url = get_definition_url(mot)
        if url:
            result = scrape_definitions(url)
            if result:
                return jsonify(result)
            else:
                return jsonify({"error": "Définitions non trouvées"}), 404
        else:
            return jsonify({"error": "Mot non trouvé"}), 404

    # Vérifier si un verbe est à conjuguer
    elif conjugaison_mot:
        url = get_conjugaison_url(conjugaison_mot)
        if url:
            result = scrape_conjugaison(url)
            if result:
                return jsonify(result)
            else:
                return jsonify({"error": "Conjugaison non trouvée"}), 404
        else:
            return jsonify({"error": "Verbe non trouvé"}), 404

    else:
        return jsonify({"error": "Veuillez fournir un mot ou un verbe"}), 400

# ---------------------- MAIN ----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
