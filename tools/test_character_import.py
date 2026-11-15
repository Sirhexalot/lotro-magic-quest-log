"""Focused Lua 5.1 regressions for website imports; no game files are written."""
from pathlib import Path
import json
import subprocess
from lupa.lua51 import LuaRuntime

PLUGIN = Path(__file__).resolve().parents[1] / 'plugin' / 'MagicQuestLog'
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
Turbine = { DataScope = { Server = 3, Character = 2 } };
stored = {};
Turbine.PluginData = {
    Load = function(scope, key) return stored[key]; end,
    Save = function(scope, key, value) stored[key] = value; end,
};
''')
lua.execute((PLUGIN / 'Characters.lua').read_text(encoding='utf-8'))
# Exercise the actual website writer, not only hand-written Lua fixtures.
converter = PLUGIN.parents[2] / 'lotro-log-book' / 'web' / 'companion.js'
files = json.loads(subprocess.check_output(['node', '-e', '''
const C = require(process.argv[1]);
console.log(JSON.stringify(C.pluginFiles(['Éowyn', 'Frödo', 'François', 'Łukasz'].map(name => ({
    name, account: 'TestAccount', server: 'TestServer', date: '2026-11-07',
    level: '123', quests: ['70000006'], deeds: [], laufend: {}
})))));
''', str(converter)], text=True))
assert len(files) == 5, 'website must write four imports and their index'
for file in files:
    key = Path(file['path']).stem
    lua.globals().stored[key] = lua.execute(file['text'])
for name in ('Éowyn', 'Frödo', 'François', 'Łukasz'):
    imported = lua.globals().MagicQuestLog.Characters.LoadImport(name)
    assert imported is not None and imported.completed['70000006'], name
lua.execute('''
local C = MagicQuestLog.Characters;
for _, name in ipairs({"Feldobar", "Éowyn", "Frödo", "François", "Łukasz"}) do
    assert(C.ValidName(name), "valid character rejected: " .. name);
end
for _, name in ipairs({"", "bad name", "../Feldobar", "a/b", "a\\\\b", "a.b", "a:foo", "a1", "×", "÷"}) do
    assert(not C.ValidName(name), "unsafe name accepted: " .. name);
end
stored.MagicQuestLog_Characters = { ["Éowyn"] = true, ["Frödo"] = true };
stored["MagicQuestLog_Import_Éowyn"] = {
    character = "Éowyn", completed = { ["70000006"] = true },
    running = {}, date = "2026-11-07", level = "123",
};
local names = C.List("Éowyn");
assert(#names == 2, "accented names lost from character switch");
local progress, exact = C.Progress("Éowyn");
assert(exact and progress["70000006"], "accented character's import was lost");
assert(stored.MagicQuestLog_Characters["Frödo"], "character index overwritten");
stored.MagicQuestLog_Import_Newcomer = {
    character = "Newcomer", completed = {}, running = {}, level = "1",
};
local empty = C.LoadImport("Newcomer");
assert(empty and empty.count == 0, "valid empty import treated as missing");
assert(C.LoadImport("Missing") == nil, "missing import must stay missing");
stored.MagicQuestLog_Import_Wrong = { character = "Someoneelse", completed = {} };
assert(C.LoadImport("Wrong") == nil, "other character accepted");
stored.MagicQuestLog_Import_Broken = { character = "Broken" };
assert(C.LoadImport("Broken") == nil, "malformed import accepted");
''')
print('PASS: accented names, character index, progress, empty and missing imports')
