from habanero import Crossref

def citation_to_url(text):
    cr = Crossref(mailto="b@fir.sh")
    results = cr.works(query_bibliographic=text, limit=1, select=["score", "URL"])
    if not results['message']['items']:
        return None
    top_result = results['message']['items'][0]
    if top_result['score'] < 75:
        return None
    return top_result['URL']
    
