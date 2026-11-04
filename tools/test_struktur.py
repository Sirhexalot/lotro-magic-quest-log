#!/usr/bin/env python3
"""0.5.0 structure and detail loading, against the real catalogue (lupa, Lua 5.1).

Checks what the split catalog and the new tree order must guarantee:
- the core carries no description or steps, every entry names its detail block,
- a detail block is imported exactly once, a missing block is reported,
- the first level is the game's region order with "Weitere Inhalte" last,
- books sort numerically (roman and arabic), Prolog first, Epilog last.
"""
from pathlib import Path
import sys
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parent.parent / 'plugin' / 'MagicQuestLog'
DATA = ROOT / 'Data'

STUBS = r'''
Turbine = {};
Turbine.Engine = { GetGameTime = function() return 0 end };
Turbine.UI = { Orientation = { Vertical = 1 } };
Turbine.UI.Color = function(...) return { ... } end;
Turbine.Shell = { IsCommand = function() return false end, WriteLine = function() end };
Turbine.DataScope = { Character = 2, Server = 3 };
Turbine.PluginData = { Load = function() return nil end, Save = function() return true end };
imports = {};
function import(name) if string.find(name, "MagicQuestLog.Data.", 1, true) then imports[#imports + 1] = name; end end
'''


def main():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    for name in ('Model.lua', 'Strings.lua'):
        lua.execute((ROOT / name).read_text(encoding='utf-8'))
    lua.execute(r'''
local S = MagicQuestLog.Strings.de;
-- A small catalog in the shape the generator produces: core plus detail blocks.
local function core(id, path, sc, blk)
	return { id = id, name = "Test " .. id, p = path, l = "10", sc = sc, blk = blk };
end
local paths = {
	{ { k = "region:Eriador", n = "Eriador" }, { k = "zone:Breeland", n = "Breeland" } },
	{ { k = "section:more", n = "@more" }, { k = "section:story", n = "@story" },
	  { k = "volume:II", n = "@volume:II" }, { k = "category:1", n = "Buch 10: Ende" } },
	{ { k = "section:more", n = "@more" }, { k = "section:story", n = "@story" },
	  { k = "volume:II", n = "@volume:II" }, { k = "category:2", n = "Buch 9: Zurück" } },
	{ { k = "section:more", n = "@more" }, { k = "section:story", n = "@story" },
	  { k = "volume:I", n = "@volume:I" }, { k = "category:3", n = "Prolog: Anfang" } },
	{ { k = "section:more", n = "@more" }, { k = "section:story", n = "@story" },
	  { k = "volume:II", n = "@volume:II" }, { k = "category:4", n = "Epilog" } },
	{ { k = "region:Haradwaith", n = "Haradwaith" }, { k = "zone:Umbar", n = "Umbar" } },
	{ { k = "region:Mordor", n = "Mordor" }, { k = "zone:Gorgoroth", n = "Gorgoroth" } },
	{ { k = "section:more", n = "@more" }, { k = "section:festivals", n = "@festivals" } },
	{ { k = "region:Rhovanion", n = "Rhovanion" }, { k = "zone:Moria", n = "Moria" } },
};
local records = {};
for index, path in ipairs(paths) do records[index] = core(string.format("7000000%d", index), path, 1, 1); end
local root = MagicQuestLog.Model.Build(records, "", S, {}, {});
order = {};
for _, node in ipairs(root.order) do order[#order + 1] = node.name; end
local function children(id)
	for _, node in ipairs(root.order) do
		if node.name == id then
			local names = {};
			for _, child in ipairs(node.order) do names[#names + 1] = child.name; end
			return names;
		end
	end
	return {};
end
insideMore = children(S.more);
-- The epic story's list sections must order Prolog, Buch 9, Buch 10, Epilog.
local story = nil;
for _, node in ipairs(root.order) do
	if node.name == S.more then
		for _, child in ipairs(node.order) do if child.name == S.story then story = child; end end
	end
end
sections = {};
for _, record in ipairs(story.items) do sections[#sections + 1] = record.section; end
''')
    order = [str(value) for value in lua.eval('order').values()]
    inside = [str(value) for value in lua.eval('insideMore').values()]
    sections = [str(value) for value in lua.eval('sections').values()]
    print('PASS: first level: ' + ' · '.join(order))
    print('PASS: inside "Weitere Inhalte": ' + ' · '.join(inside))
    print('PASS: epic story sections: ' + ' · '.join(sections))
    expected = ['Eriador', 'Rhovanion', 'Mordor', 'Haradwaith', 'Weitere Inhalte']
    assert order == expected, order
    assert inside == ['Epische Geschichte', 'Feste und Ereignisse'], inside
    assert sections[0].startswith('Band I > Prolog'), sections
    assert 'Buch 9' in sections[1] and 'Buch 10' in sections[2], sections
    assert sections[3] == 'Band II > Epilog', sections
    print('PASS: region order follows the game, "Weitere Inhalte" last; books and '
          'chapters numeric, Prolog first, Epilog last')

    # Detail loading: once per block, honest when the block is missing.
    lua.execute(r'''
MagicQuestLog.Data = MagicQuestLog.Data or {};
local M = MagicQuestLog.Model;
local a = { id = "70000001", name = "A", blk = 1 };
local b = { id = "70000002", name = "B", blk = 1 };
MagicQuestLog.Data.questDetails_de_1 = {
	["70000001"] = { d = "Beschreibung A", s = { { i = "1", n = { "Zeile" }, g = {} } }, t = {} },
	["70000002"] = { d = "Beschreibung B", s = {}, t = {} },
};
MagicQuestLog.language = "de";
imports = {};
M.Details(a); M.Details(b); M.Details(a);
importCount = #imports;
loadedA = a.d;
loadedB = b.d;
local missing = { id = "70999999", name = "C", blk = 42 };
M.Details(missing);
missingFlag = missing.detailMissing == true and missing.d == nil;
noBlock = { id = "70000001", name = "D" };
M.Details(noBlock);
noBlockFlag = noBlock.detailMissing == nil and noBlock.d == nil;
''')
    assert lua.eval('importCount') == 1, 'one import per block, not per entry'
    assert lua.eval('loadedA') == 'Beschreibung A' and lua.eval('loadedB') == 'Beschreibung B'
    assert lua.eval('missingFlag') is True, 'a missing block must be reported, not shown as empty'
    assert lua.eval('noBlockFlag') is True
    print('PASS: details import once per block, are attached to the entry, and a '
          'missing block is reported')

    # The real catalog: core without description/steps, each entry with a block.
    lua.execute((DATA / 'Quests_de.lua').read_text(encoding='utf-8'))
    lua.execute(r'''
local quests = MagicQuestLog.Data.quests_de;
checked, withDetail, withBlock = 0, 0, 0;
for _, record in ipairs(quests) do
	checked = checked + 1;
	assert(record.d == nil, "description must not be in the core: " .. record.id);
	assert(record.s == nil, "steps must not be in the core: " .. record.id);
	assert(type(record.blk) == "number", "every entry needs a detail block: " .. record.id);
	withBlock = withBlock + 1;
	if (record.sc or 0) > 0 then withDetail = withDetail + 1; end
end
''')
    print('PASS: %s core entries carry no description or steps, all name their detail block '
          '(%s with steps)' % (lua.eval('checked'), lua.eval('withDetail')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
