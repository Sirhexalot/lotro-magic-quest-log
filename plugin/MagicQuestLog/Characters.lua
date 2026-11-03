-- Progress per character, kept in the client's own plugin data.
--
-- Everything lives in the server scope (PluginData/<account>/<server>/AllCharacters),
-- one file per character, so the window can show any character of this server and
-- not only the one that is logged in:
--
--   MagicQuestLog_Characters        names this plugin or the map site has seen
--   MagicQuestLog_Import_<name>     what LOTRO Companion knew, written by the map site
--   MagicQuestLog_Live_<name>       what this plugin saw finish in the quest channel
--
-- An import file is only ever read here; the plugin never writes it. The client
-- reads a plugin data file from disk on every Load (checked in the game), so a new
-- import shows up the next time the window opens, without a restart.
MagicQuestLog = MagicQuestLog or {};
local C = {};
MagicQuestLog.Characters = C;

local INDEX = "MagicQuestLog_Characters";
local IMPORT = "MagicQuestLog_Import_";
local LIVE = "MagicQuestLog_Live_";
-- Where live progress lived before 0.2.0: the character scope, which no other
-- character can read. It is taken over once and left untouched.
local OLD_LIVE = "MagicQuestLogLive";
local HEX = "^%x%x%x%x%x%x%x%x$";

local function scope(name)
	if Turbine == nil or Turbine.DataScope == nil then return nil; end
	return Turbine.DataScope[name];
end

local function load(where, key)
	if Turbine.PluginData == nil or where == nil then return nil; end
	local ok, data = pcall(Turbine.PluginData.Load, where, key);
	if ok and type(data) == "table" then return data; end
	return nil;
end

local function save(where, key, value)
	if Turbine.PluginData == nil or where == nil then return false; end
	local ok = pcall(Turbine.PluginData.Save, where, key, value);
	return ok == true;
end

--- Only plain names make a usable file name. LOTRO character names are letters.
function C.ValidName(name)
	return type(name) == "string" and string.find(name, "^%a+$") ~= nil;
end

--- Ids from a table of "70000006" = true. Anything else is dropped, never guessed.
local function idSet(source)
	local set, count = {}, 0;
	if type(source) ~= "table" then return set, 0; end
	for id, value in pairs(source) do
		if type(id) == "string" and string.find(id, HEX) ~= nil and (value == true or value == "true") then
			set[string.upper(id)] = true;
			count = count + 1;
		end
	end
	return set, count;
end

--- Names this server knows, sorted, with the logged-in character always present.
--- The logged-in character is added to the stored list, so the map site's export
--- and the plugin end up with the same names.
function C.List(current)
	local stored = load(scope("Server"), INDEX) or {};
	local names, seen = {}, {};
	local function add(name)
		if C.ValidName(name) and not seen[name] then
			seen[name] = true;
			names[#names + 1] = name;
		end
	end
	for name, value in pairs(stored) do
		if value == true or value == "true" then add(name); end
	end
	if C.ValidName(current) and stored[current] ~= true then
		local copy = {};
		for name in pairs(seen) do copy[name] = true; end
		copy[current] = true;
		save(scope("Server"), INDEX, copy);
	end
	add(current);
	table.sort(names);
	return names;
end

--- What the map site imported from LOTRO Companion for this character, or nil.
--- A file that names another character is ignored: showing it would be wrong.
function C.LoadImport(name)
	if not C.ValidName(name) then return nil; end
	local data = load(scope("Server"), IMPORT .. name);
	if data == nil then return nil; end
	if data.character ~= nil and data.character ~= name then return nil; end
	local completed, count = idSet(data.completed);
	if count == 0 then return nil; end
	return {
		completed = completed,
		count = count,
		date = type(data.date) == "string" and data.date or nil,
		stamp = tostring(data.date or "") .. "|" .. tostring(count),
	};
end

--- Live completions of a character. The logged-in character also takes over what
--- an older version stored in the character scope.
function C.LoadLive(name, isCurrent)
	local live = { version = "1", character = name, completed = {}, unresolved = {} };
	if not C.ValidName(name) then return live; end
	local stored = load(scope("Server"), LIVE .. name);
	if stored == nil and isCurrent then stored = load(scope("Character"), OLD_LIVE); end
	if stored ~= nil then
		live.completed = idSet(stored.completed);
		if type(stored.unresolved) == "table" then
			for key, count in pairs(stored.unresolved) do
				live.unresolved[key] = tostring(count);
			end
		end
	end
	return live;
end

function C.SaveLive(live)
	if live == nil or not C.ValidName(live.character) then return false; end
	return save(scope("Server"), LIVE .. live.character, {
		version = "1",
		character = live.character,
		completed = live.completed,
		unresolved = live.unresolved,
	});
end

--- Finished ids of one character: import, live and the old Progress.lua (only for
--- its own character). "exact" says whether older history is in it: live alone
--- starts at zero. nil means nothing is known, never "nothing done".
function C.Progress(name, live, legacy)
	local merged, any = {}, false;
	local imported = C.LoadImport(name);
	local exact = false;
	if imported ~= nil then
		for id in pairs(imported.completed) do merged[id] = true; end
		any, exact = true, true;
	end
	if legacy ~= nil then
		for id in pairs(legacy) do merged[id] = true; end
		any, exact = true, true;
	end
	for id in pairs((live or {}).completed or {}) do
		merged[id] = true;
		any = true;
	end
	if not any then return nil, false, imported; end
	return merged, exact, imported;
end
