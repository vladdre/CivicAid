"""
Tool pentru generarea automată a cererilor oficiale (ex: ANPC) pe baza input-ului utilizatorului.
"""

import os
import sys
import re
import base64
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# Set PROJECT_ROOT consistently
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "app"))

TEMPLATE_FILE = PROJECT_ROOT / "data" / "cerere_ANPC.txt"
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated_forms"


def detect_form_request(message: str) -> bool:
    """
    Detectează dacă mesajul utilizatorului cere generarea unui formular/cerere.
    
    Args:
        message: Mesajul utilizatorului
        
    Returns:
        True dacă mesajul cere generarea unui formular, False altfel
    """
    message_lower = message.lower()
    
    # Cuvinte cheie pentru trigger
    form_keywords = [
        'formular', 'form', 'cerere', 'solicitare',
        'anpc', 'autoritatea', 'protecția consumatorilor', 'protectia consumatorilor',
        'generează', 'genereaza', 'creează', 'creeaza',
        'completare', 'complet', 'completă', 'completa',
        'document', 'documente', 'petiție', 'petitie',
        'email', 'trimite', 'trimite email', 'trimite mail',
        'trimitere', 'trimite cerere', 'trimite formular',
        'am nevoie de o cerere scrisă', 'am nevoie de o cerere scrisa',
        'am nevoie de cerere', 'vreau cerere', 'vreau formular'
    ]
    
    # Verifică dacă mesajul conține cuvinte cheie
    for keyword in form_keywords:
        if keyword in message_lower:
            return True
    
    # Verifică pattern-uri specifice
    patterns = [
        r'(?:vrei|vreau|pot|poți|poate)\s+(?:să|sa)\s+(?:generez|generezi|generează|genereaza|creez|creezi|creează|creeaza|trimit|trimiți|trimite)\s+(?:un|o)\s+(?:formular|cerere|form|email)',
        r'(?:generează|genereaza|creează|creeaza|trimite|trimiți)\s+(?:un|o)\s+(?:formular|cerere|form|email)\s+(?:anpc|pentru|la)',
        r'(?:formular|cerere|form|email)\s+(?:anpc|pentru|la)',
        r'(?:trimite|trimiți)\s+(?:email|mail|cerere|formular)\s+(?:la|pentru|către)',
        r'(?:vrei|vreau)\s+(?:să|sa)\s+(?:trimiti|trimite|trimiți)\s+(?:email|mail|cerere|formular)',
        r'am\s+nevoie\s+de\s+(?:o|un)\s+cerere\s+scris[ăa]',
        r'am\s+nevoie\s+de\s+cerere',
    ]
    
    for pattern in patterns:
        if re.search(pattern, message_lower):
            return True
    
    return False


