"""
SOP Export Utilities — Preprocesses rich HTML content for clean PDF and DOCX export.

The SOP content is stored as Bootstrap-rich HTML (with CSS classes like 'table',
'table-bordered', 'fw-bold', 'text-primary', etc.) and FontAwesome icon tags.
Neither xhtml2pdf (PDF) nor htmldocx (DOCX) understand these, so we must
convert the HTML into a portable format with inline styles before export.
"""

import re
import os
from bs4 import BeautifulSoup, NavigableString
from django.conf import settings


# ── Colour palette ─────────────────────────────────────────────
_BLUE_PRIMARY = '#1e40af'
_BLUE_ACCENT = '#3b82f6'
_GREY_TEXT = '#334155'
_GREY_LIGHT = '#64748b'
_GREY_BG = '#f1f5f9'
_BORDER = '#cbd5e1'
_WARNING_BG = '#fff7ed'
_WARNING_BORDER = '#f59e0b'
_DANGER_BG = '#fef2f2'
_DANGER_BORDER = '#ef4444'
_SUCCESS_BG = '#f0fdf4'
_SUCCESS_BORDER = '#22c55e'


def _inline_table(tag):
    """Add inline styles to a <table> and its children."""
    existing = tag.get('style', '')
    tag['style'] = (
        f'width:100%; border-collapse:collapse; margin:12px 0; '
        f'font-size:10pt; {existing}'
    ).strip()
    # Remove Bootstrap classes that mean nothing outside a browser
    for cls in list(tag.get('class', [])):
        pass  # keep classes for selector matching but they won't matter

    for th in tag.find_all('th'):
        th['style'] = (
            f'border:1px solid {_BORDER}; padding:8px 10px; '
            f'background-color:{_GREY_BG}; color:{_BLUE_PRIMARY}; '
            f'font-weight:bold; text-align:left; font-size:10pt;'
        )

    for td in tag.find_all('td'):
        existing_td = td.get('style', '')
        td['style'] = (
            f'border:1px solid {_BORDER}; padding:6px 10px; '
            f'vertical-align:top; font-size:10pt; {existing_td}'
        ).strip()


def _handle_images(soup):
    """
    Handle <img> tags for export.
    Convert relative media URLs to absolute filesystem paths.
    """
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if not src:
            continue
            
        # Convert media URLs to absolute filesystem paths
        if src.startswith(settings.MEDIA_URL):
            relative_path = src[len(settings.MEDIA_URL):].replace('/', os.sep)
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            if os.path.exists(absolute_path):
                img['src'] = absolute_path
        
        # Ensure images don't overflow the page
        existing_style = img.get('style', '')
        img['style'] = f'max-width:100%; height:auto; {existing_style}'.strip()


def _inline_heading(tag, level):
    """Add inline styles to heading tags."""
    sizes = {1: '20pt', 2: '16pt', 3: '14pt', 4: '12pt', 5: '11pt', 6: '10pt'}
    colours = {1: _BLUE_PRIMARY, 2: _BLUE_PRIMARY, 3: _BLUE_ACCENT,
               4: _BLUE_ACCENT, 5: _BLUE_ACCENT, 6: _GREY_TEXT}
    tag['style'] = (
        f'font-size:{sizes.get(level, "11pt")}; '
        f'color:{colours.get(level, _GREY_TEXT)}; '
        f'font-weight:bold; margin-top:16px; margin-bottom:8px;'
    )


def _inline_alert_for_docx(tag, soup):
    """
    For DOCX, htmldocx doesn't handle borders on divs well.
    Convert alerts to a 1x1 table with a background color.
    """
    classes = tag.get('class', [])
    bg = _WARNING_BG
    if 'alert-danger' in classes:
        bg = _DANGER_BG
    elif 'alert-success' in classes:
        bg = _SUCCESS_BG
    elif 'alert-info' in classes:
        bg = '#eff6ff'
    
    # Create a new table
    new_table = soup.new_tag('table')
    new_table['style'] = f'width:100%; border:1pt solid {_BORDER}; background-color:{bg}; margin:10pt 0;'
    new_table['class'] = ['word-alert-table']
    
    row = soup.new_tag('tr')
    cell = soup.new_tag('td')
    cell['style'] = 'padding:10pt; border:none;'
    
    # Move content from alert div to table cell
    for content_item in list(tag.contents):
        cell.append(content_item)
        
    row.append(cell)
    new_table.append(row)
    tag.replace_with(new_table)


