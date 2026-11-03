import "Turbine";
import "Turbine.Gameplay";
import "Turbine.UI";
import "Turbine.UI.Lotro";
import "MagicQuestLog.Class";
import "MagicQuestLog.Strings";
import "MagicQuestLog.Settings";
import "MagicQuestLog.Model";
import "MagicQuestLog.Live";
import "MagicQuestLog.Characters";
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

--- Data/Progress.lua from versions before 0.2.0, or nil. Still honoured for its own
--- character so nothing is lost; new progress comes from the map site's import.
--- A file that belongs to another character is ignored: its counts would be wrong.
local function loadProgress(characterName)
	pcall(function() import("MagicQuestLog.Data.Progress"); end);
	local progress = (MagicQuestLog.Data or {}).progress;
	if progress == nil or progress.completed == nil then return nil; end
	if progress.character ~= nil and characterName ~= nil and progress.character ~= characterName then
		return nil;
	end
	return progress.completed;
end

local Characters = MagicQuestLog.Characters;

--- Show one character's progress in the window. Any character of this server can be
--- chosen; live completions only ever come in for the one that is logged in.
function MagicQuestLog.ShowCharacter(name)
	local window = MagicQuestLog.window;
	if window == nil then return; end
	local current = MagicQuestLog.context and MagicQuestLog.context.name or nil;
	local live = (name == current) and MagicQuestLog.live or Characters.LoadLive(name, false);
	local legacy = MagicQuestLog.legacy;
	if MagicQuestLog.legacyCharacter ~= name then legacy = nil; end
	local merged, exact, imported = Characters.Progress(name, live, legacy);
	MagicQuestLog.shown = name;
	MagicQuestLog.importStamp = imported and imported.stamp or false;
	window:SetCharacter(name, imported and imported.date or nil, name == current,
		#(MagicQuestLog.characters or {}));
	-- Level: live for the logged-in character, from the import for any other.
	local level = imported and imported.level or nil;
	if name == current then
		local ok, value = pcall(function() return Turbine.Gameplay.LocalPlayer.GetInstance():GetLevel(); end);
		if ok and tonumber(value) ~= nil then level = tonumber(value); end
	end
	window:SetProgress(merged, exact, imported and imported.running or nil, level);
end

--- Read the import again: the map site may have written a new one while the game
--- was running. Only a changed file rebuilds the tree.
function MagicQuestLog.Refresh()
	local name = MagicQuestLog.shown;
	if name == nil or MagicQuestLog.window == nil then return; end
	local imported = Characters.LoadImport(name);
	local stamp = imported and imported.stamp or false;
	if stamp ~= MagicQuestLog.importStamp then MagicQuestLog.ShowCharacter(name); end
end

--- Next character in the list, for the switch in the window.
function MagicQuestLog.NextCharacter()
	local names = Characters.List(MagicQuestLog.context and MagicQuestLog.context.name);
	MagicQuestLog.characters = names;
	if #names == 0 then return; end
	local index = 1;
	for position, name in ipairs(names) do
		if name == MagicQuestLog.shown then index = position + 1; end
	end
	if index > #names then index = 1; end
	MagicQuestLog.ShowCharacter(names[index]);
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
	MagicQuestLog.context = context;
	MagicQuestLog.legacy = loadProgress(context.name);
	MagicQuestLog.legacyCharacter = context.name;
	local live = Characters.LoadLive(context.name, true);
	MagicQuestLog.live = live;
	MagicQuestLog.characters = Characters.List(context.name);
	MagicQuestLog.window.CharacterClicked = function() MagicQuestLog.NextCharacter(); end;
	MagicQuestLog.window.Shown = function() MagicQuestLog.Refresh(); end;
	MagicQuestLog.ShowCharacter(context.name);
	MagicQuestLog.tracker = MagicQuestLog.Live.New({
		index = MagicQuestLog.Live.Index(quests, deeds),
		completed = live.completed,
		unresolved = live.unresolved,
		onChange = function()
			Characters.SaveLive(live);
			if MagicQuestLog.shown == context.name then MagicQuestLog.ShowCharacter(context.name); end
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
