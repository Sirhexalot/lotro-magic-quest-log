"""Conservative enemy-location hints from our own DAT exports, never exact goals.

Only a single, plain defeat event with territory + species is supported. More
complex predicates fail closed. Only the base world layer and outdoor cells are
used; map rectangles alone do not prove that a content-layer spawn is reachable.
"""
import json
from collections import defaultdict


PRESENTATION = {
    'Accomplishment_LoreInfo', 'QuestEvent_ProgressOverride',
    'QuestEvent_BillboardProgressOverride', 'QuestEvent_EventOrder',
    'QuestEvent_ShowBillboardText', 'QuestEvent_ShowProgressText',
    'QuestEvent_Number', 'QuestEvent_HideRadarIcon',
}


def hunting_rule(objective):
    if set(objective) - {'Quest_CompletionConditionArray', 'Quest_ObjectiveIndex',
                         'Quest_ObjectiveDescription', 'Quest_ObjectiveLoreOverride',
                         'Quest_ObjectiveProgressOverride', 'Quest_ObjectiveBillboardOverride'}:
        return None
    groups = objective.get('Quest_CompletionConditionArray') or []
    if not isinstance(groups, list) or len(groups) != 1 or not isinstance(groups[0], list) or len(groups[0]) != 1:
        return None
    event = groups[0][0]
    if not isinstance(event, dict) or event.get('QuestEvent_ID') != 22:
        return None
    if set(event) - PRESENTATION - {'QuestEvent_ID', 'QuestEvent_MonsterGenus_Array'}:
        return None
    rules = event.get('QuestEvent_MonsterGenus_Array') or []
    if not isinstance(rules, list) or len(rules) != 1 or not isinstance(rules[0], dict):
        return None
    rule = rules[0]
    if set(rule) != {'Quest_MonsterRegion', 'Quest_MonsterSpecies'}:
        return None
    territory, species = rule['Quest_MonsterRegion'], rule['Quest_MonsterSpecies']
    if not isinstance(territory, int) or not isinstance(species, int) or territory <= 0 or species <= 0:
        return None
    return territory, species


def enemy_index(placed_path, positions_path, areas, landblocks, attribute):
    """Index actual placements with provenance, not invented area centres/hulls."""
    species = {}
    with open(placed_path, encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            value = row.get('properties', {}).get('Agent_Species')
            if isinstance(value, int):
                species[row['id']] = value
    area_props = {int(row['id'], 16): row.get('properties', {}) for row in areas}
    index = defaultdict(dict)
    with open(positions_path, encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if (row.get('layer') != 0 or row.get('instance') != 0
                    or row.get('cell') != '00000000' or row['did'] not in species):
                continue
            block = tuple(str(row[key]) for key in ('region', 'block_x', 'block_y'))
            area = landblocks.get(block)
            if area is None:
                continue
            area = int(area)
            territory = area_props.get(area, {}).get('Area_Territory', area)
            lat, lon = row['latitude'], row['longitude']
            map_id = attribute(lat, lon, row['region'])
            if map_id is None:
                continue
            # Keep the actual precision; deduplicate duplicate geo records only.
            key = (map_id, lat, lon, row['did'])
            index[(territory, species[row['did']])][key] = {
                'gm': map_id, 'lat': lat, 'lon': lon, 'did': row['did'],
                'territory': territory, 'species': species[row['did']],
                'source': 'dat-enemy-base-world',
            }
    return {rule: [points[key] for key in sorted(points)] for rule, points in index.items()}
