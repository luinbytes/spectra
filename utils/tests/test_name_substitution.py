"""Check that shared translations keep the name appropriate to each message."""

import xml.etree.ElementTree as xml
from zlib import crc32

from .. import name_substitution_utils as names


def test_spectra_and_helium_can_share_a_translation(monkeypatch):
    """A Spectra title and another message can have identical source text."""

    def fingerprint(message):
        return str(crc32(''.join(message.itertext()).encode('utf-8')))

    monkeypatch.setattr(names, 'compute_fp', fingerprint)
    source = '''<grit><messages>
      <message name="IDS_BROWSER_WINDOW_TITLE_FORMAT"><ph name="PAGE">$1</ph> - Chromium</message>
      <message name="IDS_OTHER"><ph name="PAGE">$1</ph> - Chromium</message>
      <message name="IDS_CREDIT">The Helium Authors</message>
    </messages></grit>'''
    replaced, helium_ids, spectra_ids = names.replace_grit_tree(source)
    title, other, credit = xml.fromstring(replaced).findall('.//message')
    assert title.find('ph').tail == ' - Spectra'
    assert other.find('ph').tail == ' - Helium'
    assert credit.text == 'The Helium Authors'

    old_id = next(iter(helium_ids))
    translation = f'<translationbundle><translation id="{old_id}">ስለChromium : <ph name="PAGE"/>'
    translation += '</translation></translationbundle>'
    localized = names.replace_xtb_tree(translation, helium_ids, spectra_ids)
    translated = {node.get('id'): node for node in xml.fromstring(localized)}
    assert translated[helium_ids[old_id]].text == 'ስለHelium : '
    assert translated[spectra_ids[old_id]].text == 'ስለSpectra : '
    assert translated[spectra_ids[old_id]].find('ph').get('name') == 'PAGE'
