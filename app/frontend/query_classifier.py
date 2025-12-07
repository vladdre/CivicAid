"""
Clasifică query-urile pentru a determina dacă necesită rezultate din baza de date.
"""

import re


def needs_database_results(query: str) -> bool:
    """
    Determină dacă query-ul necesită rezultate din baza de date (instituții).
    
    Args:
        query: Mesajul user-ului
        
    Returns:
        True dacă query-ul necesită rezultate din baza de date, False altfel
    """
    query_lower = query.lower()
    
    # Cuvinte cheie care indică nevoia de rezultate din baza de date
    database_keywords = [
        'unde', 'adresa', 'adresă', 'loc', 'locație', 'locație',
        'merg', 'mă duc', 'du-te', 'du-te', 'mergi',
        'rezolv', 'rezolvă', 'rezolvi',
        'depun', 'depune', 'depui',
        'aplic', 'aplică', 'aplici',
        'contact', 'telefon', 'număr', 'numar',
        'program', 'orar', 'programul', 'orarul',
        'instituție', 'instituție', 'oficiu', 'birou',
        'găsesc', 'găsi', 'găsești',
        'caut', 'caută', 'cauți',
        'trebuie să', 'trebuie sa',
        'pot să', 'pot sa',
        'cum ajung', 'cum mă duc', 'cum ma duc',
        'ce instituție', 'ce instituție',
        'care instituție', 'care instituție'
    ]
    
    # Verifică dacă query-ul conține cuvinte cheie
    for keyword in database_keywords:
        if keyword in query_lower:
            return True
    
    # Verifică pattern-uri specifice
    patterns = [
        r'unde\s+(?:să|sa|trebuie|pot|trebui|se)\s+',
        r'(?:trebuie|pot|se)\s+(?:să|sa)\s+(?:mă|ma|te|se)\s+(?:duc|merg|rezolv)',
        r'(?:adresa|adresă|locul|locația)\s+(?:unde|la)',
        r'(?:cum|ce)\s+(?:instituție|instituție|oficiu)',
    ]
    
    for pattern in patterns:
        if re.search(pattern, query_lower):
            return True
    
    return False

