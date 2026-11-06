"""Safety boundaries for derived hunting hints; python -m unittest discover."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from deed_locations import hunting_rule, enemy_index


class HuntingTests(unittest.TestCase):
    def objective(self):
        return {'Quest_CompletionConditionArray': [[{
            'QuestEvent_ID': 22, 'QuestEvent_Number': 30,
            'QuestEvent_MonsterGenus_Array': [{
                'Quest_MonsterRegion': 100, 'Quest_MonsterSpecies': 57}],
        }]]}

    def test_only_complete_supported_predicates(self):
        good = self.objective()
        self.assertEqual(hunting_rule(good), (100, 57))
        for field, value in [('QuestEvent_ID', 7),
                             ('QuestEvent_RoleConstraint', 'instance'),
                             ('QuestEvent_MonsterGenus_ExclusionArray', [{}]),
                             ('QuestEvent_WorldEvent', 42),
                             ('UnknownConstraint', 1)]:
            bad = copy.deepcopy(good)
            bad['Quest_CompletionConditionArray'][0][0][field] = value
            self.assertIsNone(hunting_rule(bad), field)
        bad = copy.deepcopy(good)
        bad['Quest_CompletionConditionArray'][0][0]['QuestEvent_MonsterGenus_Array'][0]['Quest_MonsterClass'] = 1
        self.assertIsNone(hunting_rule(bad))
        bad = copy.deepcopy(good)
        bad['Quest_CompletionConditionArray'][0].append({'QuestEvent_ID': 7})
        self.assertIsNone(hunting_rule(bad))

    def test_world_context_and_axis_order(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            placed, positions = folder / 'placed', folder / 'positions'
            placed.write_text(json.dumps({'id': '70000001', 'properties': {'Agent_Species': 57}}) + '\n')
            good = dict(did='70000001', layer=0, instance=0, cell='00000000',
                        region=1, block_x=2, block_y=3, latitude=-30, longitude=-55)
            rows = [good, good] + [dict(good, **change) for change in [
                {'layer': 1}, {'instance': 2}, {'cell': '00000002'},
                {'block_x': 4}, {'did': '70000002'}, {'latitude': 999}]]
            positions.write_text('\n'.join(json.dumps(r) for r in rows))
            calls = []
            def attribute(lat, lon, region):
                calls.append((lat, lon, region))
                return 123 if (lat, lon, region) == (-30, -55, 1) else None
            index = enemy_index(placed, positions, [{'id': '00000009', 'properties': {'Area_Territory': 100}}],
                                {('1', '2', '3'): '9'}, attribute)
            self.assertEqual(len(index[(100, 57)]), 1)
            point = index[(100, 57)][0]
            self.assertEqual((point['lat'], point['lon'], point['gm']), (-30, -55, 123))
            self.assertEqual(point['source'], 'dat-enemy-base-world')
            self.assertIn((-30, -55, 1), calls)


if __name__ == '__main__':
    unittest.main()
