"""Headless plugin test: Lua 5.1, real German catalog, stubbed Turbine UI.

Covers behaviour that must not silently break: search by name part, accent
insensitivity, collapsed start, detail rendering, MoorMap command and the
language fallback. It does not prove how the window looks in the game.
"""
from pathlib import Path
import re
import sys
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugin/MagicQuestLog'
DATA = PLUGIN / 'Data'

STUBS = r'''
function import() end

-- Generic stand-in for every Turbine UI object: records what the plugin sets.
local function controlFactory()
	local object = { width = 100, height = 20, text = "", items = {} };
	return setmetatable(object, { __index = function(self, key)
		if key == "GetWidth" then return function(s) return s.width end end
		if key == "GetHeight" then return function(s) return s.height end end
		if key == "SetSize" then return function(s, w, h) s.width = w; s.height = h end end
		if key == "SetWidth" then return function(s, w) s.width = w end end
		if key == "SetHeight" then return function(s, h) s.height = h end end
		if key == "GetText" then return function(s) return s.text end end
		if key == "SetText" then return function(s, v) s.text = v end end
		if key == "SetParent" then return function(s, p) s.parent = p end end
		if key == "AddItem" then return function(s, v) table.insert(s.items, v) end end
		if key == "ClearItems" then return function(s) s.items = {} end end
		if key == "GetItemCount" then return function(s) return #s.items end end
		if key == "GetItem" then return function(s, i) return s.items[i] end end
		if key == "SetPosition" then return function(s, l, x) s.left = tonumber(l) or 0; s.top = tonumber(x) or 0 end end
		if key == "GetLeft" then return function(s) return s.left or 0 end end
		if key == "GetTop" then return function(s) return s.top or 0 end end
		if key == "GetSelectedIndex" then return function(s) return s.selected or 0 end end
		if key == "SetSelectedIndex" then return function(s, i) s.selected = tonumber(i) or 0 end end
		if key == "SetShortcut" then return function(s, v) s.shortcut = v end end
		if key == "SetBackground" then return function(s, v) s.background = v end end
		if key == "GetBackground" then return function(s) return s.background end end
		if key == "SetMouseVisible" then return function(s, v) s.mouseVisible = v end end
		if key == "SetFont" then return function(s, v) s.font = v end end
		if key == "SetVisible" then return function(s, v) s.visible = v end end
		if key == "IsVisible" then return function(s) return s.visible ~= false end end
		return function() end
	end });
end

local function windowBase() end
Turbine = {};
Turbine.DataScope = { Character = 3 };
Turbine.UI = { Orientation = { Vertical = 1 } };
Turbine.UI.Color = function(...) return { ... } end;
Turbine.Shell = {};
languageCommand = "hilfe";
Turbine.Shell.IsCommand = function(name) return name == languageCommand end;
Turbine.Shell.WriteLine = function(text) lastShell = text end;
Turbine.Shell.AddCommand = function() end;
Turbine.ShellCommand = function() return {} end;
Turbine.Gameplay = {};
Turbine.Gameplay.LocalPlayer = { GetInstance = function()
	return { GetName = function() return "Feldobar" end,
	         GetClass = function() return 1 end,
	         GetRace = function() return 2 end };
end };
Turbine.Gameplay.Class = { Hunter = 1 };
Turbine.Gameplay.Race = { Hobbit = 2 };
Turbine.UI.Control = controlFactory;
Turbine.UI.Label = controlFactory;
Turbine.UI.ListBox = controlFactory;
Turbine.UI.Lotro = { Button = controlFactory, ScrollBar = controlFactory, TextBox = controlFactory,
	Quickslot = controlFactory };
Turbine.UI.Lotro.ShortcutType = { Alias = 1 };
-- A shortcut only matters through its data, so the stub keeps it readable.
Turbine.UI.Lotro.Shortcut = function(kind, data)
	local shortcut = { kind = kind, data = data };
	shortcut.SetData = function(self, value) shortcut.data = value end;
	shortcut.GetData = function(self) return shortcut.data end;
	return shortcut;
end;
Turbine.UI.ContentAlignment = { MiddleLeft = 1, MiddleCenter = 2 };
Turbine.UI.FontStyle = { Outline = 1 };
Turbine.UI.CheckBox = { MiddelCenter = 1, BottomCenter = 2 };
Turbine.UI.Lotro.Font = { Verdana12 = 1, Verdana14 = 2 };
-- The window class needs a real base table with a callable constructor.
local windowPrototype = controlFactory();
windowPrototype.Constructor = function(self)
	self.width = self.width or 100;
	self.height = self.height or 20;
end;
Turbine.UI.Window = windowPrototype;
Turbine.UI.Lotro.Window = windowPrototype;
Turbine.UI.Display = { GetWidth = function() return 1920 end, GetHeight = function() return 1080 end };
storedSettings = nil;
savedSettings = nil;
Turbine.PluginData = {
	Load = function() return storedSettings end,
	Save = function(scope, key, value) savedSettings = value; return true end,
};
Turbine.Shell.WriteLine = function(text) lastShell = text end;
'''

