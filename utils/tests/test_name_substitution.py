"""Check that shared translations keep the name appropriate to each message."""

import xml.etree.ElementTree as xml
from zlib import crc32

from .. import i18n_apply
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


def test_linux_missing_desktop_translation_keeps_both_product_names(monkeypatch, tmp_path):
    """The Spectra GRIT message can use the existing Helium translation."""
    monkeypatch.setattr(i18n_apply.namesub, 'compute_fp',
                        lambda message: str(crc32(''.join(message.itertext()).encode('utf-8'))))
    name = 'IDS_SETTINGS_DEFAULT_BROWSER_SECONDARY'
    source = 'Helium cannot be set as default without <ph name="DESKTOP_FILENAME">$1</ph>.'
    translated = 'Impossible de définir Helium par défaut sans <ph name="DESKTOP_FILENAME">$1</ph>.'
    xtb = tmp_path / 'strings.xtb'
    xtb.write_text('<translationbundle/>', encoding='utf-8')

    i18n_apply.merge_into_xtb(xtb, [{
        'name': name,
        'context': '',
        'message': source
    }], {(name, source): {
             'message': translated
         }})

    entries = {entry.get('id'): entry for entry in xml.parse(xtb).getroot()}
    for brand in ('Helium', 'Spectra'):
        message_id = i18n_apply.get_id(name, '', source.replace('Helium', brand), None)
        entry = entries[message_id]
        assert entry.text == f'Impossible de définir {brand} par défaut sans '
        assert entry.find('ph').get('name') == 'DESKTOP_FILENAME'


def test_spectra_product_name_respects_attached_locale_endings():
    """Keep the localized case ending when the product name changes."""
    text = 'Heliumit / Heliumia / Helium을 / Heliumను / Helium / HeliumBrowser'
    expected = 'Spectrat / Spectraa / Spectra를 / Spectraను / Spectra / HeliumBrowser'
    assert names.replace_spectra_text(text) == expected
