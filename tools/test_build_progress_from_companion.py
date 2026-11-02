"""Tests for the Companion status-file conversion. Runs without any game data."""
from pathlib import Path
import tempfile
import unittest

import build_progress_from_companion as converter


QUESTS = '''<?xml version="1.0" encoding="UTF-8"?>
<questsStatus>
	<questStatus key="70000006" state="COMPLETED" />
	<questStatus key="70017AEB" state="UNDEFINED" />
</questsStatus>
'''

DEEDS = '''<?xml version="1.0" encoding="UTF-8"?>
<deedsStatus>
	<deedStatus key="70000cff" state="COMPLETED" />
</deedsStatus>
'''


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.data = Path(self.temporary.name)
        self.character = self.data / 'characters' / 'ACCOUNT' / 'SERVER' / 'Feldobar'
        self.character.mkdir(parents=True)
        (self.character / 'questsStatus.xml').write_text(QUESTS, encoding='utf-8')
        (self.character / 'deedsStatus.xml').write_text(DEEDS, encoding='utf-8')

    def tearDown(self):
        self.temporary.cleanup()

    def test_finds_the_character(self):
        found = converter.find_characters(self.data)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['name'], 'Feldobar')
        self.assertEqual(found[0]['server'], 'SERVER')

    def test_lowercase_id_is_normalised(self):
        completed, states = converter.collect(converter.find_characters(self.data)[0])
        self.assertIn('70000CFF', completed)
        self.assertIn('70000CFF', states)

    def test_only_completed_counts(self):
        completed, states = converter.collect(converter.find_characters(self.data)[0])
        self.assertEqual(completed, {'70000006', '70000CFF'})
        self.assertEqual(states['70017AEB'], 'UNDEFINED')
        # The active entry must not be reported as finished.
        self.assertNotIn('70017AEB', completed)

    def test_render_is_valid_lua_shape(self):
        character = converter.find_characters(self.data)[0]
        completed, states = converter.collect(character)
        text, counts = converter.render(character, completed, states)
        self.assertTrue(text.startswith(converter.HEADER))
        self.assertIn('["completed"] = {', text)
        self.assertIn('\t\t["70000006"] = true,', text)
        self.assertIn('["character"] = "Feldobar"', text)
        self.assertEqual(counts['COMPLETED'], 2)
        self.assertEqual(text.count('["states"] = {'), 1)

    def test_missing_state_is_rejected(self):
        (self.character / 'deedsStatus.xml').write_text(
            '<deedsStatus><deedStatus key="70000CFF" completed="true"/></deedsStatus>',
            encoding='utf-8')
        character = converter.find_characters(self.data)[0]
        with self.assertRaises(ValueError):
            converter.collect(character)

    def test_bad_id_is_rejected(self):
        (self.character / 'questsStatus.xml').write_text(
            '<questsStatus><questStatus key="abc" state="COMPLETED"/></questsStatus>',
            encoding='utf-8')
        character = converter.find_characters(self.data)[0]
        with self.assertRaises(ValueError):
            converter.collect(character)

    def test_no_characters(self):
        empty = Path(self.temporary.name) / 'empty'
        empty.mkdir()
        self.assertEqual(converter.find_characters(empty), [])


if __name__ == '__main__':
    unittest.main()
