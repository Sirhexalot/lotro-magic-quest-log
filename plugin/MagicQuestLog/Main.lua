import "Turbine";
import "Turbine.Gameplay";
import "Turbine.UI";
import "Turbine.UI.Lotro";
import "MagicQuestLog.Class";
import "MagicQuestLog.Strings";
import "MagicQuestLog.Settings";
import "MagicQuestLog.Model";
import "MagicQuestLog.Live";
import "MagicQuestLog.Icon";
import "MagicQuestLog.Window";

MagicQuestLog = MagicQuestLog or {};

--- The catalog language follows the client language. English is the explicit fallback.
local function clientLanguage()
	if Turbine.Shell ~= nil and Turbine.Shell.IsCommand("hilfe") then return "de"; end
	if Turbine.Shell ~= nil and Turbine.Shell.IsCommand("aide") then return "fr"; end
	return "en";
end

local function playerContext()
	local ok, player = pcall(function() return Turbine.Gameplay.LocalPlayer.GetInstance(); end);
	if not ok then player = nil; end
	return MagicQuestLog.Model.Context(player, Turbine.Gameplay.Class, Turbine.Gameplay.Race);
end

--- A present table is the only reliable success signal for import().
local function loadCatalog(language)
	pcall(function()
		import("MagicQuestLog.Data.Quests_" .. language);
		import("MagicQuestLog.Data.Deeds_" .. language);
	end);
	local data = MagicQuestLog.Data or {};
	return data["quests_" .. language], data["deeds_" .. language];
end

--- Finished ids of the logged-in character, or nil when unknown.
--- A progress file that belongs to another character is ignored: showing its
--- counts here would be a lie. nil always means "not known", never "none done".
local function loadProgress(characterName)
	pcall(function() import("MagicQuestLog.Data.Progress"); end);
	local progress = (MagicQuestLog.Data or {}).progress;
	if progress == nil or progress.completed == nil then return nil; end
	if progress.character ~= nil and characterName ~= nil and progress.character ~= characterName then
		return nil;
	end
	return progress.completed;
end

-- Completions seen while playing are stored per character, in the client's own
-- plugin data. The Progress.lua file is only ever read: a live session must not
-- overwrite an export, and an export must not overwrite a live session.
local LIVE_KEY = "MagicQuestLogLive";

local function loadLive(characterName)
	local stored = nil;
	if Turbine.PluginData ~= nil then
		local ok, data = pcall(Turbine.PluginData.Load, Turbine.DataScope.Character, LIVE_KEY);
		if ok and type(data) == "table" then stored = data; end
	end
	local live = { version = "1", character = characterName, completed = {}, unresolved = {} };
	if stored ~= nil then
		if type(stored.completed) == "table" then
			for id, value in pairs(stored.completed) do
				if value == true then live.completed[id] = true; end
			end
		end
		if type(stored.unresolved) == "table" then
			for name, count in pairs(stored.unresolved) do
				live.unresolved[name] = tostring(count);
			end
		end
	end
	return live;
end

local function saveLive(live)
	if Turbine.PluginData == nil or live == nil then return; end
	local stored = {
		version = "1",
		character = live.character,
		completed = live.completed,
		unresolved = live.unresolved,
	};
	pcall(Turbine.PluginData.Save, Turbine.DataScope.Character, LIVE_KEY, stored);
end

--- Baseline from a file plus what was seen live. "exact" says whether the set can
--- be complete: a live session alone starts at zero and cannot know older history,
--- so the headline must not claim a full count then.
local function mergeProgress(baseline, live)
	local merged, count = {}, 0;
	for id in pairs(baseline or {}) do
		if merged[id] ~= true then merged[id] = true; count = count + 1; end
	end
	local liveCount = 0;
	for id in pairs((live or {}).completed or {}) do
		liveCount = liveCount + 1;
		if merged[id] ~= true then merged[id] = true; count = count + 1; end
	end
	if baseline == nil and liveCount == 0 then return false, nil; end
	return baseline ~= nil, merged;
end

function MagicQuestLog.SetVisible(visible)
	local window = MagicQuestLog.window;
	if window == nil then return; end
	window:SetVisible(visible);
end

function MagicQuestLog.Toggle()
	local window = MagicQuestLog.window;
	if window == nil then return; end
	window:SetVisible(not window:IsVisible());
end

function MagicQuestLog.Load(plugin)
	MagicQuestLog.plugin = plugin;
	local language = clientLanguage();
	local quests, deeds = loadCatalog(language);
	if quests == nil then
		language = "en";
		quests, deeds = loadCatalog(language);
	end
	local strings = MagicQuestLog.Strings[language] or MagicQuestLog.Strings.en;
	MagicQuestLog.language = language;
	MagicQuestLog.strings = strings;
	if quests == nil then
		Turbine.Shell.WriteLine("<rgb=#FF8080>Magic Quest Log: " .. strings.catalogerror .. "</rgb>");
		return;
	end
	local settings = MagicQuestLog.Settings.Load();
	local context = playerContext();
	MagicQuestLog.catalogs = { quests = quests, deeds = deeds };
	MagicQuestLog.window = MagicQuestLog.Window(strings, MagicQuestLog.catalogs);
	MagicQuestLog.window:SetContext(context);
	local live = loadLive(context.name);
	MagicQuestLog.live = live;
	local exact, merged = mergeProgress(loadProgress(context.name), live);
	MagicQuestLog.window:SetProgress(merged, exact);
	MagicQuestLog.tracker = MagicQuestLog.Live.New({
		index = MagicQuestLog.Live.Index(quests, deeds),
		completed = live.completed,
		unresolved = live.unresolved,
		onChange = function()
			saveLive(live);
			local nowExact, nowMerged = mergeProgress(loadProgress(context.name), live);
			MagicQuestLog.window:SetProgress(nowMerged, nowExact);
		end,
		onAmbiguous = function(name, candidates)
			Turbine.Shell.WriteLine("<rgb=#D6B35A>Magic Quest Log: </rgb>" .. name .. " — "
				.. string.format(strings.liveshared, candidates));
		end,
	});
	MagicQuestLog.Live.Attach(MagicQuestLog.tracker);
	MagicQuestLog.icon = MagicQuestLog.Icon(function() MagicQuestLog.Toggle(); end);
	local left = settings.iconLeft or (Turbine.UI.Display:GetWidth() - 44);
	local top = settings.iconTop or 230;
	MagicQuestLog.icon:SetPosition(left, top);
	MagicQuestLog.icon:SetVisible(settings.useIcon ~= false);
	MagicQuestLog.icon.Moved = function(newLeft, newTop)
		local current = MagicQuestLog.Settings.Get();
		current.iconLeft, current.iconTop = newLeft, newTop;
		MagicQuestLog.Settings.Save();
	end;
end

if Turbine.Shell ~= nil and Turbine.Shell.AddCommand ~= nil then
	local command = Turbine.ShellCommand();
	command.Execute = function(_, arguments)
		local text = string.lower(tostring(arguments or ""));
		if string.find(text, "hide") then
			MagicQuestLog.SetVisible(false);
		elseif string.find(text, "show") then
			MagicQuestLog.SetVisible(true);
		else
			MagicQuestLog.Toggle();
		end
	end;
	command.GetShortHelp = function() return MagicQuestLog.strings ~= nil and MagicQuestLog.strings.help or "Magic Quest Log"; end;
	Turbine.Shell.AddCommand("mql;magicquestlog", command);
end

MagicQuestLog.Load(nil);
