#!/usr/bin/env python3
"""0.3.0 features against the real catalogue, headless (lupa, Lua 5.1):
filter, area search, level ranges, requirements, spoiler-free details, counters
from the import, area summary. Run with the plugin venv."""
import sys
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parent.parent / 'plugin' / 'MagicQuestLog'
lua = LuaRuntime(unpack_returned_tuples=True)
for name in ('Model.lua', 'Strings.lua', 'Data/Quests_de.lua', 'Data/Deeds_de.lua'):
    lua.execute((ROOT / name).read_text(encoding='utf-8'))
lua.execute("Turbine = {}; MagicQuestLog.Characters = nil")
lua.execute((ROOT / 'Characters.lua').read_text(encoding='utf-8'))

lua.execute(r'''
local M, S = MagicQuestLog.Model, MagicQuestLog.Strings.de
local quests, deeds = MagicQuestLog.Data.quests_de, MagicQuestLog.Data.deeds_de
local byId = {}
for _, r in ipairs(quests) do byId[r.id] = r end
-- A small progress set: the first required quest of some record is done.
local sample, need
for _, r in ipairs(quests) do
	if r.v ~= nil and #r.v == 1 and r.vb == nil and r.x == nil and byId[r.v[1]] ~= nil and r.vl == nil then sample, need = r, r.v[1]; break end
end
assert(sample ~= nil, "a quest with one plain requirement")
local completed = { [need] = true }
local all = M.Build(quests, "", S, completed, {}, { filter = "all", level = 150 })
local avail = M.Build(quests, "", S, completed, {}, { filter = "available", level = 150 })
assert(avail.total > 0 and avail.total < all.total, "available is a real subset")
assert(M.Available(sample, completed, 150), "requirement met -> available")
assert(not M.Available(sample, {}, 150), "requirement open -> not available")
local done = M.Build(quests, "", S, completed, {}, { filter = "done" })
assert(done.total == 1, "done shows exactly the finished entry, got " .. done.total)
-- Area search: the area name finds its entries.
local area = M.Build(quests, "Breeland", S, nil, {}, {})
local byName = M.Build(quests, "Abgetragen", S, nil, {}, {})
assert(area.total > 400, "area name finds the area's entries: " .. area.total)
assert(byName.total >= 2 and byName.total < 20, "a quest name still finds the quest")
-- Level range on areas, ~ on scaling ones.
local function find(node, name)
	for _, c in ipairs(node.order) do
		if c.name == name then return c end
		local hit = find(c, name); if hit then return hit end
	end
end
local bree = find(all, "Breeland")
assert(bree and bree.range and string.find(bree.range, "-"), "Breeland has a range: " .. tostring(bree and bree.range))
local scaling
for _, r in ipairs(quests) do if r.ls == 1 and r.l == 1 then scaling = r break end end
assert(M.LevelText(scaling) == "~", "scaling level reads ~")
-- Details: giver, requirement state, steps hidden by default.
local text = M.Detail(sample, S, {}, { completed = completed, byId = all.byId, level = 150 })
assert(string.find(text, S.requirements, 1, true), "requirements block")
assert(string.find(text, "(" .. S.reqdone .. ")", 1, true), "requirement state shown")
if sample.s and #sample.s > 0 then
	assert(not string.find(text, S.step .. " ", 1, true), "steps hidden by default")
	local open = M.Detail(sample, S, {}, { completed = completed, byId = all.byId, showSteps = true })
	assert(string.find(open, S.step .. " ", 1, true), "steps on request")
end
-- Counters from the import, matched by objective and condition number.
local running = MagicQuestLog.Characters.Running({ ["70000CFB"] = "1:0:1:1;2:0:0:44" })
local deed
for _, r in ipairs(deeds) do if r.id == "70000CFB" then deed = r end end
local deedText = M.Detail(deed, S, {}, { running = running["70000CFB"], deed = true })
assert(string.find(deedText, "[44/75", 1, true), "counter 44/75 in the deed text")
-- Area summary.
local summary = M.NodeSummary(bree, S, completed, 150, {})
assert(string.find(summary, S.available .. ":", 1, true), "summary lists available")
print("PASS: filter (" .. avail.total .. " available of " .. all.total .. "), area search, level range "
	.. bree.range .. ", requirements, spoiler-free details, counter 44/75, area summary")
''')
