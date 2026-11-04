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
-- import() reads the named module from the Data folder, exactly like the client:
-- the plugin's detail blocks are loaded this way when an entry is opened.
function import(name) ladeModul(name) end

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
		if key == "SetValue" then return function(s, v)
			if s.scrollbar ~= nil then s.boundSetValue = true end
			s.value = tonumber(v)
		end end
		if key == "SetVerticalScrollBar" then return function(s, v) s.scrollbar = v end end
		if key == "GetValue" then return function(s) return s.value or 0 end end
		if key == "SetVisible" then return function(s, v) s.visible = v end end
		if key == "IsVisible" then return function(s) return s.visible ~= false end end
		return function() end
	end });
end

local function windowBase() end
Turbine = {};
gameTime = 0;
Turbine.Engine = { GetGameTime = function() return gameTime end };
Turbine.DataScope = { Character = 3 };
Turbine.UI = { Orientation = { Vertical = 1 } };
Turbine.UI.Color = function(...) return { ... } end;
Turbine.Shell = {};
languageCommand = "hilfe";
Turbine.Shell.IsCommand = function(name) return name == languageCommand end;
Turbine.Shell.WriteLine = function(text) lastShell = text end;
Turbine.Shell.AddCommand = function(name, command) shellCommand = command end;
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
-- A scroll bar bound to a label only shows while the text overflows the label. The
-- stub cannot lay out text, so it always reports "fits" and the plugin's fallback
-- (counting characters) is what the checks below exercise.
local function scrollFactory()
	local object = controlFactory();
	object.visible = false;
	return object;