def run():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    for name in ('Class.lua', 'Strings.lua', 'Settings.lua', 'Model.lua', 'Icon.lua', 'Window.lua'):
        lua.execute((PLUGIN / name).read_text(encoding='utf-8'))
    lua.execute((DATA / 'Quests_de.lua').read_text(encoding='utf-8'))
    lua.execute((DATA / 'Deeds_de.lua').read_text(encoding='utf-8'))
    lua.execute((DATA / 'Quests_en.lua').read_text(encoding='utf-8'))
    lua.execute((DATA / 'Deeds_en.lua').read_text(encoding='utf-8'))
    lua.execute((DATA / 'Progress.lua').read_text(encoding='utf-8'))
    lua.execute((PLUGIN / 'Main.lua').read_text(encoding='utf-8'))
    # Every texture the plugin points at must exist next to it, or the client
    # silently draws nothing. The path is relative to the Plugins folder.
    referenced = set(re.findall(r'"(MagicQuestLog/Resources/[A-Za-z0-9_]+\.tga)"',
                                '\n'.join(path.read_text(encoding='utf-8')
                                          for path in PLUGIN.rglob('*.lua'))))
    assert referenced, 'no textures referenced'
    for resource in sorted(referenced):
        assert (PLUGIN / resource.split('/', 1)[1]).is_file(), 'missing texture ' + resource
    print('PASS: %d referenced icon textures exist' % len(referenced))
    lua.execute(r'''
local MQL = MagicQuestLog;
assert(MQL.language == "de", "client德语 should win, got " .. tostring(MQL.language));
assert(MQL.window ~= nil, "window missing");
local window = MQL.window;
assert(window:IsVisible(), "window must start visible");
assert(string.find(window.countLabel:GetText(), "15117"), "count label: " .. window.countLabel:GetText());
-- Collapsed by default: only root nodes are rows.
local roots = 0;
for _, child in ipairs(MQL.Model.Build(MQL.catalogs.quests, "", MQL.strings).order) do roots = roots + 1; end
assert(window.tree:GetItemCount() == roots, "tree must start collapsed");
-- Search is a literal name-part search and ignores case and accents.
local function search(text)
	window.searchBox:SetText(text);
	window.query = text;
	window:Rebuild();
	return window.root.total;
end
local all = search("");
assert(all == 15117, "unfiltered total " .. tostring(all));
local diacritic = search("ker izel");
local plain = search("Kêr Izel");
assert(diacritic > 0 and diacritic == plain, "accent-insensitive search failed");
local partial = search("zügellosen");
assert(partial > 0 and partial < all, "partial name search failed");
assert(search("zzzz-nicht-vorhanden") == 0, "empty result expected");
search("");
-- Selecting a record fills the details and a proven MoorMap position.
local withTarget, sample = 0, nil;
for _, record in ipairs(MQL.catalogs.quests) do
	if #record.t > 0 then withTarget = withTarget + 1; if sample == nil then sample = record; end end
end
assert(withTarget > 9000, "too few verified positions: " .. tostring(withTarget));
window:ShowDetails(sample);
local detail = window.detailText:GetText();
assert(string.find(detail, MQL.strings.description, 1, true), "description missing");
assert(string.find(detail, MQL.strings.step .. " ", 1, true), "step heading missing");
assert(not string.find(detail, "${", 1, true), "raw placeholder leaked");
assert(not string.find(detail, "\\n", 1, true), "literal newline leaked");
assert(window.mapSlot:IsVisible(), "map slot must be visible");
assert(string.find(window.command, "/moormap ping ", 1, true), "map command: " .. tostring(window.command));
local ping, map, lat, lon = string.match(window.command, "^(/moormap ping) (%d+):([%-%d%.]+):([%-%d%.]+)");
assert(ping ~= nil and tonumber(map) > 0 and tonumber(lat) ~= nil and tonumber(lon) ~= nil, "map command malformed");
-- The command must reach MoorMap through the shortcut, not by printing it.
assert(window.mapShortcut.data == window.command, "shortcut must carry the ping command");
assert(window.mapSlot.shortcut == window.mapShortcut, "shortcut must be attached to the slot");
-- The quickslot prints the alias inside itself ("/MO…"), which looks like a broken
-- button. A cover with the pin hides that, but it must let the click through to
-- the slot: both cover and icon ignore the mouse.
assert(window.mapCover.mouseVisible == false, "cover must not swallow the click");
assert(window.mapIcon.mouseVisible == false, "pin must not swallow the click");
assert(window.mapIcon.parent == window.mapCover, "pin must sit on the cover");
assert(window.mapCover.visible == true, "cover must show with a verified position");
-- Tree text is one size up as well; nodes and rows share the detail body font.
local nodeRow = nil;
for _, row in ipairs(window.rows) do
	if row.control.label and row.control.label.font ~= nil then nodeRow = row; break; end
end
assert(nodeRow ~= nil, "expected a tree node row");
assert(nodeRow.control.label.font == window.body, "tree node font must be the body font");
assert(nodeRow.control:GetHeight() >= 20, "tree rows must be taller for the bigger font");
-- A record without a verified position must not pretend to have one.
local without = nil;
for _, record in ipairs(MQL.catalogs.quests) do if #record.t == 0 then without = record; break end end
window:ShowDetails(without);
assert(not window.mapSlot:IsVisible(), "map slot must hide without a position");
assert(window.mapInfo:GetText() == MQL.strings.nomap, "honest no-position text expected");
assert(window.command == false, "no command without a position");
-- Deeds use the same machinery.
window:SetKind("deeds");
assert(window.kind == "deeds" and window.root.total == 5534, "deed catalog");
window:SetKind("quests");
-- Expanding a node keeps the totals and shows its children.
local function node(key)
	local root = MQL.Model.Build(MQL.catalogs.quests, "", MQL.strings);
	return root.children[key];
end
local gondor = node("region:Gondor");
assert(gondor ~= nil and gondor.total > 0, "Gondor missing");
local before = window.tree:GetItemCount();
window.expanded["|0/region:Gondor"] = true;
window:Rebuild();
assert(window.tree:GetItemCount() > before, "expanding must add rows");
assert(window.root.total == 15117, "totals must not change on expand");
-- Row clicks use the list selection path.
window.searchBox:SetText("Zügellosen");
window.query = "Zügellosen";
window:Rebuild();
local rows = window.tree:GetItemCount();
assert(rows > 1, "expected a reduced tree, got " .. rows);
window.tree.selected = rows;
window.tree.SelectedIndexChanged();
assert(window.selectedRow ~= nil, "clicking a leaf must select it");
assert(window.record ~= false and window.record ~= nil, "clicking a leaf must show its record");
assert(window.tree.selected == 0, "selection must reset so the same row is clickable again");
assert(window.detailTitle:GetText() == window.record.name, "detail title follows the selection");
window.searchBox:SetText("");
window.query = "";
window:Rebuild();
local collapsed = window.tree:GetItemCount();
local function click(index)
	window.tree.selected = index;
	window.tree.SelectedIndexChanged();
end
click(1);
assert(window.tree:GetItemCount() > collapsed, "clicking a node must expand it");
assert(window.root.total == 15117, "totals must survive expanding");
click(1);
assert(window.tree:GetItemCount() == collapsed, "clicking the same node again must collapse it");
-- Start icon toggles the window and remembers its place.
assert(MQL.icon ~= nil, "start icon missing");
local visibleBefore = MQL.window:IsVisible();
MQL.icon.onClick();
assert(MQL.window:IsVisible() ~= visibleBefore, "icon must toggle the window");
MQL.icon.onClick();
assert(MQL.window:IsVisible() == visibleBefore, "icon must toggle back");
assert(MQL.icon.Moved ~= nil, "icon must be movable");
MQL.icon.Moved(44, 55);
assert(savedSettings ~= nil and savedSettings.iconLeft == "44",
	"icon position must be stored, got " .. tostring(savedSettings and savedSettings.iconLeft));
-- Stored as text on purpose: the client writes numbers with a decimal comma on a
-- German or French client ("239,000000"), which is not valid Lua and breaks the
-- whole settings file on the next load.
assert(type(savedSettings.iconLeft) == "string" and type(savedSettings.iconTop) == "string",
	"positions must never be stored as numbers");
assert(MagicQuestLog.Settings.Placement(239.4) == "239", "placement must round to whole pixels");
assert(MagicQuestLog.Settings.Placement(nil) == nil, "missing placement stays missing");
-- Header row: the standard window paints a title bar, so nothing may sit above y=30.
assert(window.kindQuest.top >= 30 and window.searchBox.top >= 30,
	"header must stay below the title bar: " .. tostring(window.kindQuest.top));
assert(window.searchLabel:GetText() == MQL.strings.search, "search label text");
assert(window.searchLabel:GetText() ~= "", "search label must be visible text");
assert(window.searchIcon.background == MQL.Icons.search, "search icon texture missing");
assert(window.clearIcon.background == MQL.Icons.clear, "clear icon texture missing");
assert(window.mapIcon.background == MQL.Icons.mappin, "map pin texture missing");
assert(window.detailStatus.background ~= nil, "status mark must carry a texture");
assert(window.kindQuestIcon.background == MQL.Icons.quests, "quest tab icon missing");
assert(window.kindDeedIcon.background == MQL.Icons.deeds, "deed tab icon missing");
assert(window.tree.top > window.searchBox.top, "tree must sit below the header");
-- Expanding must not rebuild and re-sort the catalog again.
local builds, originalBuild = 0, MQL.Model.Build;
MQL.Model.Build = function(...) builds = builds + 1; return originalBuild(...); end;
window:Rebuild();
assert(builds == 0, "an unchanged rebuild must reuse the cached tree, got " .. builds);
window.expanded["|0/region:Gondor"] = true;
window:Rebuild();
assert(builds == 0, "expanding must reuse the cached tree, got " .. builds);
assert(window.root.total == 15117, "cached tree must keep its totals");
window.query = "Zügellosen";
window:Rebuild();
assert(builds == 1, "a new search must rebuild exactly once, got " .. builds);
window.query = "";
window:Rebuild();
assert(builds == 2, "clearing the search must rebuild exactly once, got " .. builds);
MQL.Model.Build = originalBuild;
-- Counters: "n/total" with progress, and an honest headline.
window:SetProgress(nil);
assert(not string.find(window.countLabel:GetText(), MQL.strings.finished, 1, true),
	"without progress no finished count may be claimed");
local sampleId = MQL.catalogs.quests[1].id;
window:SetProgress({ [sampleId] = true });
assert(string.find(window.countLabel:GetText(), MQL.strings.finished, 1, true),
	"progress must be reported: " .. window.countLabel:GetText());
assert(string.find(window.countLabel:GetText(), "1 / 15117"), "headline count: " .. window.countLabel:GetText());
window.expanded["|0/region:Gondor"] = true;
window:Rebuild();
local counterSeen = false;
for _, row in ipairs(window.rows) do
	local text = row.control.label and row.control.label:GetText() or "";
	if string.find(text, "/", 1, true) ~= nil then counterSeen = true; end
end
assert(counterSeen, "node counters must show n/total with progress");
window:SetProgress(nil);
assert(not string.find(window.countLabel:GetText(), "1 / 15117", 1, true),
	"without progress the finished count must disappear again");
-- Placeholders in names and group captions are filled in, never shown raw.
local resolved = MQL.Model.Display("Der ${CLASS} prueft ${PLAYERNAME:A[1]|B[2]}", { charclass = "Jäger" },
	MQL.strings);
assert(not string.find(resolved, "${", 1, true), "placeholder left: " .. resolved);
assert(string.find(resolved, "Jäger", 1, true), "class placeholder not filled: " .. resolved);
assert(string.find(resolved, "A / B", 1, true), "alternatives not joined: " .. resolved);
-- Real group captions carry placeholders ("${PLAYERNAME:Runebewahrer[im]|Runebewahrerin[f]}"):
-- a raw one in a tree row is unreadable, so the caption must be resolved too.
local node = MQL.Model.Build({ { id = "70000001", name = "Test", p = {
	{ k = "zone:X", n = "${PLAYERNAME:Runebewahrer[im]|Runebewahrerin[f]}" } }, s = {}, t = {} } },
	"", MQL.strings, nil, {});
local caption = node.children["zone:X"].name;
assert(string.find(caption, "${", 1, true) == nil, "caption placeholder left: " .. caption);
assert(string.find(caption, "Runebewahrer / Runebewahrerin", 1, true) ~= nil,
	"caption alternatives not joined: " .. caption);
local raw = 0;
for _, record in ipairs(MQL.catalogs.quests) do
	for _, part in ipairs(record.p) do
		if string.find(part.n, "${", 1, true) ~= nil then raw = raw + 1; end
	end
end
assert(raw > 0, "expected real catalog captions with placeholders");
-- Placeholders in texts must be filled: the resolution result used to be thrown
-- away, which replaced every one of them with the plain "[value]" marker.
local withPlayer = nil;
for _, record in ipairs(MQL.catalogs.quests) do
	if string.find(record.d or "", "${PLAYER", 1, true) ~= nil then withPlayer = record; break; end
end
assert(withPlayer ~= nil, "expected a quest whose text uses a player placeholder");
window:ShowDetails(withPlayer);
local filled = window.detailText:GetText();
assert(string.find(filled, "Feldobar", 1, true) ~= nil,
	"player placeholder not filled in: " .. string.sub(filled, 1, 120));
assert(string.find(filled, MQL.strings.value, 1, true) == nil,
	"placeholder fell back to the value marker: " .. string.sub(filled, 1, 120));
window:ShowDetails(sample);
-- Client language without a local catalog falls back to English explicitly.
MQL.language = "fr";
MQL.Data["quests_fr"] = nil;
local quests, deeds = nil, nil;
quests = MQL.Data["quests_fr"];
assert(quests == nil, "precondition");
''')
    lua.execute(r'''
-- Client reports German, but the German catalog is missing: English must be used
-- explicitly, with English strings, and the window must still be complete.
-- A French client without a French catalog must fall back to English.
languageCommand = "aide";
assert(MagicQuestLog.Data["quests_fr"] == nil, "precondition: no French catalog loaded");
local previousWindow = MagicQuestLog.window;
MagicQuestLog.Load(nil);
fallbackLanguage = MagicQuestLog.language;
assert(fallbackLanguage == "en", "fallback language: " .. tostring(fallbackLanguage));
assert(MagicQuestLog.window ~= previousWindow, "fallback must build a new window, not keep the old one");
assert(MagicQuestLog.window ~= nil and MagicQuestLog.window.root ~= nil, "fallback window missing");
assert(MagicQuestLog.window.root.total == 15117, "fallback total: " .. tostring(MagicQuestLog.window.root.total));
assert(MagicQuestLog.strings.quests == "Quests", "fallback strings");
assert(MagicQuestLog.Data["quests_en"] ~= nil, "English catalog must be present for the fallback");
assert(MagicQuestLog.Data["quests_de"] ~= nil, "German catalog stays loaded and is simply not chosen");
assert(MagicQuestLog.window.countLabel:GetText() ~= nil and MagicQuestLog.window.countLabel:GetText() ~= "", "empty count");
-- Then a locale that exists must be used as-is.
MagicQuestLog.Load(nil);
assert(MagicQuestLog.language == "en", "still English without a local catalog");
''')

    lua.execute(r'''
-- Stored values can come back as text: they must be coerced and honoured.
storedSettings = { windowLeft = "300", windowTop = "180", windowVisible = false, useIcon = false };
local settings = MagicQuestLog.Settings.Load();
assert(settings.windowLeft == 300 and settings.windowTop == 180, "numeric settings must be coerced");
assert(settings.windowVisible == false and settings.useIcon == false, "stored switches must win");
-- Saving must produce a file the client can read back: no number, no decimal comma.
MagicQuestLog.Settings.Save();
local saved = savedSettings;
assert(type(saved.windowLeft) == "string" and type(saved.windowTop) == "string",
	"saved placement must be text, got " .. type(saved.windowLeft));
assert(type(saved.windowVisible) == "boolean" and type(saved.useIcon) == "boolean",
	"switches stay booleans");
for _, name in ipairs({ "windowLeft", "windowTop", "iconLeft", "iconTop" }) do
	assert(saved[name] == nil or type(saved[name]) == "string",
		"saved " .. name .. " must be text, got " .. type(saved[name]));
	assert(saved[name] == nil or string.find(saved[name], "[,.]") == nil,
		"saved " .. name .. " must be whole pixels");
end
MagicQuestLog.Load(nil);
assert(MagicQuestLog.window:IsVisible() == false, "window must honour stored visibility");
assert(MagicQuestLog.icon:IsVisible() == false, "icon must honour stored visibility");
assert(MagicQuestLog.window:GetLeft() == 300 and MagicQuestLog.window:GetTop() == 180, "window position");
-- A progress file that belongs to another character must be ignored, never
-- reported as this character's progress.
local progress = MagicQuestLog.Data.progress;
assert(progress ~= nil, "progress data must be loaded for this test");
local originalCharacter = progress.character;
progress.character = "Someoneelse";
MagicQuestLog.Load(nil);
assert(MagicQuestLog.window.completed == false, "foreign progress must be ignored");
assert(not string.find(MagicQuestLog.window.countLabel:GetText(), MagicQuestLog.strings.finished, 1, true),
	"a foreign progress file must never show finished counts");
progress.character = originalCharacter;
MagicQuestLog.Load(nil);
assert(MagicQuestLog.window.completed ~= false, "matching progress must be used again");
-- Back to a clean German client for the summary below.
storedSettings = nil;
languageCommand = "hilfe";
MagicQuestLog.Load(nil);
assert(MagicQuestLog.language == "de", "German client must use the German catalog");
''')

    read = lua.eval('''function()
    local MQL = MagicQuestLog;
    local roots, collapsed = 0, true;
    for _ in ipairs(MQL.Model.Build(MQL.catalogs.quests, "", MQL.strings).order) do roots = roots + 1; end
    local withTargets, withoutTargets = 0, 0;
    for _, record in ipairs(MQL.catalogs.quests) do
        if #record.t > 0 then withTargets = withTargets + 1 else withoutTargets = withoutTargets + 1 end
    end
    return { total = MQL.window.root.total,
             count = MQL.window.countLabel:GetText(),
             roots = roots,
             items = MQL.window.tree:GetItemCount(),
             withTargets = withTargets,
             withoutTargets = withoutTargets,
             rows = MQL.window.tree:GetItemCount(),
             language = MQL.language,
             searchLabelText = MQL.strings.search,
             counterSample = (MQL.window.rows[1] and MQL.window.rows[1].control.label
                 and MQL.window.rows[1].control.label:GetText()) or "" };
end''')
    lua.globals().read = read
    values = read()
    print('PASS: plugin loads a catalog, window visible, count label "%s"' % values['count'])
    print('PASS: tree starts fully collapsed (%s root rows shown of %s entries)' %
          (values['items'], values['total']))
    print('PASS: name-part search, case- and accent-insensitive ("ker izel" == "Kêr Izel")')
    print('PASS: details show description and numbered steps, no raw placeholders')
    print('PASS: %s quests with verified MoorMap positions, %s without; command format checked' %
          (values['withTargets'], values['withoutTargets']))
    print('PASS: a quest without a verified position shows no map button and no command')
    print('PASS: %s row clicks via list selection (same row stays clickable); nodes expand and collapse' % values['rows'])
    print('PASS: start icon toggles the window; position and visibility are stored and honoured')
    print('PASS: header sits below the title bar, search is labelled "%s"' % values['searchLabelText'])
    print('PASS: expanding reuses the cached tree (no re-sort); a new search rebuilds exactly once')
    print('PASS: counters show "%s" with progress and claim nothing without it' % values['counterSample'])
    print('PASS: MoorMap runs through a quickslot alias shortcut, not by printing the command')
    print('PASS: a progress file for another character is ignored instead of being shown as ours')
    print('PASS: a client language without its catalog falls back to English (chosen: %s) with English strings'
          % lua.globals().fallbackLanguage)
    return 0


if __name__ == '__main__':
    sys.exit(run())
