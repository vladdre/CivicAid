"""
Clasifică query-urile pentru a determina dacă necesită rezultate din baza de date.
"""

import re


def needs_database_results(query: str, conversation_history: list = None) -> bool:
    """
    Determină dacă query-ul necesită rezultate din baza de date (instituții).
    
    Returnează True DOAR dacă întrebarea este clar despre unde să meargă/utilizeze.
    Altfel, returnează False pentru a permite generarea de rezumate.
    
    Args:
        query: Mesajul user-ului
        conversation_history: Istoricul conversației (opțional) pentru a înțelege contextul
        
    Returns:
        True dacă query-ul necesită rezultate din baza de date, False altfel
    """
    query_lower = query.lower().strip()
    
    # Pattern-uri STRICTE care indică clar o întrebare despre locații
    # Doar întrebări explicite despre "unde să merg/duc/rezolv/depun/aplic"
    location_patterns = [
        # "unde să merg", "unde să mă duc", "unde trebuie să merg"
        r'unde\s+(?:să|sa|trebuie|pot|trebui|se)\s+(?:mă|ma|te|se|să|sa)?\s*(?:duc|merg|rezolv|depun|aplic|mergi|rezolvi|depui|aplici)',
        # "unde merg", "unde mă duc"
        r'^unde\s+(?:mă|ma|te|se)?\s*(?:duc|merg|mergi)',
        # "unde rezolv", "unde depun", "unde aplic"
        r'^unde\s+(?:rezolv|depun|aplic|rezolvi|depui|aplici)',
        # "adresa", "adresă", "locația", "locul"
        r'(?:adresa|adresă|locația|locul)\s+(?:unde|la|pentru)',
        # "cum ajung", "cum mă duc"
        r'^cum\s+(?:ajung|mă\s+duc|ma\s+duc)',
        # "ce instituție" / "care instituție" (doar dacă este clar despre locație)
        r'(?:ce|care)\s+instituție\s+(?:să|sa|trebuie|pot)',
        # "trebuie să merg", "trebuie să mă duc", "trebuie să rezolv"
        r'trebuie\s+(?:să|sa)\s+(?:mă|ma|te|se)?\s*(?:duc|merg|rezolv|depun|aplic)',
        # "pot să merg", "pot să mă duc"
        r'pot\s+(?:să|sa)\s+(?:mă|ma|te|se)?\s*(?:duc|merg)',
    ]
    
    # Verifică pattern-urile stricte
    for pattern in location_patterns:
        if re.search(pattern, query_lower):
            return True
    
    # Dacă există context și mesajul este o întrebare de follow-up despre locații
    if conversation_history and len(conversation_history) > 0:
        # Verifică dacă mesajul curent este o întrebare de follow-up despre locații
        follow_up_location_patterns = [
            r'^unde\s+(?:să|sa|trebuie|pot)',
            r'^unde\?',
            r'^unde\s+(?:mă|ma|te|se)?\s*(?:duc|merg)',
        ]
        
        is_location_follow_up = any(re.search(pattern, query_lower) for pattern in follow_up_location_patterns)
        
        if is_location_follow_up:
            # Verifică dacă în context există informații despre un subiect specific
            # care ar necesita căutare în DB pentru locații
            context_text = " ".join([
                msg.get('content', '') for msg in conversation_history[-4:]
                if msg.get('role') == 'user'
            ]).lower()
            
            # Cuvinte cheie care sugerează nevoia de instituții (locații)
            subject_keywords = [
                'accident', 'pensie', 'buletin', 'identitate', 'carte', 'pașaport',
                'energie', 'gaz', 'căldură', 'apă', 'electricitate',
                'școală', 'educație', 'licență', 'permis',
                'sănătate', 'spital', 'medic', 'asigurare',
                'taxe', 'impozit', 'fiscal', 'anaf',
                'munca', 'angajare', 'șomaj', 'ajutor'
            ]
            
            # Dacă contextul menționează un subiect și mesajul este o întrebare despre locații
            if any(keyword in context_text for keyword in subject_keywords):
                return True
    
    # În toate celelalte cazuri, returnează False pentru a permite generarea de rezumate
    return False