def request_user_info() -> str:
    """
    Returnează mesajul pentru cererea informațiilor necesare de la utilizator.
    
    Returns:
        Mesaj formatat cu cerințele
    """
    # Verifică dacă SMTP este configurat
    smtp_configured = bool(os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"))
    
    email_note = ""
    if not smtp_configured:
        email_note = "\n\n💡 Notă: Pentru a trimite email, asigurați-vă că SMTP este configurat în .env sau conectați-vă la Google OAuth accesând /auth/google"
    
    return f"""📧 Pentru a genera și trimite cererea ANPC prin email, am nevoie de următoarele informații:

**🔴 OBLIGATORIU:**

- **Email-ul dvs. (expeditor)** - adresa de email de la care se va trimite cererea
- **Email-ul instituției ANPC (destinatar)** - adresa de email către care se trimite cererea (ex: contact@anpc.ro)

**📋 Informații personale:**

- Nume și prenume complet
- Adresa completă (strada, număr, localitate, județ)
- Seria și numărul buletinului de identitate (opțional, dar recomandat)
- Număr de telefon (opțional)

**📝 Detalii despre cerere:**

- Ce informații sau acțiuni solicitați de la ANPC?
- Există o situație specifică pe care doriți să o menționați în cerere?
- Aveți întrebări specifice sau documente pe care doriți să le solicitați?

**💡 Exemplu de răspuns:**

```
Nume: Ion Popescu
Adresă: Str. Exemplu nr. 10, București, Sector 1
Email meu: ion.popescu@example.com
Email instituție ANPC: contact@anpc.ro
Telefon: 0712345678
Buletin: RO123456
Vreau să întreb despre procedura de returnare a produselor defecte după 15 zile.
```

Vă rog să furnizați toate aceste informații într-un singur mesaj pentru a putea genera și trimite cererea completă.{email_note}"""


def extract_user_info_from_conversation(conversation_history: list, current_message: str) -> dict:
    """
    Extrage informațiile utilizatorului din istoricul conversației și mesajul curent.
    
    Args:
        conversation_history: Istoricul conversației
        current_message: Mesajul curent al utilizatorului
        
    Returns:
        Dicționar cu informațiile extrase
    """
    # Combină toate mesajele pentru analiză
    all_text = current_message
    for msg in conversation_history:
        if msg.get('role') == 'user':
            all_text += " " + msg.get('content', '')
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {}
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=api_key
        )
        
        prompt = f"""Extrage informațiile necesare pentru completarea și trimiterea unei cereri ANPC din următorul text.

Text utilizator:

{all_text}

Extrage următoarele informații și returnează-le în format JSON:

{{
    "nume_prenume": "Nume complet sau null dacă nu este menționat",
    "adresa_completa": "Adresă completă sau null dacă nu este menționat",
    "telefon": "Număr de telefon sau null dacă nu este menționat",
    "email": "Adresă email a utilizatorului (expeditor) sau null dacă nu este menționat",
    "email_institutie": "Email-ul instituției ANPC (destinatar) sau null dacă nu este menționat",
    "serie_nr_buletin": "Seria și numărul buletinului sau null dacă nu este menționat",
    "gen": "masculin sau feminin sau null dacă nu poate fi determinat (determină din nume/prenume)",
    "intrebari_cerere": ["Listă de întrebări sau cereri specifice"],
    "context_situatie": "Context sau situație specifică menționată sau null"
}}

IMPORTANT pentru gen:
- Analizează numele și prenumele pentru a determina genul
- Prenume feminine românești: Maria, Ana, Elena, Ioana, etc.
- Prenume masculine românești: Ion, Gheorghe, Mihai, etc.
- Dacă nu poți determina, folosește null

IMPORTANT pentru email_institutie:
- Caută email-uri care se referă la ANPC, Autoritatea Națională pentru Protecția Consumatorilor
- Email-uri comune: contact@anpc.ro, anpc@anpc.ro, etc.
- Dacă nu este menționat, folosește null

Returnează DOAR JSON, fără explicații, fără markdown, fără backticks."""

        response = llm.invoke(prompt)
        result = json.loads(response.content.strip())
        return result
        
    except Exception as e:
        print(f"Eroare la extragerea informațiilor: {e}")
        return {}


def complete_form_template(user_info: dict, conversation_context: str = "") -> str:
    """
    Completează template-ul cererii ANPC cu informațiile utilizatorului folosind OpenAI.
    
    Args:
        user_info: Dicționar cu informațiile utilizatorului
        conversation_context: Context suplimentar din conversație
        
    Returns:
        Cererea completată ca string
    """
    # Citește template-ul
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"Template-ul nu există: {TEMPLATE_FILE}")
    
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = f.read()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY nu este setată")
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=api_key
    )
    
    # Determină genul pentru adaptarea textului
    gen = user_info.get('gen', '').lower() if user_info.get('gen') else None
    is_feminin = gen == 'feminin'
    
    # Adaptează template-ul pentru gen
    template_adapted = template
    if is_feminin:
        # Pentru feminin: păstrează (a)
        template_adapted = template_adapted.replace('Subsemnatul(a)', 'Subsemnata')
        template_adapted = template_adapted.replace('identificat(ă)', 'identificată')
    else:
        # Pentru masculin: elimină (a)
        template_adapted = template_adapted.replace('Subsemnatul(a)', 'Subsemnatul')
        template_adapted = template_adapted.replace('identificat(ă)', 'identificat')
    
    # Construiește prompt-ul pentru completare
    prompt = f"""Completează următorul template de cerere ANPC cu informațiile furnizate.

Template:

{template_adapted}

Informații utilizator:

{user_info}

Context conversație (dacă există):

{conversation_context}

Instrucțiuni:

1. Înlocuiește toate placeholder-urile [NUME_PRENUME_UTILIZATOR], [ADRESA_COMPLETA], etc. cu informațiile reale
2. Dacă o informație lipsește, folosește "[NU ESTE FURNIZAT]" pentru acea secțiune
3. Pentru [DATA_CURENTA], folosește data de astăzi în format DD.MM.YYYY
4. Păstrează formatarea și structura originală
5. Dacă utilizatorul a menționat întrebări specifice, le include în secțiunea [ÎNTREBAREA_1], [ÎNTREBAREA_2], etc.
6. Dacă există context sau situație specifică, adaugă-l înainte de întrebări
7. Păstrează tonul formal și profesional
8. Nu adăuga informații care nu sunt în datele furnizate
9. IMPORTANT: Template-ul este deja adaptat pentru gen (feminin/masculin), nu mai modifica "Subsemnatul/Subsemnata" sau "identificat/identificată"

Returnează DOAR cererea completată, fără explicații, fără markdown, fără backticks."""

    response = llm.invoke(prompt)
    completed_form = response.content.strip()
    
    # Curăță dacă are markdown
    if completed_form.startswith("```"):
        completed_form = completed_form.split("```")[1]
        if completed_form.startswith("text"):
            completed_form = completed_form[4:]
        completed_form = completed_form.strip()
    
    return completed_form