def _strip_icon_tags(soup):
    """
    Replace FontAwesome <i> tags (and similar empty icon elements) with a
    simple text equivalent or nothing at all.
    """
    icon_map = {
        'fa-chevron-right': '▸ ',
        'fa-exclamation-triangle': '⚠ ',
        'fa-exclamation-circle': '⚠ ',
        'fa-clipboard-check': '☑ ',
        'fa-check-circle': '✓ ',
        'fa-check': '✓ ',
        'fa-book': '📖 ',
        'fa-info-circle': 'ℹ ',
        'fa-heartbeat': '♥ ',
        'fa-shield-virus': '🛡 ',
        'fa-pills': '💊 ',
        'fa-cogs': '⚙ ',
        'fa-ambulance': '🚑 ',
        'fa-flask': '🧪 ',
        'fa-user-nurse': '👩‍⚕ ',
        'fa-file-alt': '📄 ',
        'fa-spinner': '',
        'fa-eye': '',
        'fa-paperclip': '📎 ',
    }
    for i_tag in soup.find_all('i'):
        classes = i_tag.get('class', [])
        replacement_text = ''
        for cls in classes:
            if cls in icon_map:
                replacement_text = icon_map[cls]
                break
        i_tag.replace_with(replacement_text)


def _handle_colspan_header(soup):
    """
    htmldocx has a known bug with colspan/rowspan (IndexError).
    Instead of just stripping them, we attempt to 'balance' the table 
    by adding the missing cells so that every row has the same number of cells.
    """
    for table in soup.find_all('table'):
        # Find the max number of cells in any row
        max_cells = 0
        rows = table.find_all('tr')
        for row in rows:
            count = 0
            for cell in row.find_all(['td', 'th']):
                cs = cell.get('colspan')
                count += int(cs) if cs and cs.isdigit() else 1
            max_cells = max(max_cells, count)
        
        # Balance each row
        for row in rows:
            current_cells = row.find_all(['td', 'th'])
            actual_count = 0
            for cell in current_cells:
                cs = cell.get('colspan')
                val = int(cs) if cs and cs.isdigit() else 1
                actual_count += val
                # Remove the attributes that crash htmldocx
                if 'colspan' in cell.attrs: del cell.attrs['colspan']
                if 'rowspan' in cell.attrs: del cell.attrs['rowspan']
            
            # Add missing cells to match max_cells
            while actual_count < max_cells:
                new_cell = soup.new_tag('td')
                new_cell.string = ""
                new_cell['style'] = 'border:1px solid #cbd5e1;'
                row.append(new_cell)
                actual_count += 1


def _inline_bootstrap_utilities(soup):
    """Convert common Bootstrap utility classes to inline styles."""
    utility_map = {
        'fw-bold': 'font-weight:bold;',
        'text-primary': f'color:{_BLUE_ACCENT};',
        'text-danger': f'color:{_DANGER_BORDER};',
        'text-success': f'color:{_SUCCESS_BORDER};',
        'text-muted': f'color:{_GREY_LIGHT};',
        'text-center': 'text-align:center;',
        'mb-0': 'margin-bottom:0;',
        'mb-2': 'margin-bottom:8px;',
        'mb-3': 'margin-bottom:12px;',
        'mb-4': 'margin-bottom:16px;',
        'mt-4': 'margin-top:16px;',
        'p-2': 'padding:8px;',
        'p-3': 'padding:12px;',
        'bg-light': f'background-color:{_GREY_BG};',
    }

    for tag in soup.find_all(True):
        classes = tag.get('class', [])
        if not classes:
            continue
        added_styles = []
        for cls in classes:
            if cls in utility_map:
                added_styles.append(utility_map[cls])
        if added_styles:
            existing = tag.get('style', '')
            tag['style'] = ' '.join(added_styles) + ' ' + existing


def _inline_lists(soup):
    """Add basic inline styles to lists for consistent rendering."""
    for ul in soup.find_all('ul'):
        ul['style'] = 'margin:0 0 12px 0; padding-left:30px;'
    for ol in soup.find_all('ol'):
        existing = ol.get('style', '')
        if 'padding-left' not in existing:
            ol['style'] = f'margin:0 0 12px 0; padding-left:30px; {existing}'.strip()
    for li in soup.find_all('li'):
        li['style'] = 'margin-bottom:4px; font-size:10pt;'


def _inline_paragraphs(soup):
    """Add basic inline styles to paragraphs."""
    for p in soup.find_all('p'):
        existing = p.get('style', '')
        if 'font-size' not in existing:
            p['style'] = f'margin:0 0 8px 0; line-height:1.5; font-size:10pt; {existing}'.strip()