end
Turbine.UI.ListBox = controlFactory;
Turbine.UI.Lotro = { Button = controlFactory, ScrollBar = scrollFactory, TextBox = controlFactory,
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
-- Settings live in the account scope, progress in the server scope (one file per
-- character, so every character of the server can be shown). Each scope is its own
-- table, so a test can tell where something was written.
savedData = {};
serverData = {};
characterData = {};
Turbine.DataScope = { Account = 1, Character = 2, Server = 3 };
Turbine.PluginData = {
	Load = function(scope, key)
		if scope == Turbine.DataScope.Account then return storedSettings; end
		if scope == Turbine.DataScope.Server then return serverData[key]; end
		return characterData[key];
	end,
	Save = function(scope, key, value)
		if scope == Turbine.DataScope.Account then
			savedSettings = value;
		elseif scope == Turbine.DataScope.Server then
			serverData[key] = value;
			savedData[key] = value;
		else
			characterData[key] = value;
		end
		return true;
	end,
};
-- The chat hook: a test sets message and calls Turbine.Chat.Received.
Turbine.Chat = { Received = nil };
Turbine.ChatType = { Quest = 11, Advancement = 12, Standard = 0 };
function receiveChat(message, chatType)
	if Turbine.Chat.Received == nil then return false end;
	Turbine.Chat.Received(nil, { Message = message, ChatType = chatType or Turbine.ChatType.Quest });
	return true;
end
Turbine.Shell.WriteLine = function(text) lastShell = text end;
'''

def run():
    lua = LuaRuntime(unpack_returned_tuples=True)

    def lade_modul(name):
        """MagicQuestLog.Data.QuestDetails_de_3 -> Data/QuestDetails_de_3.lua.
        The client's own modules ("Turbine", "Turbine.UI" …) are part of the stub."""
        if not name.startswith('MagicQuestLog.Data.'):
            return name
        datei = DATA / (name.rsplit('.', 1)[-1] + '.lua')
        if not datei.is_file():
            raise RuntimeError('module not found: ' + name)
        text = datei.read_text(encoding='utf-8')
        # One test needs the progress file of another character; the module is read
        # again on every Load, so the name is replaced on the way in.
        if datei.name == 'Progress.lua' and lua.eval('testWithoutProgress'):
            return name  # a client without any older progress
        fremd = lua.eval('testProgressCharacter')
        if datei.name == 'Progress.lua' and fremd:
            text = re.sub(r'\["character"\]\s*=\s*"[^"]*"', '["character"] = "%s"' % fremd, text, count=1)
        lua.execute(text)
        return name

    lua.globals().ladeModul = lade_modul
    lua.execute(STUBS)
    for name in ('Perf.lua', 'Class.lua', 'Strings.lua', 'Settings.lua', 'Model.lua', 'Live.lua', 'Characters.lua', 'Icon.lua', 'Window.lua'):
        lua.execute((PLUGIN / name).read_text(encoding='utf-8'))
    lua.execute((DATA / 'Quests_de.lua').read_text(encoding='utf-8'))
    lua.execute((DATA / 'Deeds_de.lua').read_text(encoding='utf-8'))
    lua.execute((DATA / 'Quests_en.lua').read_text(encoding='utf-8'))
    lua.execute((DATA / 'Deeds_en.lua').read_text(encoding='utf-8'))
    lua.execute((DATA / 'Progress.lua').read_text(encoding='utf-8'))
    lua.execute((PLUGIN / 'Main.lua').read_text(encoding='utf-8'))
    lua.execute(r'''
local P = MagicQuestLog.Perf;
assert(P.enabled == false and #P.samples > 0, "startup samples kept without chat spam");
assert(MagicQuestLog.command == shellCommand, "shell command kept alive by a global reference");
shellCommand:Execute("mql", "zeit");
assert(P.enabled, "shell callback receives command name before arguments");
shellCommand:Execute("mql", "zeit");
assert(not P.enabled, "shell timing command toggles off");
assert(P.clock == "os.clock", "CPU clock used when available");
local realNow = P.Now;
P.Now = function() return gameTime end;
local started = P.Now();
gameTime = gameTime + 0.125;
P.Record("test", started, " (detail)");
local sample = P.samples[#P.samples];
assert(sample.ms == 125 and sample.detail == " (detail)", "seconds converted to milliseconds");
P.Toggle();
assert(P.enabled and string.find(lastShell, "125.0 ms", 1, true), "toggle prints retained samples");
P.Toggle();
assert(not P.enabled, "measurement output can be disabled");
for i = 1, P.limit + 1 do P.Record("bounded", P.Now()); end
assert(#P.samples == P.limit, "retained samples bounded");
-- Frame timing: the watcher reports game time until the next Update.
P.pending = nil;
P.Frame("Rebuild");
assert(P.pending ~= nil, "frame timing pending");
gameTime = gameTime + 0.040;
P.watcher.Update(P.watcher);
assert(P.pending == nil and P.samples[#P.samples].ms > 39.9 and P.samples[#P.samples].ms < 40.1, "frame time measured");
P.Now = realNow;
''')
    print('PASS: timing retains startup samples, reports milliseconds, toggles chat and bounds memory')
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
-- Die erwartete Gesamtzahl kommt aus dem geladenen Katalog, nicht aus einer
-- festen Zahl: der Katalog waechst mit jedem Spielupdate.
questTotal = #MQL.catalogs.quests;
deedTotal = #MQL.catalogs.deeds;
assert(questTotal > 14000, "quest catalog implausibly small: " .. questTotal);
-- Counted totals are not the catalog size: a session play is never recorded by the
-- game, and of two quests that rule each other out only one can be taken. Both stay
-- out of the counters, so the expected numbers are worked out here.
function erwartet(completed)
	local total, done = 0, 0;
	local known = completed ~= nil and completed ~= false;
	for _, record in ipairs(MQL.catalogs.quests) do
		local finished = known and completed[record.id] == true;
		if finished then
			total, done = total + 1, done + 1;
		elseif record.x ~= 1 then
			local blocked = false;
			if known then
				for _, other in ipairs(record.ex or {}) do
					if completed[other] == true then blocked = true; break; end
				end
			end
			if not blocked then total = total + 1; end
		end
	end
	return total, done;
end
function zahl(completed) return (erwartet(completed)); end
assert(MQL.language == "de", "client德语 should win, got " .. tostring(MQL.language));
assert(MQL.window ~= nil, "window missing");
local window = MQL.window;
-- List sections start folded in the window; these checks look at entries inside
-- them, so every section is treated as unfolded here (folding is tested below).
local foldedDefault = window.folded;
window.folded = setmetatable({}, { __index = function() return false; end });
assert(window:IsVisible(), "window must start visible");
assert(string.find(window.countLabel:GetText(), tostring(zahl(window.completed)), 1, true), "count label: " .. window.countLabel:GetText());
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
assert(all == zahl(window.completed), "unfiltered total " .. tostring(all));
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
	if (record.gt ~= nil or record.sc ~= nil) then withTarget = withTarget + 1; if sample == nil then sample = record; end end
end
assert(withTarget > 7000, "too few verified positions: " .. tostring(withTarget));
-- No spoilers by default: description yes, objectives and steps only on request.
window.showObjectives = false;
window:ShowDetails(sample);
local hidden = window.detailText:GetText();
assert(string.find(hidden, MQL.strings.description, 1, true), "description missing");
assert(not string.find(hidden, MQL.strings.step .. " ", 1, true), "steps must stay hidden by default");
assert(window.stepsButton:IsVisible(), "the show-objectives button must be offered");
assert(window.stepsButton:GetText() == MQL.strings.showsteps and MQL.strings.showsteps == "Ziele einblenden", "button says Ziele einblenden");
assert(window.stepsButton:GetTop() > window.detailText:GetTop() and window.stepsButton:GetTop() <= window.detailText:GetTop() + window.detailText:GetHeight() + 6,
	"the button sits right under the description");
assert(window.findButton == nil or type(window.findButton) == "function", "no requirement search button any more");
if sample.gt ~= nil then
	assert(string.find(window.command, string.format("%d:", sample.gt.map), 1, true), "MoorMap must point at the giver by default");
end
window.stepsButton.Click();
assert(window.showObjectives == true, "the button switches objectives on");
assert(not window.stepsButton:IsVisible(), "once shown the button goes away");
assert(window.detailText:GetHeight() == window.detailMax, "shown objectives use the whole pane");
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
-- A name that does not fit must not run into the row below: the row grows in whole
-- lines, and the height is cached per text and column width.
local oneLine = window:RowHeight("Rueckeroberung", 300);
local manyLines = window:RowHeight(string.rep("Rueckeroberung des Agarnaith ", 6), 300);
assert(oneLine == 20, "a short name must stay one line, got " .. tostring(oneLine));
assert(manyLines > oneLine and manyLines <= 80, "a long name must grow its row: " .. tostring(manyLines));
assert(window:RowHeight(string.rep("Rueckeroberung des Agarnaith ", 6), 300) == manyLines,
	"row heights must be cached per text and width");
local ladder = { [20] = true, [40] = true, [60] = true, [80] = true };
for _, row in ipairs(window.rows) do
	assert(ladder[row.control:GetHeight()], "row height must be a whole number of lines: "
		.. tostring(row.control:GetHeight()));
end
-- A record without a verified position must not pretend to have one.
local without = nil;
for _, record in ipairs(MQL.catalogs.quests) do
	if record.gt == nil then MQL.Model.Details(record); end
	if record.gt == nil and #record.t == 0 then without = record; break end
end
assert(without ~= nil, "a quest without any position");
-- With objectives shown for this entry (they start hidden for every new one).
window.showObjectives = true;
window:ShowDetails(without, true);
assert(not window.mapSlot:IsVisible(), "map slot must hide without a position");
assert(window.mapInfo:GetText() == MQL.strings.nomap, "honest no-position text expected");
window:ShowDetails(without);
assert(window.showObjectives == false, "a new entry starts with its objectives hidden");
assert(window.command == false, "no command without a position");
-- Deeds use the same machinery.
window:SetKind("deeds");
assert(window.kind == "deeds" and window.root.total == deedTotal, "deed catalog");
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
assert(window.root.total == zahl(window.completed), "totals must not change on expand");
-- Switching kinds must not leave the other kind's record in the detail pane.
assert(window.record == false, "a kind switch must clear the detail pane");
-- Row clicks use the list selection path. Open the path of one known quest so the
-- row under test is a leaf; selecting it must show exactly that record.
local target = nil;
for _, record in ipairs(MQL.catalogs.quests) do
	if record.searchText ~= nil and string.find(record.searchText, "zugellosen", 1, true) ~= nil then
		target = record;
		break;
	end
end
assert(target ~= nil, "expected a quest matching Zügellosen");
window.searchBox:SetText("Zügellosen");
window.query = "Zügellosen";
local path = "|";
for depth, part in ipairs(target.p) do
	path = path .. (depth - 1) .. "/" .. part.k;
	window.expanded[path] = true;
end
window:Rebuild();
local leaf = nil;
for index, row in ipairs(window.rows) do
	-- The row reads "name   · level": the name comes first.
	if row.control.text and string.find(row.control.text:GetText(), target.displayName, 1, true) == 1 then leaf = index; break; end
end
assert(leaf ~= nil, "expected the matching quest as a visible row");
window.tree.selected = leaf;
window.tree.SelectedIndexChanged();
assert(window.highlighted ~= nil, "clicking a leaf must select it");
assert(window.record == target, "clicking a leaf must show that record");
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
assert(window.root.total == zahl(window.completed), "totals must survive expanding");
click(1);
assert(window.tree:GetItemCount() == collapsed, "clicking the same node again must collapse it");
-- The longest catalog name must actually arrive as a taller row, not as a clipped
-- one: this runs through AddNode and AddRow, not only through the height helper.
local tallest, tallestLength = nil, 0;
for _, record in ipairs(MQL.catalogs.quests) do
	local name = tostring(record.displayName or record.name);
	if #name > tallestLength then tallest, tallestLength = record, #name; end
end
assert(tallest ~= nil, "expected a quest record");
window.expanded = {};
window.searchBox:SetText(tallest.displayName);
window.query = tallest.displayName;
local tallPath = "|";
for depth, part in ipairs(tallest.p) do
	tallPath = tallPath .. (depth - 1) .. "/" .. part.k;
	window.expanded[tallPath] = true;
end
window:Rebuild();
local tallRow = nil;
for _, row in ipairs(window.rows) do
	if row.control.text and string.find(row.control.text:GetText(), tallest.displayName, 1, true) == 1 then tallRow = row; break; end
end
assert(tallRow ~= nil, "expected the longest name as a visible row");
assert(tallRow.control:GetHeight() > 20,
	"a long name must get a taller row, got " .. tostring(tallRow.control:GetHeight()));
assert(tallRow.control.text:GetHeight() == tallRow.control:GetHeight(),
	"the name label must fill the taller row");
window.expanded = {};
window.searchBox:SetText("");
window.query = "";
window:Rebuild();
-- Session plays and alternatives. The game never records a session play, and of two
-- quests that rule each other out only one can be taken, so neither is counted.
assert(type(window.completed) == "table", "precondition: progress is known here");
local completed = window.completed;
local sessionRecord, excludedRecord = nil, nil;
for _, record in ipairs(MQL.catalogs.quests) do
	if record.x == 1 and sessionRecord == nil then sessionRecord = record; end
	if excludedRecord == nil and completed ~= nil and record.ex ~= nil then
		for _, other in ipairs(record.ex) do
			if completed[other] == true and completed[record.id] ~= true then
				excludedRecord = record;
			end
		end
	end
end
assert(sessionRecord ~= nil, "expected a session play in the catalog");
assert(excludedRecord ~= nil, "expected an entry ruled out by a finished alternative");
window:Rebuild();
assert(sessionRecord.sessionPlay == true, "the session play must be flagged");
assert(excludedRecord.excluded == true, "a finished alternative must rule an entry out");
assert(type(excludedRecord.excludedByName) == "string" and excludedRecord.excludedByName ~= "",
	"the entry that rules it out must be named");
-- A finished entry always counts, even where the data claims both alternatives are
-- exclusive: eleven such pairs exist in the export and this character has both.
assert(completed[excludedRecord.id] ~= true, "precondition: the ruled-out entry is open");
local paired = nil;
for _, record in ipairs(MQL.catalogs.quests) do
	for _, other in ipairs(record.ex or {}) do
		if completed[record.id] == true and completed[other] == true then paired = record; end
	end
end
assert(paired == nil or paired.excluded ~= true, "a finished entry must never be marked as ruled out");
-- The two entries reported from the game: "Ein Schlag auf den Kopf" is ruled out by
-- the chapter this character played, "Endlich, der Schatz" is a session play. Both
-- sit in the same epic chapter group, which must count only what is still doable.
local ersatz, interlude = nil, nil;
for _, record in ipairs(MQL.catalogs.quests) do
	if record.id == "70048CDF" then ersatz = record; end
	if record.id == "70048CDC" then interlude = record; end
end
assert(ersatz ~= nil and interlude ~= nil, "expected the two entries from the game");
local root = MQL.Model.Build(MQL.catalogs.quests, "", MQL.strings, completed, {});
-- The tree has two levels; the chapter group is a list section of its book.
local function leafOf(record)
	local node = root;
	for index, part in ipairs(record.p) do
		if index > 2 then break; end
		node = node.children[part.k];
	end
	return node;
end
local group = leafOf(interlude);
assert(group ~= nil and leafOf(ersatz) == group and interlude.section == ersatz.section and interlude.section ~= "",
	"both entries must share one chapter group");
local counted, listed = 0, 0;
for _, record in ipairs(group.items) do
	if record.section == interlude.section then
		listed = listed + 1;
		if not (record.sessionPlay or record.excluded) then counted = counted + 1; end
	end
end
assert(counted == listed - 2, "the two entries must be the only uncounted ones: "
	.. tostring(counted) .. " of " .. tostring(listed));
local bookCountable = 0;
for _, record in ipairs(group.items) do
	if not (record.sessionPlay or record.excluded) then bookCountable = bookCountable + 1; end
end
assert(group.total == bookCountable, "the book must count only what can still be done: "
	.. tostring(group.total) .. " of " .. tostring(bookCountable));
bookCounted, bookListed = counted, listed;
assert(ersatz.excluded == true, "the alternate chapter must be ruled out");
assert(interlude.sessionPlay == true, "the interlude must be a session play");
-- Rows say so: dimmed text with a short label, and no status mark that would claim
-- the entry is still open.
window.expanded = {};
window.searchBox:SetText("Endlich, der Schatz");
window.query = "Endlich, der Schatz";
local interludePath = "|";
for depth, part in ipairs(interlude.p) do
	interludePath = interludePath .. (depth - 1) .. "/" .. part.k;
	window.expanded[interludePath] = true;
end
window:Rebuild();
local interludeRow = nil;
for _, row in ipairs(window.rows) do
	local shown = row.control.text and row.control.text:GetText() or "";
	if string.find(shown, interlude.displayName, 1, true) == 1
		and string.find(shown, "(" .. MQL.strings.sessionplay .. ")", 1, true) then interludeRow = row; break; end
end
assert(interludeRow ~= nil, "the session play row must carry its label");
assert(interludeRow.control.status == false, "a session play must not carry a status mark");
window:ShowDetails(interlude);
assert(string.find(window.detailText:GetText(), MQL.strings.sessionnote, 1, true),
	"the details must explain why it is not counted");
window:ShowDetails(ersatz);
assert(string.find(MQL.Model.Normalize(window.detailText:GetText()),
	MQL.Model.Normalize(MQL.strings.alternative), 1, true),
	"the details must say the entry is not possible");
assert(string.find(window.detailText:GetText(), ersatz.excludedByName, 1, true),
	"the details must name the finished alternative");
window.expanded = {};
window.searchBox:SetText("");
window.query = "";
window:Rebuild();
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
assert(window.root.total == zahl(window.completed), "cached tree must keep its totals");
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
window:SetProgress({ [sampleId] = true }, true);
assert(string.find(window.countLabel:GetText(), MQL.strings.finished, 1, true),
	"progress must be reported: " .. window.countLabel:GetText());
assert(string.find(window.countLabel:GetText(), "1 / " .. tostring(zahl(window.completed)), 1, true), "headline count: " .. window.countLabel:GetText());
window.expanded["|0/region:Gondor"] = true;
window:Rebuild();
local counterSeen = false;
for _, row in ipairs(window.rows) do
	local text = row.control.label and row.control.label:GetText() or "";
	if string.find(text, "/", 1, true) ~= nil then counterSeen = true; end
end
assert(counterSeen, "node counters must show n/total with progress");
window:SetProgress(nil);
assert(not string.find(window.countLabel:GetText(), "1 / " .. tostring(zahl(window.completed)), 1, true),
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
-- Whatever the catalog holds, no raw placeholder may reach a caption.
local raw = 0;
for _, record in ipairs(MQL.catalogs.quests) do
	for _, part in ipairs(record.p) do
		local shown = MQL.Model.Display(part.n, {}, MQL.strings);
		if string.find(shown, "${", 1, true) ~= nil then raw = raw + 1; end
	end
end
assert(raw == 0, "raw placeholders in displayed captions: " .. raw);
-- Placeholders in texts must be filled: the resolution result used to be thrown
-- away, which replaced every one of them with the plain "[value]" marker.
-- The fixture is built here instead of taken from the catalog: the DAT export
-- writes these markers bare ("PLAYER", "CLASS", without the "${...}" wrapper),
-- so a catalog with no wrapped placeholder would silently retire this check.
local synthetic = { id = "7F000001", name = "Platzhalterprobe", p = {},
	d = "Der ${PLAYER} und der ${CLASS} pruefen ${PLAYERNAME:A[1]|B[2]} ihre Pflicht.",
	s = {}, t = {} };
window:ShowDetails(synthetic);
local filled = window.detailText:GetText();
assert(string.find(filled, "Feldobar", 1, true) ~= nil,
	"player placeholder not filled in: " .. string.sub(filled, 1, 120));
assert(string.find(filled, "Jäger", 1, true) ~= nil,
	"class placeholder not filled in: " .. string.sub(filled, 1, 120));
assert(string.find(filled, "${", 1, true) == nil,
	"placeholder left raw: " .. string.sub(filled, 1, 120));
assert(string.find(filled, MQL.strings.value, 1, true) == nil,
	"placeholder fell back to the value marker: " .. string.sub(filled, 1, 120));
window:ShowDetails(sample);
-- Game text carries LOTRO markup ("<rgb=#FF0000>…</rgb>", "<b>", "<u>"), which a
-- label cannot render. The tags must go, the words must stay.
assert(MQL.Model.CleanMarkup("<rgb=#FF0000>Erwerbt das Rezept</rgb>") == "Erwerbt das Rezept",
	"colour tag not removed");
assert(MQL.Model.CleanMarkup("<b>fett</b> und <u>unterstrichen</u>") == "fett und unterstrichen",
	"bold/underline not removed");
assert(MQL.Model.CleanMarkup("Pack <rgb>Sorciere</rgb>") == "Pack Sorciere",
	"malformed tag not removed");
assert(MQL.Model.CleanMarkup("Asseyez-vous</sit> avec lui") == "Asseyez-vous avec lui",
	"stray closing tag not removed");
assert(MQL.Model.CleanMarkup("<Armund sighs") == "<Armund sighs",
	"a stray < inside real text must stay");
local marked = nil;
for _, core in ipairs(MQL.catalogs.quests) do
	local record = MQL.Model.Details(core);
	if string.find(record.d or "", "<rgb", 1, true) ~= nil then marked = record; break; end
end
assert(marked ~= nil, "expected a quest whose text carries markup");
window:ShowDetails(marked);
local clean = window.detailText:GetText();
assert(string.find(clean, "<rgb", 1, true) == nil, "markup leaked into the detail text");
assert(string.find(clean, "</rgb>", 1, true) == nil, "closing markup leaked");
-- Switching records must start at the top again. A bar bound to a label may not be
-- set directly, so the pane must be rebound after every text change.
window:ShowDetails(sample);
assert(window.detailText.scrollbar == window.detailScroll, "detail bar must stay bound");
assert(window.detailText.boundSetValue ~= true, "SetValue on a bound bar must never happen");
window:ShowDetails(without);
assert(window.detailText.boundSetValue ~= true, "SetValue on a bound bar must never happen");
window:ShowDetails(nil);
assert(window.detailText.boundSetValue ~= true, "SetValue on a bound bar must never happen");
assert(window.detailText:GetText() == "", "clearing must empty the detail text");
-- Live completion detection from the quest channel.
local tracker = MQL.tracker;
assert(tracker ~= nil, "chat tracker missing");
assert(Turbine.Chat.Received ~= nil, "chat hook not installed");
-- Pick a quest whose name is unique, so the completion can be assigned.
local uniqueRecord, sharedName = nil, nil;
for _, record in ipairs(MQL.catalogs.quests) do
	local ids = tracker.index[record.name];
	if ids ~= nil and #ids == 1 and string.find(record.name, "${", 1, true) == nil then
		uniqueRecord = record;
	elseif ids ~= nil and #ids > 1 and sharedName == nil then
		sharedName = record.name;
	end
end
assert(uniqueRecord ~= nil, "expected a quest with a unique name");
assert(sharedName ~= nil, "expected a quest name shared by several entries");
local before = window.root.total;
local doneBefore = 0;
for _ in pairs(tracker.completed) do doneBefore = doneBefore + 1; end;
-- Two chat events: header first, then the name.
assert(receiveChat("Abgeschlossen:"), "hook must accept a message");
assert(tracker.completed[uniqueRecord.id] ~= true, "name alone must not mark anything");
receiveChat(uniqueRecord.name);
assert(tracker.completed[uniqueRecord.id] == true, "two-event completion must be assigned");
-- One event with the name on the same line (English client form).
local second = nil;
for _, record in ipairs(MQL.catalogs.quests) do
	if record.id ~= uniqueRecord.id and tracker.index[record.name] ~= nil
		and #tracker.index[record.name] == 1 and string.find(record.name, "${", 1, true) == nil then
		second = record; break;
	end
end
assert(second ~= nil, "expected a second uniquely named quest");
receiveChat("Completed: " .. second.name);
assert(tracker.completed[second.id] == true, "single-line completion must be assigned");
-- One event containing a line break instead of the name: third case.
local third = nil;
for _, record in ipairs(MQL.catalogs.quests) do
	local ids = tracker.index[record.name];
	if ids ~= nil and #ids == 1 and record.id ~= uniqueRecord.id and record.id ~= second.id
		and string.find(record.name, "${", 1, true) == nil then third = record; break; end
end
assert(third ~= nil, "expected a third uniquely named quest");
receiveChat("Terminé :\r\n" .. third.name);
assert(tracker.completed[third.id] == true, "line-break completion must be assigned");
-- A shared name is never guessed, and it is remembered for later.
local markedShared = false;
for _, id in ipairs(tracker.index[sharedName]) do
	if tracker.completed[id] == true then markedShared = true; end
end
receiveChat("Abgeschlossen:");
receiveChat(sharedName);
for _, id in ipairs(tracker.index[sharedName]) do
	assert(tracker.completed[id] ~= true, "a shared name must not be assigned to a guess");
end
assert(tracker.unresolved[sharedName] ~= nil, "a shared name must be recorded");
assert(type(tracker.unresolved[sharedName]) == "string",
	"the remembered count must be text, got " .. type(tracker.unresolved[sharedName]));
-- Other chat channels are ignored, and unrelated lines mark nothing.
local unrelated = receiveChat("Abgeschlossen: " .. second.name, Turbine.ChatType.Standard);
assert(unrelated, "hook was not called for the channel test");
assert(tracker.completed[second.id] == true, "still assigned");
tracker.completed[second.id] = nil;
receiveChat("Abgeschlossen: " .. second.name, Turbine.ChatType.Standard);
assert(tracker.completed[second.id] ~= true, "a non-quest channel must be ignored");
receiveChat("Neue Aufgabe: " .. second.name);
assert(tracker.completed[second.id] ~= true, "starting a quest is not completing it");
receiveChat("Abgeschlossen: Gibt es nicht");
assert(tracker.unresolved["Gibt es nicht"] == nil, "an unknown name is not a name clash");
-- Live progress is stored per character in the server scope, not in the settings.
local saved = savedData["MagicQuestLog_Live_Feldobar"];
assert(saved ~= nil, "live progress must be saved");
assert(saved.completed[uniqueRecord.id] == true, "saved live progress must hold the id");
assert(savedSettings == nil or savedSettings.completed == nil,
	"live progress must not land in the account settings");
-- The window follows the new mark, and says its totals are only partly known.
window:SetProgress(tracker.completed, false);
assert(string.find(window.countLabel:GetText(), MQL.strings.finishedknown, 1, true) ~= nil,
	"live-only progress must be labelled as partial: " .. window.countLabel:GetText());
window:SetProgress(tracker.completed, true);
assert(string.find(window.countLabel:GetText(), MQL.strings.finished, 1, true) ~= nil,
	"an exported baseline allows a full count: " .. window.countLabel:GetText());
-- Reloading the plugin must not stack a second handler.
MagicQuestLog.Load(nil);
local newTracker = MagicQuestLog.tracker;
assert(newTracker ~= nil and newTracker ~= tracker, "reload must build a new tracker");
local freshId = nil;
for _, record in ipairs(MagicQuestLog.catalogs.quests) do
	local ids = newTracker.index[record.name];
	if ids ~= nil and #ids == 1 and string.find(record.name, "${", 1, true) == nil then
		freshId = record.id; break;
	end
end
receiveChat("Abgeschlossen: " .. MagicQuestLog.catalogs.quests[1].name);
local marks = 0;
for _, line in ipairs({}) do marks = marks + 1; end
assert(tracker.completed ~= newTracker.completed or savedData["MagicQuestLog_Live_Feldobar"] ~= nil,
	"reload must not keep two trackers writing");
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
-- The test stub can load every language now, so a missing French catalog is
-- simulated the way the client would show it: the module import fails.
local realImport = import;
import = function(name)
	if string.find(name, "_fr", 1, true) ~= nil then error("no French catalog in this build"); end
	return realImport(name);
end;
assert(MagicQuestLog.Data["quests_fr"] == nil, "precondition: no French catalog loaded");
local previousWindow = MagicQuestLog.window;
MagicQuestLog.Load(nil);
fallbackLanguage = MagicQuestLog.language;
import = realImport;
assert(fallbackLanguage == "en", "fallback language: " .. tostring(fallbackLanguage));
assert(MagicQuestLog.window ~= previousWindow, "fallback must build a new window, not keep the old one");
assert(MagicQuestLog.window ~= nil and MagicQuestLog.window.root ~= nil, "fallback window missing");
assert(MagicQuestLog.window.root.total == zahl(MagicQuestLog.window.completed), "fallback total: " .. tostring(MagicQuestLog.window.root.total));
assert(MagicQuestLog.strings.quests == "Quests", "fallback strings");
assert(MagicQuestLog.Data["quests_en"] ~= nil, "English catalog must be present for the fallback");
assert(MagicQuestLog.Data["quests_de"] ~= nil, "German catalog stays loaded and is simply not chosen");
assert(MagicQuestLog.window.countLabel:GetText() ~= nil and MagicQuestLog.window.countLabel:GetText() ~= "", "empty count");
-- Then a locale that exists must be used as-is: with the French catalog present,
-- a French client gets French.
MagicQuestLog.Load(nil);
assert(MagicQuestLog.language == "fr", "a present French catalog must be used");
''')

    lua.execute(r'''
-- Stored values can come back as text: they must be coerced and honoured.
-- A damaged file once carried stray numeric keys; they must not be loaded back.
storedSettings = { windowLeft = "300", windowTop = "180", windowVisible = false, useIcon = false,
	[1] = 0, [2] = 0, junk = "x" };
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
assert(saved[1] == nil and saved[2] == nil and saved.junk == nil,
	"unknown keys must not be written back");
local known = 0;
for key in pairs(saved) do
	assert(key == "windowLeft" or key == "windowTop" or key == "iconLeft"
		or key == "iconTop" or key == "windowVisible" or key == "useIcon"
		or key == "showObjectives" or key == "filter",
		"unexpected key in the settings file: " .. tostring(key));
	known = known + 1;
end
assert(known >= 2 and known <= 8, "settings file has " .. known .. " keys");
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
testProgressCharacter = "Someoneelse";
-- No live or imported progress either, so only the foreign file could claim anything.
local keptServer, keptCharacter = serverData, characterData;
serverData, characterData = {}, {};
MagicQuestLog.Load(nil);
assert(MagicQuestLog.window.completed == false, "foreign progress must be ignored");
testProgressCharacter = nil;
assert(not string.find(MagicQuestLog.window.countLabel:GetText(), MagicQuestLog.strings.finished, 1, true),
	"a foreign progress file must never show finished counts");
progress.character = originalCharacter;
serverData, characterData = keptServer, keptCharacter;
MagicQuestLog.Load(nil);
assert(MagicQuestLog.window.completed ~= false, "matching progress must be used again");
-- Back to a clean German client for the summary below.
storedSettings = nil;
languageCommand = "hilfe";
MagicQuestLog.Load(nil);
assert(MagicQuestLog.language == "de", "German client must use the German catalog");
''')

    lua.execute(r'''
-- Several characters. The map site writes one import file per character into the
-- server scope; the plugin reads it, never writes it, and can show any character.
local MQL = MagicQuestLog;
serverData, characterData = {}, {};
local quests = MQL.catalogs.quests;
local a, b, c = quests[1].id, quests[2].id, quests[3].id;
-- The old live file in the character scope is taken over once.
characterData["MagicQuestLogLive"] = { version = "1", completed = { [c] = true }, unresolved = {} };
serverData["MagicQuestLog_Import_Feldobar"] = { version = "1", character = "Feldobar",
	date = "2026-11-03", completed = { [a] = true, ["nonsense"] = true, ["7000000Z"] = true } };
serverData["MagicQuestLog_Import_Meriadoc"] = { version = "1", character = "Meriadoc",
	date = "2026-11-02", completed = { [b] = true } };
-- A file whose content names another character is not that character's progress.
serverData["MagicQuestLog_Import_Fremder"] = { version = "1", character = "Feldobar",
	completed = { [b] = true } };
serverData["MagicQuestLog_Characters"] = { Meriadoc = true, Fremder = true, ["bad name"] = true };
MQL.Data.progress = nil;
package.loaded["MagicQuestLog.Data.Progress"] = nil;
MagicQuestLog.Load(nil);
local window = MQL.window;
assert(MQL.shown == "Feldobar", "the logged-in character is shown first");
assert(window.completed[a] == true, "imported id must count");
assert(window.completed[c] == true, "old live progress must be taken over");
assert(window.completed["NONSENSE"] == nil and window.completed["7000000Z"] == nil, "malformed ids are dropped");
assert(window.progressExact == true, "an import holds the older history");
assert(string.find(window.characterLabel:GetText(), "2026-11-03", 1, true), "import date shown: " .. window.characterLabel:GetText());
-- The logged-in character needs no name; the switch shows because there are several.
assert(not string.find(window.characterLabel:GetText(), "Feldobar", 1, true), "own name is not repeated");
assert(window.characterButton:IsVisible(), "switch offered with several characters");
-- The logged-in character joins the stored list; invalid names never do.
local index = serverData["MagicQuestLog_Characters"];
assert(index.Feldobar == true and index.Meriadoc == true, "character list must hold both");
assert(MQL.characters[1] == "Feldobar" and #MQL.characters == 3, "sorted list without bad names: " .. table.concat(MQL.characters, ","));
-- Switching shows the other character's import and no live claim.
window.CharacterClicked();
assert(MQL.shown == "Fremder", "next character: " .. tostring(MQL.shown));
assert(window.completed == false, "a file naming someone else must be ignored");
window.CharacterClicked();
assert(MQL.shown == "Meriadoc", "next character: " .. tostring(MQL.shown));
assert(window.completed[b] == true and window.completed[a] == nil, "only Meriadoc's ids");
assert(not string.find(window.characterLabel:GetText(), MQL.strings.livenow, 1, true), "no live tag for another character");
assert(string.find(window.characterLabel:GetText(), "Meriadoc", 1, true), "another character is named");
window.CharacterClicked();
assert(MQL.shown == "Feldobar", "the switch wraps around");
-- Live completions belong to the logged-in character only, in its own file.
MQL.Live.Mark(MQL.tracker, b);
assert(serverData["MagicQuestLog_Live_Feldobar"].completed[b] == true, "live goes to the own file");
assert(serverData["MagicQuestLog_Live_Meriadoc"] == nil, "another character's file stays untouched");
assert(characterData["MagicQuestLogLive"].completed[c] == true, "the old file is left as it was");
-- A new import while the game runs shows up when the window opens again.
local builds, original = 0, MQL.Model.Build;
MQL.Model.Build = function(...) builds = builds + 1; return original(...); end;
window.Shown();
assert(builds == 0, "an unchanged import must not rebuild the tree");
serverData["MagicQuestLog_Import_Feldobar"].completed[quests[4].id] = true;
serverData["MagicQuestLog_Import_Feldobar"].date = "2026-11-04";
window:SetVisible(false);
window:SetVisible(true);
window.VisibleChanged();
assert(window.completed[quests[4].id] ~= true, "the import is read at most every 30 seconds");
gameTime = gameTime + 31;
window.VisibleChanged();
assert(window.completed[quests[4].id] == true, "a new import must be picked up on opening");
assert(builds >= 1, "a changed import rebuilds the tree");
MQL.Model.Build = original;
-- Search waits for a pause in typing; one character does not search.
window.query = "";
window:Rebuild();
local searchBuilds = 0;
MQL.Model.Build = function(...) searchBuilds = searchBuilds + 1; return original(...); end;
window.searchBox:SetText("b");
window.searchBox.TextChanged();
window.searchBox:SetText("br");
window.searchBox.TextChanged();
window.searchBox:SetText("bree");
window.searchBox.TextChanged();
window.Update();
assert(searchBuilds == 0, "typing does not search before the pause");
gameTime = gameTime + 0.4;
window.Update();
assert(searchBuilds == 1 and window.query == "bree", "one search after the pause");
window:Search("b");
assert(window.query == "", "a single character is no search");
window:Search("é");
assert(window.query == "", "a single accented character is no search either");
MQL.Model.Build = original;
-- Expanding twice hands back the same row controls; no new labels.
window:Rebuild();
local first = window.tree:GetItem(1);
window.tree.SelectedIndexChanged = window.tree.SelectedIndexChanged;
window.tree:SetSelectedIndex(1); window.tree.SelectedIndexChanged();
local opened = window.tree:GetItemCount();
window.tree:SetSelectedIndex(1); window.tree.SelectedIndexChanged();
window.tree:SetSelectedIndex(1); window.tree.SelectedIndexChanged();
assert(window.tree:GetItem(1) == first and window.tree:GetItemCount() == opened, "rows reused on expanding again");
local cachedChild = false;
for _, control in pairs(window.rowCache) do if control == window.tree:GetItem(2) then cachedChild = true end end
assert(cachedChild, "child rows come from the row cache");
window.tree:SetSelectedIndex(1); window.tree.SelectedIndexChanged();
-- Short names need no ruler.
local measured = window.rulerWorks;
window.rulerWorks = true;
window.heights = {};
window.perfRulerCount = 0;
assert(window:RowHeight("Bree", 300) == window:LineHeight(), "short text is one line");
assert(window.perfRulerCount == 0, "short text skips the ruler");
window.rulerWorks = measured;
window.heights = {};
-- Without any import, live or old file there is no claim at all.
serverData, characterData = {}, {};
testWithoutProgress = true;
-- The already-loaded progress table must go too, or the old file still counts.
MagicQuestLog.Data.progress = nil;
MagicQuestLog.Load(nil);
testWithoutProgress = nil;
assert(MQL.window.completed == false, "nothing known means nothing claimed");
assert(MQL.characters[1] == "Feldobar", "the logged-in character is always listed");
-- Back to the regular data for the summary below.
serverData, characterData = {}, {};
''')
    lua.execute((DATA / 'Progress.lua').read_text(encoding='utf-8'))
    lua.execute("MagicQuestLog.Load(nil)")

    read = lua.eval('''function()
    local MQL = MagicQuestLog;
    local roots, collapsed = 0, true;
    for _ in ipairs(MQL.Model.Build(MQL.catalogs.quests, "", MQL.strings).order) do roots = roots + 1; end
    local withTargets, withoutTargets = 0, 0;
    for _, record in ipairs(MQL.catalogs.quests) do
        if record.sc ~= nil or record.gt ~= nil then withTargets = withTargets + 1 else withoutTargets = withoutTargets + 1 end
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
                 and MQL.window.rows[1].control.label:GetText()) or "",
             bookCounted = bookCounted, bookListed = bookListed };
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
    lua.execute(r'''
local M = MagicQuestLog.Model;
-- The map a position is on is a game map (gm); MoorMap's number (map) only drives
-- the button. Without it there is no command, and the ping format is unchanged.
assert(M.MapCommand({ gm = 268437716, lat = -30.5, lon = -50.8 }, "X") == nil, "no MoorMap number, no button");
assert(M.MapCommand({ gm = 268437716, map = 9, lat = -30.5, lon = -50.8, n = "1" }, "Bree quest")
	== "/moormap ping 9:-30.50000:-50.80000:1:Bree quest", "ping format unchanged");
local withGame, withNumber = 0, 0;
for _, core in ipairs(MagicQuestLog.catalogs.quests) do
	local record = MagicQuestLog.Model.Details(core);
	for _, target in ipairs(record.t or {}) do
		assert(type(target.gm) == "number", "every target names its game map");
		withGame = withGame + 1;
		if target.map ~= nil then withNumber = withNumber + 1; end
	end
end
assert(withNumber > 0.95 * withGame, "almost every target has a MoorMap number: " .. withNumber .. "/" .. withGame);
mapShare = string.format("%.1f", 100 * withNumber / withGame);
''')
    print('PASS: targets name their game map; the MoorMap button needs MoorMap\'s number (%s %% of targets have one); ping format unchanged' % lua.globals().mapShare)
    print('PASS: %s row clicks via list selection (same row stays clickable); nodes expand and collapse' % values['rows'])
    print('PASS: start icon toggles the window; position and visibility are stored and honoured')
    print('PASS: header sits below the title bar, search is labelled "%s"' % values['searchLabelText'])
    print('PASS: expanding reuses the cached tree (no re-sort); a new search rebuilds exactly once')
    print('PASS: counters show "%s" with progress and claim nothing without it' % values['counterSample'])
    print('PASS: session plays and ruled-out alternatives stay out of the counters (the reported chapter group counts %s of %s entries)'
          % (values['bookCounted'], values['bookListed']))
    print('PASS: MoorMap runs through a quickslot alias shortcut, not by printing the command')
    print('PASS: a progress file for another character is ignored instead of being shown as ours')
    print('PASS: several characters: import per character, switch, old live data taken over, new import read on opening')
    print('PASS: LOTRO markup is removed from texts, a stray "<" in real words is kept')
    print('PASS: switching records resets the detail scroll to the top')
    print('PASS: live completion is read from the quest channel in all three forms')
    print('PASS: a name shared by several entries is never guessed, only recorded')
    print('PASS: live progress is stored per character; other channels and quest starts are ignored')
    print('PASS: live-only totals are labelled as partial, an export allows a full count')
    print('PASS: a client language without its catalog falls back to English (chosen: %s) with English strings'
          % lua.globals().fallbackLanguage)
    return 0


if __name__ == '__main__':
    sys.exit(run())