def send_email_with_gmail_api(form_text: str, sender_email: str, recipient_email: str, refresh_token: str, user_name: str = None) -> dict:
    """
    Trimite cererea completată prin Gmail API folosind OAuth.
    
    Args:
        form_text: Textul cererii completate
        sender_email: Adresa de email a utilizatorului (expeditor)
        recipient_email: Adresa de email a instituției ANPC (destinatar)
        refresh_token: Refresh token OAuth pentru Gmail
        user_name: Numele utilizatorului (opțional)
        
    Returns:
        Dict cu status și mesaj
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            return {
                'success': False,
                'message': '❌ Configurare OAuth incompletă. Verifică GOOGLE_CLIENT_ID și GOOGLE_CLIENT_SECRET în .env'
            }
        
        # Creează credențiale din refresh_token
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Reîmprospătează token-ul dacă e necesar
        if credentials.expired:
            credentials.refresh(Request())
        
        # Generează subject-ul din cerere
        subject = "Solicitare de informații de interes public conform Legii nr. 544/2001"
        if "Subiect:" in form_text:
            try:
                subject_line = [line for line in form_text.split('\n') if 'Subiect:' in line][0]
                subject = subject_line.split('Subiect:')[1].strip()
            except:
                pass
        
        # Construiește serviciul Gmail
        service = build('gmail', 'v1', credentials=credentials)
        
        # Obține email-ul real din Gmail API (pentru a seta corect From)
        profile = service.users().getProfile(userId='me').execute()
        actual_sender_email = profile.get('emailAddress')
        
        # Creează mesajul email
        message = MIMEText(form_text, 'plain', 'utf-8')
        message['To'] = recipient_email
        message['From'] = actual_sender_email  # Folosește email-ul real din Gmail
        message['Subject'] = subject
        
        # Encodează mesajul pentru Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Trimite email-ul prin Gmail API
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            'success': True,
            'message': f'✅ Cererea ANPC a fost trimisă cu succes!\n\n📧 De la: {actual_sender_email}\n📧 Către: {recipient_email}',
            'sender_email': actual_sender_email,
            'recipient_email': recipient_email,
            'message_id': send_message.get('id')
        }
        
    except Exception as e:
        error_str = str(e)
        # Verifică dacă eroarea este legată de adresa de email invalidă
        if 'invalid' in error_str.lower() or 'malformed' in error_str.lower() or 'address' in error_str.lower():
            return {
                'success': False,
                'message': f'❌ Adresa de email este invalidă: {recipient_email}\n\n🔍 Verifică că adresa "{recipient_email}" este corectă și există.\n\nEroare detaliată: {error_str}'
            }
        elif 'quota' in error_str.lower() or 'limit' in error_str.lower():
            return {
                'success': False,
                'message': f'❌ Limită de trimitere email-uri atinsă pentru contul Gmail.\n\nEroare: {error_str}'
            }
        elif 'authentication' in error_str.lower() or 'unauthorized' in error_str.lower():
            return {
                'success': False,
                'message': f'❌ Eroare de autentificare Gmail API. Reconectează-te la Google OAuth.\n\nEroare: {error_str}'
            }
        else:
            return {
                'success': False,
                'message': f'❌ Eroare la trimiterea email-ului prin Gmail API: {error_str}\n\n🔍 Verifică că adresa "{recipient_email}" este corectă.'
            }


def send_email_with_form(form_text: str, sender_email: str, recipient_email: str, user_name: str = None, refresh_token: str = None) -> dict:
    """
    Trimite cererea completată prin email de la adresa utilizatorului către instituție.
    Folosește Gmail API dacă refresh_token este furnizat, altfel folosește SMTP (fallback).
    
    Args:
        form_text: Textul cererii completate
        sender_email: Adresa de email a utilizatorului (expeditor)
        recipient_email: Adresa de email a instituției ANPC (destinatar)
        user_name: Numele utilizatorului (opțional)
        refresh_token: Refresh token OAuth pentru Gmail (opțional)
        
    Returns:
        Dict cu status și mesaj
    """
    # Dacă avem refresh_token, folosim Gmail API
    if refresh_token:
        return send_email_with_gmail_api(form_text, sender_email, recipient_email, refresh_token, user_name)
    
    # Fallback la SMTP (pentru compatibilitate)
    try:
        # Configurare SMTP din variabile de mediu
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not smtp_username or not smtp_password:
            return {
                'success': False,
                'message': '❌ Configurare SMTP incompletă. Verifică variabilele de mediu SMTP_USERNAME și SMTP_PASSWORD în .env'
            }
        
        # Generează subject-ul din cerere (extrage din primul rând sau folosește default)
        subject = "Solicitare de informații de interes public conform Legii nr. 544/2001"
        if "Subiect:" in form_text:
            try:
                subject_line = [line for line in form_text.split('\n') if 'Subiect:' in line][0]
                subject = subject_line.split('Subiect:')[1].strip()
            except:
                pass
        
        # Creează mesajul email
        msg = MIMEMultipart()
        msg['From'] = sender_email  # Email-ul utilizatorului
        msg['To'] = recipient_email  # Email-ul instituției
        msg['Subject'] = subject
        
        # Adaugă conținutul cererii în body (cererea completă)
        body = form_text
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Trimite email-ul folosind credențialele SMTP configurate
        # NOTĂ: Email-ul va apărea ca fiind trimis DE LA sender_email (utilizator)
        # dar va folosi serverul SMTP configurat pentru autentificare
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            # Folosim sendmail pentru a seta From manual
            # sendmail returnează un dicționar cu adresele care au eșuat
            failed_recipients = server.sendmail(sender_email, recipient_email, msg.as_string())
            
            # Verifică dacă au existat erori
            if failed_recipients:
                # failed_recipients este un dicționar: {email: (code, error_message)}
                error_details = []
                for email, (code, msg) in failed_recipients.items():
                    error_details.append(f"  • {email}: {code} - {msg}")
                
                return {
                    'success': False,
                    'message': f'❌ Eroare la trimiterea email-ului:\n\n📧 Adresă invalidă sau eroare:\n' + '\n'.join(error_details) + f'\n\n🔍 Verifică că adresa "{recipient_email}" este corectă și există.'
                }
        
        return {
            'success': True,
            'message': f'✅ Cererea ANPC a fost trimisă cu succes!\n\n📧 De la: {sender_email}\n📧 Către: {recipient_email}',
            'sender_email': sender_email,
            'recipient_email': recipient_email
        }
        
    except smtplib.SMTPRecipientsRefused as e:
        # Toate adresele au fost refuzate
        refused = ', '.join(e.recipients.keys())
        return {
            'success': False,
            'message': f'❌ Adresa de email a fost refuzată: {refused}\n\n🔍 Verifică că adresa "{recipient_email}" este corectă și există.'
        }
    except smtplib.SMTPDataError as e:
        return {
            'success': False,
            'message': f'❌ Eroare la datele email-ului: {str(e)}\n\n🔍 Verifică că adresa "{recipient_email}" este corectă.'
        }
    except smtplib.SMTPAuthenticationError:
        return {
            'success': False,
            'message': '❌ Eroare de autentificare SMTP. Verifică credențialele SMTP_USERNAME și SMTP_PASSWORD în .env'
        }
    except smtplib.SMTPConnectError as e:
        return {
            'success': False,
            'message': f'❌ Eroare la conectarea la serverul SMTP ({smtp_server}:{smtp_port}): {str(e)}'
        }
    except smtplib.SMTPException as e:
        return {
            'success': False,
            'message': f'❌ Eroare SMTP: {str(e)}\n\n🔍 Verifică configurația SMTP în .env și că adresa "{recipient_email}" este corectă.'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'❌ Eroare neașteptată: {str(e)}\n\n🔍 Verifică că adresa "{recipient_email}" este corectă și că serverul SMTP este accesibil.'
        }


def generate_pdf_from_text(text: str, output_filename: str = None) -> Path:
    """
    Generează un fișier PDF din textul cererii.
    
    Args:
        text: Textul cererii completate
        output_filename: Numele fișierului de output (opțional)
        
    Returns:
        Path către fișierul PDF generat
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
    except ImportError:
        raise ImportError("reportlab nu este instalat. Instalează cu: pip install reportlab")
    
    # Creează directorul de output dacă nu există
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generează nume de fișier dacă nu este furnizat
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"cerere_ANPC_{timestamp}.pdf"
    
    output_path = OUTPUT_DIR / output_filename
    
    # Creează PDF-ul
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Încearcă să încarce un font cu suport pentru diacritice românești
    # Folosim DejaVu Sans dacă este disponibil, altfel folosim fontul implicit cu encoding corect
    font_name = 'Helvetica'
    try:
        # Încearcă să găsească DejaVu Sans (comun pe Linux)
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        
        # Căută fonturi comune cu suport UTF-8
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            'C:/Windows/Fonts/arial.ttf',  # Windows
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('RomanianFont', font_path))
                    font_name = 'RomanianFont'
                    break
                except:
                    continue
    except:
        pass
    
    # Stiluri
    styles = getSampleStyleSheet()
    
    # Stil pentru text normal (justificat) cu font care suportă diacritice
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY,
        fontName=font_name,
        encoding='utf-8'
    )
    
    # Stil pentru titlu
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        leading=16,
        alignment=TA_LEFT,
        fontName=font_name if font_name == 'RomanianFont' else 'Helvetica-Bold',
        encoding='utf-8'
    )
    
    # Construiește conținutul
    story = []
    
    # Împarte textul în linii și procesează
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.3*cm))
            continue
        
        # Dacă linia pare a fi un titlu (toate majuscule sau scurtă)
        if line.isupper() and len(line) < 100:
            # Escapă caractere speciale pentru XML/PDF
            line_escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(line_escaped, title_style))
        else:
            # Escapă caractere speciale pentru XML/PDF, dar păstrează diacriticele
            line_escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(line_escaped, normal_style))
        
        story.append(Spacer(1, 0.2*cm))
    
    # Construiește PDF-ul
    doc.build(story)
    
    return output_path