def preprocess_html_for_export(html_content, is_docx=False):
    """
    Main function: takes SOP HTML content (Bootstrap-rich) and returns
    clean HTML with inline styles suitable for xhtml2pdf or htmldocx.
    """
    if not html_content:
        return html_content

    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Strip FontAwesome icons → text equivalents
    _strip_icon_tags(soup)

    # 2. Handle colspan/rowspan in header block
    # For Word, we must be very careful with tables
    _handle_colspan_header(soup)

    # 3. Inline Bootstrap utility classes
    _inline_bootstrap_utilities(soup)

    # 3.5 Handle images (convert to absolute paths)
    _handle_images(soup)

    # 4. Style alerts
    if is_docx:
        for alert in soup.find_all('div', class_=lambda c: c and 'alert' in c):
            _inline_alert_for_docx(alert, soup)
    else:
        # Standard PDF alert styling
        for tag in soup.find_all('div', class_=lambda c: c and 'alert' in c):
            classes = tag.get('class', [])
            bg = _WARNING_BG
            border_colour = _WARNING_BORDER
            if 'alert-danger' in classes:
                bg = _DANGER_BG
                border_colour = _DANGER_BORDER
            elif 'alert-success' in classes:
                bg = _SUCCESS_BG
                border_colour = _SUCCESS_BORDER
            elif 'alert-info' in classes:
                bg = '#eff6ff'
                border_colour = _BLUE_ACCENT
            tag['style'] = (
                f'border-left:4px solid {border_colour}; '
                f'background-color:{bg}; padding:12px 16px; '
                f'margin:12px 0; font-size:10pt;'
            )
            tag['class'] = []

    # 5. Style all tables
    for table in soup.find_all('table'):
        _inline_table(table)

    # 6. Style headings
    for level in range(1, 7):
        for h in soup.find_all(f'h{level}'):
            _inline_heading(h, level)

    # 7. Style lists
    _inline_lists(soup)

    # 8. Style paragraphs
    _inline_paragraphs(soup)

    # 9. Remove <span> with class text-danger that contain bullets (used for decoration)
    for span in soup.find_all('span', class_='text-danger'):
        text = span.get_text(strip=True)
        if text in ('•', '●', '•'):
            span.replace_with('• ')

    # 10. Clean up empty wrapper divs that serve no purpose in export
    for div in soup.find_all('div'):
        classes = div.get('class', [])
        # Keep alerts (already styled as tables for docx), remove decorative wrappers
        if 'sop-header-block' in classes:
            if is_docx:
                div.unwrap()
            else:
                # For PDF, keep the wrapper but style it nicely
                div['style'] = (
                    f'border:1px solid {_BLUE_ACCENT}; '
                    f'background-color:#f8fbff; border-radius:4px; '
                    f'margin-bottom:20px; padding:1px;' # 1px padding so table borders don't overlap
                )
        elif 'sop-content-formatted' in classes:
            div.unwrap()

    return str(soup)


def preprocess_html_for_pdf(html_content):
    """
    Variant for PDF export: same preprocessing but also wraps content
    in a properly styled container for xhtml2pdf.
    """
    return preprocess_html_for_export(html_content)


def preprocess_html_for_docx(html_content):
    """
    Variant for DOCX export: same preprocessing, plus additional
    tweaks for htmldocx compatibility.
    """
    if not html_content:
        return html_content

    processed = preprocess_html_for_export(html_content, is_docx=True)

    # Additional DOCX-specific: ensure tables have borders that Word likes
    # htmldocx often ignores css borders, so we try to be explicit
    soup = BeautifulSoup(processed, 'html.parser')
    
    for table in soup.find_all('table'):
        table['border'] = "1"
        table['cellspacing'] = "0"
        table['cellpadding'] = "5"

    for tag in soup.find_all(['td', 'th']):
        if 'colspan' in tag.attrs:
            del tag.attrs['colspan']
        if 'rowspan' in tag.attrs:
            del tag.attrs['rowspan']

    # Remove <style> blocks that htmldocx can't process
    for style_tag in soup.find_all('style'):
        style_tag.decompose()

    # Remove HTML entities that docx can't render (htmldocx chokes on some)
    result = str(soup)
    # Replace common HTML entities with plain text equivalents
    result = result.replace('&ge;', '≥')
    result = result.replace('&le;', '≤')
    result = result.replace('&lt;', '<')
    result = result.replace('&gt;', '>')
    result = result.replace('&rarr;', '→')
    result = result.replace('&larr;', '←')
    result = result.replace('&check;', '✓')
    result = result.replace('&bull;', '•')
    result = result.replace('&deg;', '°')
    result = result.replace('&nbsp;', ' ')

    return result
