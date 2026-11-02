import "Turbine";

-- Only window placement and icon visibility are stored here. Character progress
-- and catalogs are deliberately not part of these settings.
MagicQuestLog = MagicQuestLog or {};
local S = {};
MagicQuestLog.Settings = S;

local KEY = "MagicQuestLogSettings";
local DEFAULTS = { windowVisible = true, useIcon = true };

-- Positions are stored as text, never as numbers. The client writes numbers with
-- the locale's decimal separator ("239,000000" on a German client), which is not
-- valid Lua and makes the whole settings file unreadable. Load coerces them back.
local PLACEMENTS = { "windowLeft", "windowTop", "iconLeft", "iconTop" };

function S.Load()
	local stored = nil;
	if Turbine.PluginData ~= nil then
		local ok, data = pcall(Turbine.PluginData.Load, Turbine.DataScope.Account, KEY);
		if ok and type(data) == "table" then stored = data; end
	end
	local settings = {};
	for key, value in pairs(DEFAULTS) do settings[key] = value; end
	if stored ~= nil then
		for key, value in pairs(stored) do settings[key] = value; end
	end
	for _, name in ipairs(PLACEMENTS) do
		if settings[name] ~= nil then settings[name] = tonumber(settings[name]); end
	end
	settings.windowVisible = settings.windowVisible ~= false;
	settings.useIcon = settings.useIcon ~= false;
	S.current = settings;
	return settings;
end

function S.Get()
	return S.current or S.Load();
end

--- Whole pixels as text: the client would otherwise write a decimal comma.
function S.Placement(value)
	if value == nil then return nil; end
	local number = tonumber(value);
	if number == nil then return nil; end
	return string.format("%d", math.floor(number + 0.5));
end

function S.Save()
	if Turbine.PluginData == nil or S.current == nil then return; end
	local stored = {};
	for key, value in pairs(S.current) do stored[key] = value; end
	for _, name in ipairs(PLACEMENTS) do
		if stored[name] ~= nil then stored[name] = S.Placement(stored[name]); end
	end
	pcall(Turbine.PluginData.Save, Turbine.DataScope.Account, KEY, stored);
end