def is_continuing_form_conversation(conversation_history: list) -> bool:
    """
    Verifică dacă conversația continuă un proces de formular ANPC.
    
    Args:
        conversation_history: Istoricul conversației
        
    Returns:
        True dacă ultimul mesaj al asistentului a fost cererea de informații pentru formular
    """
    if not conversation_history:
        return False
    
    # Verifică ultimul mesaj al asistentului
    for msg in reversed(conversation_history):
        if msg.get('role') == 'assistant':
            content = msg.get('content', '').lower()
            # Verifică dacă conține cererea de informații pentru formular
            if 'pentru a genera și trimite cererea anpc' in content or \
               'email-ul dvs. (expeditor)' in content or \
               'email-ul instituției anpc' in content:
                return True
            break
    
    return False


def get_user_email_from_db(username: str) -> Optional[str]:
    """
    Obține email-ul utilizatorului din baza de date.
    
    Args:
        username: Username-ul utilizatorului
        
    Returns:
        Email-ul utilizatorului sau None dacă nu există
    """
    try:
        users_file = PROJECT_ROOT / "data" / "users.json"
        if users_file.exists():
            import json
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
                if username in users:
                    return users[username].get('email', '')
    except Exception as e:
        print(f"Eroare la citirea email-ului din baza de date: {e}")
    return None


def generate_anpc_form(user_message: str, conversation_history: list = None, refresh_token: str = None, username: str = None) -> dict:
    """
    Funcție principală pentru generarea cererii ANPC.
    
    Args:
        user_message: Mesajul curent al utilizatorului
        conversation_history: Istoricul conversației
        refresh_token: Refresh token OAuth pentru Gmail (opțional)
        username: Username-ul utilizatorului (opțional, pentru a obține email-ul din baza de date)
        
    Returns:
        Dict cu status, mesaj și path către PDF (dacă a fost generat)
    """
    # Verifică dacă este trigger pentru formular SAU dacă continuă o conversație de formular
    is_form_trigger = detect_form_request(user_message)
    is_continuing = is_continuing_form_conversation(conversation_history or [])
    
    if not is_form_trigger and not is_continuing:
        return {
            'is_form_request': False,
            'message': None,
            'email_sent': False
        }
    
    # Extrage informațiile din conversație
    user_info = extract_user_info_from_conversation(conversation_history or [], user_message)
    
    # SIMULARE: Dacă email-ul nu este furnizat în conversație, încearcă să-l obțină din baza de date
    if not user_info.get('email') and username:
        db_email = get_user_email_from_db(username)
        if db_email:
            user_info['email'] = db_email
    
    # Verifică dacă sunt suficiente informații
    # Email-ul user-ului și email-ul instituției sunt OBLIGATORII
    # Dacă avem refresh_token (OAuth), email-ul user-ului va fi obținut din Gmail API
    required_fields = ['nume_prenume', 'adresa_completa', 'email_institutie']
    
    # Email-ul user-ului este obligatoriu dacă nu avem OAuth
    if not refresh_token:
        required_fields.append('email')  # Email-ul user-ului este obligatoriu fără OAuth
    
    missing_fields = [field for field in required_fields if not user_info.get(field)]
    
    if missing_fields:
        # Cere informațiile lipsă
        return {
            'is_form_request': True,
            'needs_info': True,
            'message': request_user_info(),
            'email_sent': False,
            'missing_fields': missing_fields
        }
    
    # Completează template-ul
    try:
        conversation_context = " ".join([
            msg.get('content', '') 
            for msg in (conversation_history or []) 
            if msg.get('role') == 'user'
        ])
        
        completed_form = complete_form_template(user_info, conversation_context)
        
        # Determină email-ul expeditor
        if refresh_token:
            # Pentru OAuth, email-ul va fi obținut din Gmail API (nu mai e nevoie de email în user_info)
            # Dar avem nevoie de un placeholder pentru a-l obține din Gmail API
            user_email = user_info.get('email')  # Poate fi None, dar Gmail API va folosi email-ul token-ului
        else:
            # Fără OAuth, email-ul user-ului este obligatoriu
            sender_email_config = os.getenv("FORM_SENDER_EMAIL")
            user_email = sender_email_config or user_info.get('email')
            if not user_email:
                return {
                    'is_form_request': True,
                    'needs_info': True,
                    'message': '❌ Email-ul dvs. (expeditor) este obligatoriu pentru trimiterea cererii. Vă rog să furnizați adresa de email.',
                    'email_sent': False,
                    'missing_fields': ['email']
                }
        
        # Email-ul destinatar (instituție) - OBLIGATORIU
        institution_email = user_info.get('email_institutie')
        if not institution_email:
            return {
                'is_form_request': True,
                'needs_info': True,
                'message': '❌ Email-ul instituției ANPC (destinatar) este obligatoriu. Vă rog să furnizați adresa de email a instituției (ex: contact@anpc.ro).',
                'email_sent': False,
                'missing_fields': ['email_institutie']
            }
        
        user_name = user_info.get('nume_prenume')
        
        email_result = send_email_with_form(completed_form, user_email, institution_email, user_name, refresh_token)
        
        if email_result.get('success'):
            return {
                'is_form_request': True,
                'needs_info': False,
                'message': email_result['message'],
                'email_sent': True,
                'sender_email': email_result.get('sender_email'),
                'recipient_email': email_result.get('recipient_email'),
                'form_text': completed_form
            }
        else:
            return {
                'is_form_request': True,
                'needs_info': False,
                'message': email_result['message'],
                'email_sent': False,
                'form_text': completed_form
            }
        
    except Exception as e:
        return {
            'is_form_request': True,
            'needs_info': False,
            'message': f"❌ Eroare la generarea/trimiterea cererii: {str(e)}",
            'email_sent': False
        }

