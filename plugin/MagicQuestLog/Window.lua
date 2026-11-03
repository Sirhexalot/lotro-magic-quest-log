import "Turbine";
import "Turbine.UI";
import "Turbine.UI.Lotro";
import "MagicQuestLog.Class";
import "MagicQuestLog.Model";
import "MagicQuestLog.Strings";
import "MagicQuestLog.Settings";

MagicQuestLog = MagicQuestLog or {};

local Model = MagicQuestLog.Model;

-- Icons come from Lucide and are shipped as Targa textures (see
-- MagicQuestLog/icon-sources/NOTICE and tools/build_icons.py). The client paints
-- no SVG, so every icon is a small texture loaded by plugin-relative path.
local ICONS = {
	start = "MagicQuestLog/Resources/start.tga",
	quests = "MagicQuestLog/Resources/quests.tga",
	deeds = "MagicQuestLog/Resources/deeds.tga",
	search = "MagicQuestLog/Resources/search.tga",
	clear = "MagicQuestLog/Resources/clear.tga",
	mappin = "MagicQuestLog/Resources/mappin.tga",
	done = "MagicQuestLog/Resources/done.tga",
	todo = "MagicQuestLog/Resources/todo.tga",
	donebig = "MagicQuestLog/Resources/donebig.tga",
	todobig = "MagicQuestLog/Resources/todobig.tga",
	closed = "MagicQuestLog/Resources/closed.tga",
	open = "MagicQuestLog/Resources/open.tga",
};
-- Each texture is rendered at exactly this size (see tools/build_icons.py); the
-- client resamples plugin textures poorly, so drawing a 24 px icon at 12 px shows.
local ICON_SIZE = { start = 24, quests = 18, deeds = 18, search = 16, clear = 14,
	mappin = 18, closed = 11, open = 11, todo = 12, done = 12, todobig = 18, donebig = 18 };
MagicQuestLog.Icons = ICONS;

--- A texture, optionally clickable. Text stays a Label: no font glyph is used for
--- a symbol, so nothing depends on what the client font happens to contain.
--- Every image is drawn at its own texture size, never scaled.
local function makeImage(parent, name)
	local resource = ICONS[name];
	local size = ICON_SIZE[name];
	assert(resource ~= nil and size ~= nil, "unknown icon: " .. tostring(name));
	local image = Turbine.UI.Control();
	image:SetParent(parent);
	image:SetSize(size, size);
	image:SetMouseVisible(false);
	image:SetBackground(resource);
	return image;
end

-- Status mark: a texture, not a font glyph and not a pixel mosaic. The client's
-- Verdana prints Unicode check and circle marks as a question mark, so the two
-- states come from Lucide's circle and circle-check.
local function makeStatusMark(parent, size)
	local pair = (size >= 18) and { "todobig", "donebig" } or { "todo", "done" };
	local mark = makeImage(parent, pair[1]);
	function mark:SetDone(done)
		self:SetBackground(ICONS[done == true and pair[2] or pair[1]]);
	end
	mark:SetDone(false);
	return mark;
end

local function makeLabel(parent, font, colour)
	local label = Turbine.UI.Label();
	label:SetParent(parent);
	label:SetFont(font);
	label:SetForeColor(colour);
	label:SetMouseVisible(false);
	return label;
end

-- The main window. Uses the standard silver window so frame, title, close button
-- and dragging behave like the rest of the client's UI.
MagicQuestLog.Window = class(Turbine.UI.Lotro.Window);
local Window = MagicQuestLog.Window;

local MARGIN = 14;
-- The standard window paints a title bar above its client area; anything at y<30
-- ends up underneath it. Keep the whole header below that bar.
local TITLEBAR = 30;
local ROW = TITLEBAR + 6;
local HEADER = ROW + 28;
local FOOTER = 16;

-- Row heights in whole lines. A name that does not fit the tree column must not
-- run into the row below it, so the row grows instead of clipping: one line, then
-- one more line for each 20 px, at most four lines. The longest catalog name is 95
-- characters, so that is more than enough.
local LINE = 20;

function Window:Constructor(strings, catalogs)
	Turbine.UI.Lotro.Window.Constructor(self);
	self.strings = strings;
	self.catalogs = catalogs;
	self.kind = "quests";
	self.query = "";
	self.expanded = {};
	self.rows = {};
	self.actions = {};
	-- Row height per text and column width, so expanding or resizing does not ask
	-- the client for the same measurement twice.
	self.heights = {};
	-- Last highlighted tree row. A real value, not nil: a class whose unknown
	-- fields resolve to methods would hand back a function here.
	self.highlighted = false;
	self.context = {};
	-- Finished ids for the logged-in character. false means "not known", which is
	-- never the same as "nothing done". A real value is used, not nil: a class
	-- whose unknown fields resolve to methods must not be asked about nil.
	self.completed = false;
	self.progressExact = false;
	-- Running counters from the import and the character's level, both false when
	-- unknown. Settings decide the list filter and whether objectives show.
	self.running = false;
	self.level = false;
	local stored = MagicQuestLog.Settings.Get();
	self.filter = stored.filter or "all";
	self.showObjectives = stored.showObjectives == true;
	-- The built tree is cached; expanding a node must not rebuild and re-sort
	-- 15k records again.
	self.treeCacheKey = nil;
	self.root = nil;

	-- The description was too small at Verdana12. Title leads, body follows.
	self.font = Turbine.UI.Lotro.Font.Verdana16;
	self.body = Turbine.UI.Lotro.Font.Verdana14;
	self.small = Turbine.UI.Lotro.Font.Verdana12;
	self.back = Turbine.UI.Color(0.05, 0.05, 0.05);
	self.trim = Turbine.UI.Color(0.78, 0.78, 0.78);
	self.dim = Turbine.UI.Color(0.45, 0.45, 0.45);
	self.gold = Turbine.UI.Color(1, 0.9, 0.5);
	self.selectedBack = Turbine.UI.Color(0.16, 0.15, 0.10);
	self.headerBack = Turbine.UI.Color(0.11, 0.10, 0.08);
	-- Folded list sections, by node path and section name.
	self.folded = {};

	-- Ruler for wrapped tree text. A label reports no text metrics, but a label
	-- bound to a vertical scroll bar reports overflow: the bar is visible only while
	-- the text is taller than the label. MoorMap's FontMetric measures the same way.
	-- Nothing is estimated unless that report turns out to be unavailable. The value
	-- is a real string, never nil: on this class an unset field reads back as a
	-- method, which would look like a working ruler.
	self.rulerWorks = "unknown";
	-- Height of a single line, measured once: a client with a larger font scale needs
	-- taller rows, and an assumed 20 px would make every name look wrapped.
	self.lineHeight = "unknown";
	self.ruler = makeLabel(self, self.body, self.trim);
	self.ruler:SetMultiline(true);
	self.ruler:SetPosition(0, 0);
	self.ruler:SetSize(LINE, LINE);
	self.ruler:SetOpacity(0);
	self.rulerBar = Turbine.UI.Lotro.ScrollBar();
	self.rulerBar:SetOrientation(Turbine.UI.Orientation.Vertical);
	self.rulerBar:SetParent(self);
	self.rulerBar:SetSize(12, LINE);
	self.rulerBar:SetPosition(0, 0);
	self.rulerBar:SetOpacity(0);
	self.ruler:SetVerticalScrollBar(self.rulerBar);

	local settings = MagicQuestLog.Settings.Get();
	local width, height = 1020, 640;
	local display = Turbine.UI.Display;
	width = math.min(width, display:GetWidth() - 40);
	height = math.min(height, display:GetHeight() - 40);
	local left = settings.windowLeft or math.floor((display:GetWidth() - width) / 2);
	local top = settings.windowTop or math.floor((display:GetHeight() - height) / 2);
	self:SetSize(width, height);
	self:SetPosition(left, top);
	self:SetText(strings.title .. "            ");
	self:SetResizable(false);
	self:SetOpacity(1);
	self:SetMouseVisible(true);
	self:SetVisible(settings.windowVisible);

	self.kindQuest = Turbine.UI.Lotro.Button();
	self.kindDeed = Turbine.UI.Lotro.Button();
	for _, button in ipairs({ self.kindQuest, self.kindDeed }) do
		button:SetParent(self);
		button:SetSize(120, 22);
		button:SetFont(self.small);
	end
	self.kindQuest:SetText(strings.quests);
	self.kindDeed:SetText(strings.deeds);
	self.kindQuest.Click = function() self:SetKind("quests"); end;
	self.kindDeed.Click = function() self:SetKind("deeds"); end;
	self.kindQuestIcon = makeImage(self, "quests");
	self.kindDeedIcon = makeImage(self, "deeds");

	self.searchIcon = makeImage(self, "search");
	self.searchLabel = makeLabel(self, self.small, self.gold);
	self.searchLabel:SetText(strings.search);

	self.searchBox = Turbine.UI.Lotro.TextBox();
	self.searchBox:SetParent(self);
	self.searchBox:SetFont(self.small);
	self.searchBox:SetTextAlignment(Turbine.UI.ContentAlignment.MiddleLeft);
	self.searchBox:SetMultiline(false);
	self.searchBox:SetMouseVisible(true);
	self.searchBox.TextChanged = function()
		local text = self.searchBox:GetText();
		if text ~= self.query then
			self.query = text;
			self:Rebuild();
		end
	end

	self.clearButton = Turbine.UI.Lotro.Button();
	self.clearButton:SetParent(self);
	self.clearButton:SetSize(80, 22);
	self.clearButton:SetFont(self.small);
	self.clearButton:SetText(strings.clear);
	self.clearButton.Click = function()
		self.searchBox:SetText("");
		self.query = "";
		self:Rebuild();
	end
	self.clearIcon = makeImage(self, "clear");

	self.countLabel = makeLabel(self, self.small, self.trim);

	-- Character switch: any character of this server that has progress. A click
	-- moves to the next one; the label says whose numbers are shown and how old the
	-- import is.
	self.characterButton = Turbine.UI.Lotro.Button();
	self.characterButton:SetParent(self);
	self.characterButton:SetSize(150, 20);
	self.characterButton:SetFont(self.small);
	self.characterButton:SetText(strings.character);
	self.characterButton.Click = function()
		if self.CharacterClicked then self.CharacterClicked(); end
	end
	self.characterLabel = makeLabel(self, self.small, self.trim);
	self.characterLabel:SetTextAlignment(Turbine.UI.ContentAlignment.MiddleRight);

	self.tree = Turbine.UI.ListBox();
	self.tree:SetParent(self);
	self.tree:SetBackColor(self.back);
	self.tree:SetMouseVisible(true);
	self.treeScroll = Turbine.UI.Lotro.ScrollBar();
	self.treeScroll:SetOrientation(Turbine.UI.Orientation.Vertical);
	self.treeScroll:SetParent(self.tree);
	self.treeScroll:SetBackColor(self.back);
	self.treeScroll:SetWidth(12);
	self.tree:SetVerticalScrollBar(self.treeScroll);
	-- List selection is the click path the client already uses elsewhere.
	self.tree.SelectedIndexChanged = function()
		local index = self.tree:GetSelectedIndex();
		self.tree:SetSelectedIndex(0);
		if index == nil or index == 0 then return; end
		local action = self.actions[index];
		if action ~= nil then action(); end
	end

	self.detailTitle = makeLabel(self, self.font, self.gold);
	self.detailTitle:SetSelectable(true);
	self.detailTitle:SetMultiline(true);
	-- One shared status mark for the shown record (the tree uses its own marks).
	self.detailStatus = makeStatusMark(self, 18);
	self.detailStatus:SetVisible(false);
	self.detailText = makeLabel(self, self.body, self.trim);
	self.detailText:SetSelectable(true);
	self.detailText:SetMultiline(true);
	self.detailScroll = Turbine.UI.Lotro.ScrollBar();
	self.detailScroll:SetOrientation(Turbine.UI.Orientation.Vertical);
	self.detailScroll:SetParent(self);
	self.detailScroll:SetBackColor(self.back);
	self.detailScroll:SetWidth(12);
	self.detailText:SetVerticalScrollBar(self.detailScroll);

	-- The pin sits on top of the quickslot as a click-through cover: the slot has to
	-- stay clickable (it is what fires MoorMap), but it also prints the alias text
	-- inside itself, which looks like a broken button. Both cover and icon ignore
	-- the mouse, so the click reaches the slot underneath.
	self.mapSlot = Turbine.UI.Lotro.Quickslot();
	self.mapSlot:SetParent(self);
	self.mapSlot:SetSize(22, 22);
	self.mapSlot:SetAllowDrop(false);
	self.mapSlot:SetVisible(false);
	self.mapShortcut = Turbine.UI.Lotro.Shortcut(Turbine.UI.Lotro.ShortcutType.Alias, "");
	self.mapShortcut:SetData("");
	self.mapSlot:SetShortcut(self.mapShortcut);
	self.mapSlot.DragDrop = function() self.mapSlot:SetShortcut(self.mapShortcut); end;
	self.mapCover = Turbine.UI.Control();
	self.mapCover:SetParent(self);
	self.mapCover:SetSize(22, 22);
	self.mapCover:SetBackColor(self.back);
	self.mapCover:SetMouseVisible(false);
	self.mapCover:SetVisible(false);
	self.mapIcon = makeImage(self.mapCover, "mappin");
	self.mapIcon:SetPosition(2, 2);
	self.mapLabel = makeLabel(self, self.small, self.gold);
	self.mapLabel:SetText(strings.showmap);
	self.mapInfo = makeLabel(self, self.small, self.trim);

	-- List filter: one button that steps through all, open, done and available.
	self.filterButton = Turbine.UI.Lotro.Button();
	self.filterButton:SetParent(self);
	self.filterButton:SetSize(150, 20);
	self.filterButton:SetFont(self.small);
	self.filterButton.Click = function()
		local order = { "all", "open", "done", "available" };
		local nextFilter = "all";
		for position, name in ipairs(order) do
			if name == self.filter then nextFilter = order[position % #order + 1]; end
		end
		-- "available" means nothing for deeds or without progress: skip it there.
		if nextFilter == "available" and (self.kind ~= "quests" or not self.completed) then nextFilter = "all"; end
		self:SetFilter(nextFilter);
	end

	-- Objectives and steps stay hidden until asked for, so the solution is not in
	-- view right away. The choice is kept.
	self.stepsButton = Turbine.UI.Lotro.Button();
	self.stepsButton:SetParent(self);
	self.stepsButton:SetSize(140, 20);
	self.stepsButton:SetFont(self.small);
	self.stepsButton.Click = function()
		self.showObjectives = not self.showObjectives;
		local settingsNow = MagicQuestLog.Settings.Get();
		settingsNow.showObjectives = self.showObjectives;
		MagicQuestLog.Settings.Save();
		if self.record then self:ShowDetails(self.record); end
	end

	-- First unfinished requirement: puts its name into the search.
	self.findButton = Turbine.UI.Lotro.Button();
	self.findButton:SetParent(self);
	self.findButton:SetSize(150, 20);
	self.findButton:SetFont(self.small);
	self.findButton:SetText(strings.findreq);
	self.findButton:SetVisible(false);
	self.findButton.Click = function()
		if self.findName then self.searchBox:SetText(self.findName); end
	end

	self:Layout();
	self.SizeChanged = function() self:Layout(); end;
	self.PositionChanged = function()
		local settingsNow = MagicQuestLog.Settings.Get();
		settingsNow.windowLeft = self:GetLeft();
		settingsNow.windowTop = self:GetTop();
		MagicQuestLog.Settings.Save();
	end;
	self.VisibleChanged = function()
		local settingsNow = MagicQuestLog.Settings.Get();
		settingsNow.windowVisible = self:IsVisible();
		MagicQuestLog.Settings.Save();
		-- A hidden window cannot measure wrapped text; once it is on screen the
		-- rows are measured for real instead of estimated from their length.
		if self:IsVisible() then
			self:Remeasure();
			-- A new import may have arrived while the window was closed.
			if self.Shown then self.Shown(); end
		end
	end;
	self:ShowDetails(nil);
	self:Rebuild();
end

function Window:Layout()
	local width, height = self:GetWidth(), self:GetHeight();
	self.kindQuestIcon:SetPosition(MARGIN + 8, ROW);
	self.kindQuest:SetPosition(MARGIN + 30, ROW);
	self.kindDeedIcon:SetPosition(MARGIN + 156, ROW);
	self.kindDeed:SetPosition(MARGIN + 178, ROW);
	local labelLeft = MARGIN + 306;
	self.searchIcon:SetPosition(labelLeft, ROW + 2);
	self.searchLabel:SetPosition(labelLeft + 22, ROW + 2);
	self.searchLabel:SetSize(60, 18);
	local boxLeft = labelLeft + 88;
	self.clearButton:SetPosition(width - MARGIN - 80, ROW);
	self.clearIcon:SetPosition(width - MARGIN - 72, ROW + 4);
	self.searchBox:SetPosition(boxLeft, ROW);
	self.searchBox:SetSize(math.max(120, width - MARGIN - 80 - 8 - boxLeft), 20);
	self.filterButton:SetPosition(MARGIN, ROW + 26);
	self.countLabel:SetPosition(MARGIN + 160, ROW + 28);
	self.countLabel:SetSize(math.max(200, width - MARGIN * 2 - 630), 18);
	self.characterButton:SetPosition(width - MARGIN - 150, ROW + 26);
	self.characterLabel:SetPosition(width - MARGIN - 470, ROW + 28);
	self.characterLabel:SetSize(310, 18);

	local bodyTop = HEADER + 22;
	local bodyHeight = math.max(120, height - bodyTop - MARGIN - FOOTER);
	local treeWidth = math.max(260, math.floor((width - MARGIN * 3) * 0.44));
	self.tree:SetPosition(MARGIN, bodyTop);
	self.tree:SetSize(treeWidth, bodyHeight);
	self.treeScroll:SetPosition(treeWidth - 14, 0);
	self.treeScroll:SetHeight(bodyHeight - 2);

	local detailLeft = MARGIN + treeWidth + 24;
	local detailWidth = math.max(200, width - detailLeft - MARGIN);
	self.detailTitle:SetPosition(detailLeft, bodyTop);
	self.detailTitle:SetSize(detailWidth - 30, 46);
	self.detailStatus:SetPosition(detailLeft + detailWidth - 24, bodyTop + 2);
	self.detailButtonTop = bodyTop + bodyHeight - 30;
	self.detailText:SetPosition(detailLeft, bodyTop + 52);
	local textHeight = math.max(60, self.detailButtonTop - (bodyTop + 52) - 8);
	self.detailText:SetSize(detailWidth - 14, textHeight);
	self.detailScroll:SetPosition(detailLeft + detailWidth - 14, bodyTop + 52);
	self.detailScroll:SetHeight(textHeight);
	self.mapSlot:SetPosition(detailLeft, self.detailButtonTop);
	self.mapCover:SetPosition(detailLeft, self.detailButtonTop);
	self.mapIcon:SetPosition(2, 2);
	self.mapLabel:SetPosition(detailLeft + 30, self.detailButtonTop + 5);
	self.mapLabel:SetSize(140, 18);
	self.stepsButton:SetPosition(detailLeft + detailWidth - 140, self.detailButtonTop + 2);
	self.findButton:SetPosition(detailLeft + detailWidth - 296, self.detailButtonTop + 2);
	self.mapInfo:SetPosition(detailLeft + 174, self.detailButtonTop + 5);
	self.mapInfo:SetSize(math.max(60, detailWidth - 182 - 304), 18);
	for _, row in ipairs(self.rows) do self:Sizes(row.control, row.depth); end
end

function Window:SetFilter(filter)
	self.filter = filter;
	local settingsNow = MagicQuestLog.Settings.Get();
	settingsNow.filter = filter;
	MagicQuestLog.Settings.Save();
	self:Rebuild();
end

function Window:SetKind(kind)
	if self.kind == kind then return; end
	self.kind = kind;
	if self.filter == "available" and kind ~= "quests" then self.filter = "all"; end
	self.expanded = {};
	-- The right pane belonged to the other kind: a quest left open next to a deed
	-- tree reads like a wrong entry, so it goes back to the prompt.
	self:ShowDetails(nil);
	self:Rebuild();
end

function Window:Catalog()
	return (self.catalogs or {})[self.kind] or {};
end

function Window:Rebuild(force)
	-- Only kind, query or progress change the tree. Expanding is a display
	-- change, so it must not rebuild and re-sort the whole catalog.
	local key = self.kind .. "\1" .. tostring(self.query) .. "\1" .. (self.completed and "known" or "?")
		.. "\1" .. Model.ContextKey(self.context) .. "\1" .. self.filter .. "\1" .. tostring(self.level);
	if force or self.treeCacheKey ~= key or self.root == nil then
		self.root = Model.Build(self:Catalog(), self.query, self.strings, self.completed or nil, self.context,
			{ filter = self.filter, level = self.level or nil });
		self.treeCacheKey = key;
	end
	self.tree:SetSelectedIndex(0);
	self.tree:ClearItems();
	self.rows = {};
	self.actions = {};
	self.countLabel:SetText(self:CountText());
	self.filterButton:SetText(self.strings.filter .. ": " .. self.strings["filter" .. self.filter]);
	for _, child in ipairs(self.root.order) do self:AddNode(child, 0, "|"); end
end

--- Headline count. With progress it reports finished of total, and says so. A set
--- that only holds live completions cannot know older history, so it is labelled
--- as partial instead of claiming a full count.
function Window:CountText()
	local finished = self.completed and self.root.done or nil;
	if finished == nil then
		return self.strings.results .. ": " .. tostring(self.root.total);
	end
	local label = self.progressExact and self.strings.finished or self.strings.finishedknown;
	return label .. ": " .. tostring(finished) .. " / " .. tostring(self.root.total)
		.. " " .. self.strings.results;
end

--- Finished ids of the logged-in character. false means unknown, never "none done".
--- "exact" tells whether that set can be complete; a live session alone cannot.
function Window:SetProgress(completed, exact, running, level)
	self.completed = completed or false;
	self.progressExact = exact == true;
	self.running = running or false;
	self.level = tonumber(level) or false;
	if not self.completed and self.filter ~= "all" then self.filter = "all"; end
	self.treeCacheKey = nil;
	if self.root ~= nil then self:Rebuild(); end
end

--- Can this client report wrapped text at all? The scroll bar bound to the ruler is
--- the only available answer. A hidden window cannot answer, so the question stays
--- open until it is on screen.
function Window:RulerWorks()
	if self.rulerWorks ~= "unknown" then return self.rulerWorks == true; end
	if not self:IsVisible() then return false; end
	self.ruler:SetWidth(40);
	self.ruler:SetHeight(LINE);
	self.ruler:SetText(string.rep("Schatzsuche ", 8));
	self.rulerWorks = self.rulerBar:IsVisible() == true;
	self.ruler:SetText("");
	return self.rulerWorks;
end

--- Height of one line of tree text, measured once with a word that cannot wrap.
--- A client whose font needs more than the assumed LINE gets taller rows from the
--- start instead of every row being judged as two lines.
function Window:LineHeight()
	if self.lineHeight ~= "unknown" then return self.lineHeight; end
	if not self:RulerWorks() then return LINE; end
	self.ruler:SetWidth(400);
	self.ruler:SetText("Agarnaith");
	local height = LINE;
	for candidate = 8, 80, 2 do
		height = candidate;
		self.ruler:SetHeight(candidate);
		if not self.rulerBar:IsVisible() then break; end
	end
	self.ruler:SetText("");
	self.lineHeight = math.max(LINE, height);
	return self.lineHeight;
end

--- Height one tree row needs for this text in this column. The client wraps the real
--- text with the real font, so nothing about the break is guessed. Without a working
--- ruler the length is counted instead: 9 px per character is above the average
--- glyph width of Verdana14, so the estimate errs towards a taller row, never a
--- clipped name.
function Window:RowHeight(text, width)
	text = tostring(text or "");
	width = math.max(LINE, tonumber(width) or LINE);
	local key = text .. "\1" .. tostring(width);
	local known = self.heights[key];
	if known ~= nil then return known; end
	local base = self:LineHeight();
	local height = base;
	if self:RulerWorks() then
		self.ruler:SetWidth(width);
		self.ruler:SetText(text);
		for step = 0, 3 do
			height = base + step * LINE;
			self.ruler:SetHeight(height);
			if not self.rulerBar:IsVisible() then break; end
		end
		self.ruler:SetText("");
	else
		local perLine = math.max(8, math.floor(width / 9));
		local lines = math.min(4, math.max(1, math.ceil(#text / perLine)));
		height = base + (lines - 1) * LINE;
	end
	self.heights[key] = height;
	return height;
end

--- Rows measured while the window was hidden used the fallback; once it is visible
--- the real ruler decides, so the cached heights are dropped and rebuilt.
function Window:Remeasure()
	self.heights = {};
	if self.root ~= nil then self:Rebuild(); end
end

function Window:Sizes(control, depth)
	local width = math.max(80, self.tree:GetWidth() - 16);
	local indent = depth * 14;
	local markerLeft = 3 + indent;
	local labelLeft = (control.marker and 18 or 6) + indent;
	local textLeft = 20 + indent;
	local height = control:GetHeight();
	-- A wrapped name needs a taller row; a row that stays one line high would let
	-- the second line run into the row below it.
	if control.label then
		height = self:RowHeight(control.label:GetText(), math.max(20, width - labelLeft - 6));
	end
	if control.text then
		height = self:RowHeight(control.text:GetText(), math.max(20, width - textLeft - 6));
	end
	control:SetSize(width, height);
	if control.marker then
		control.marker:SetPosition(markerLeft, 5);
	end
	if control.label then
		control.label:SetPosition(labelLeft, 0);
		control.label:SetSize(math.max(20, width - labelLeft - 6), height);
	end
	if control.status then
		control.status:SetPosition(markerLeft, 3);
	end
	if control.text then
		control.text:SetPosition(textLeft, 0);
		control.text:SetSize(math.max(20, width - textLeft - 6), height);
	end
end

function Window:AddRow(control, depth, action)
	-- Size first: the list box stacks its items by the height they already have.
	self:Sizes(control, depth);
	self.rows[#self.rows + 1] = { control = control, depth = depth };
	self.tree:AddItem(control);
	self.actions[self.tree:GetItemCount()] = action;
end

function Window:AddNode(node, depth, parentPath)
	local path = parentPath .. depth .. "/" .. tostring(node.key);
	local hasChildren = (#node.order > 0) or (#node.items > 0);
	local open = self.expanded[path] == true;
	local row = Turbine.UI.Control();
	row:SetSize(1, LINE);
	row:SetBackColor(self.back);
	row:SetMouseVisible(true);
	-- The expander is a chevron texture instead of "[+]"/"[-]" text.
	if hasChildren then
		row.marker = makeImage(row, open and "open" or "closed");
	else
		row.marker = false;
	end
	local label = makeLabel(row, self.body, depth == 0 and self.gold or self.trim);
	label:SetMultiline(true);
	local caption = node.name .. "   (" .. Model.Counter(node) .. ")";
	-- Level range on areas (second level) only; deeper rows would double the tree.
	if depth == 1 and node.range ~= nil then caption = caption .. "   " .. self.strings.level .. " " .. node.range; end
	label:SetText(caption);
	label:SetSize(1, LINE);
	row.label = label;
	row.status, row.text = false, false;
	self:AddRow(row, depth, function()
		self:ShowNode(node);
		if not hasChildren then return; end
		self.expanded[path] = not open;
		self:Rebuild();
	end);
	if not open then return; end
	for _, child in ipairs(node.order) do self:AddNode(child, depth + 1, path); end
	-- Section headers inside an area: "General" for its own entries, then
	-- sub-areas and quest groups. A click folds a section.
	local counts, sectioned = {}, false;
	for _, record in ipairs(node.items) do
		counts[record.section or ""] = (counts[record.section or ""] or 0) + 1;
		if (record.section or "") ~= "" then sectioned = true; end
	end
	local current = nil;
	for _, record in ipairs(node.items) do
		local section = record.section or "";
		local key = path .. "#" .. section;
		if sectioned and section ~= current then
			current = section;
			local header = Turbine.UI.Control();
			header:SetSize(1, LINE);
			header:SetBackColor(self.headerBack);
			header:SetMouseVisible(true);
			header.marker = makeImage(header, self.folded[key] and "closed" or "open");
			local caption = section == "" and self.strings.general or section;
			local label = makeLabel(header, self.small, self.gold);
			label:SetMultiline(true);
			label:SetText(caption .. "   (" .. tostring(counts[section]) .. ")");
			label:SetSize(1, LINE);
			header.label = label;
			header.status, header.text = false, false;
			self:AddRow(header, depth + 1, function()
				self.folded[key] = not self.folded[key];
				self:Rebuild();
			end);
		end
		if not (sectioned and self.folded[key]) then
		local item = Turbine.UI.Control();
		item:SetSize(1, LINE);
		item:SetBackColor(self.back);
		item:SetMouseVisible(true);
		-- A status mark only exists when progress is known: without it every row
		-- would carry a grey circle that says nothing. Entries that are not counted
		-- get no mark at all - a circle would claim they are still open.
		if self.completed and not record.sessionPlay and not record.excluded then
			local mark = makeImage(item, self.completed[record.id] == true and "done" or "todo");
			mark:SetPosition(3, 1);
			item.status = mark;
		else
			item.status = false;
		end
		item.label = false;
		item.marker = false;
		local text = makeLabel(item, self.body, self.trim);
		text:SetMultiline(true);
		-- An entry that cannot be counted says so next to its name: a session play
		-- the game never records, or one the finished alternative rules out. Both
		-- are dimmed so the eye skips them when reading the numbers.
		local name = record.displayName or record.name;
		if record.twin and record.g ~= nil then name = name .. "  –  " .. record.g; end
		local levelText = Model.LevelText(record);
		if levelText ~= nil then name = name .. "   · " .. levelText; end
		if self.running and self.running[record.id] ~= nil and not (self.completed and self.completed[record.id]) then
			name = name .. "   (" .. self.strings.inprogress .. ")";
		end
		if record.sessionPlay then
			text:SetForeColor(self.dim);
			name = name .. "   (" .. self.strings.sessionplay .. ")";
		elseif record.excluded then
			text:SetForeColor(self.dim);
			name = name .. "   (" .. self.strings.alternative .. ")";
		end
		text:SetText(name);
		text:SetSize(1, LINE);
		item.text = text;
		self:AddRow(item, depth + 1 + (sectioned and 1 or 0), function()
			if self.highlighted then self.highlighted:SetBackColor(self.back); end
			item:SetBackColor(self.selectedBack);
			self.highlighted = item;
			self:ShowDetails(record);
		end);
		end
	end
end

--- Set the detail text and put the pane back at the top.
--- A scroll bar bound to a label is driven by the label; the client rejects
--- SetValue on it. Unbinding, setting and rebinding resets the offset instead.
function Window:SetDetailText(text)
	self.detailText:SetVerticalScrollBar(nil);
	self.detailText:SetText(text);
	self.detailText:SetVerticalScrollBar(self.detailScroll);
end

function Window:ShowDetails(record)
	-- Every field gets a real value: leaving a key unset would fall through to the
	-- object's own lookup and could look like a set value.
	self.record = record or false;
	if record == nil then
		self.detailTitle:SetText(self.strings.choose);
		self.detailStatus:SetVisible(false);
		self:SetDetailText("");
		self.mapSlot:SetVisible(false);
		self.mapCover:SetVisible(false);
		self.mapLabel:SetVisible(false);
		self.mapInfo:SetText("");
		self.command = false;
		self.stepsButton:SetVisible(false);
		self.findButton:SetVisible(false);
		return;
	end
	self.detailTitle:SetText(record.displayName or record.name);
	if self.completed then
		self.detailStatus:SetVisible(true);
		self.detailStatus:SetDone(self.completed[record.id] == true);
	else
		self.detailStatus:SetVisible(false);
	end
	-- Unbinding, setting and rebinding is how a scrolled label is reset to the top.
	-- SetValue on a bound scroll bar is refused by the client and threw an error.
	local deed = self.kind == "deeds";
	local showSteps = self.showObjectives or deed;
	self:SetDetailText(Model.Detail(record, self.strings, self.context, {
		completed = self.completed or nil, level = self.level or nil,
		byId = self.root and self.root.byId or nil,
		running = self.running and self.running[record.id] or nil,
		showSteps = showSteps, deed = deed }));
	self.stepsButton:SetText(self.showObjectives and self.strings.hidesteps or self.strings.showsteps);
	self.stepsButton:SetVisible(not deed and record.s ~= nil and #record.s > 0);
	-- First unfinished requirement, for the search button.
	self.findName = false;
	if self.completed then
		local byId = self.root and self.root.byId or {};
		for _, id in ipairs(record.v or {}) do
			if not self.completed[id] and byId[id] ~= nil then
				self.findName = byId[id].displayName or byId[id].name;
				break;
			end
		end
	end
	self.findButton:SetVisible(self.findName ~= false);
	-- By default MoorMap points at the quest giver, not at the objective.
	local target, which = nil, nil;
	if showSteps then
		target, which = (record.t or {})[1], self.strings.targetpos;
	elseif record.gt ~= nil then
		target, which = record.gt, self.strings.giverpos;
	end
	local command = Model.MapCommand(target, record.displayName or record.name);
	self.command = command or false;
	if command ~= nil then
		self.mapShortcut:SetData(command);
		self.mapSlot:SetShortcut(self.mapShortcut);
		self.mapSlot:SetVisible(true);
		self.mapCover:SetVisible(true);
		self.mapLabel:SetVisible(true);
		self.mapInfo:SetText(which .. ": " .. Model.Coordinate(target));
	else
		self.mapSlot:SetVisible(false);
		self.mapCover:SetVisible(false);
		self.mapLabel:SetVisible(false);
		self.mapInfo:SetText(showSteps and self.strings.nomap or self.strings.nogiver);
	end
end

--- Right-hand pane for an area: level range and counts, no map button.
function Window:ShowNode(node)
	self.record = false;
	self.detailTitle:SetText(node.name);
	self.detailStatus:SetVisible(false);
	self:SetDetailText(Model.NodeSummary(node, self.strings, self.completed or nil, self.level or nil,
		self.running or nil));
	self.mapSlot:SetVisible(false);
	self.mapCover:SetVisible(false);
	self.mapLabel:SetVisible(false);
	self.mapInfo:SetText("");
	self.stepsButton:SetVisible(false);
	self.findButton:SetVisible(false);
	self.command = false;
end

--- Whose progress is shown. "date" is the day of the Companion import, if any;
--- "current" says whether this is the logged-in character, the only one whose
--- completions come in live.
function Window:SetCharacter(name, date, current)
	self.characterName = name or false;
	self.characterButton:SetText(name or self.strings.character);
	local parts = {};
	if date ~= nil then parts[#parts + 1] = self.strings.importedon .. " " .. date; end
	if current then parts[#parts + 1] = self.strings.livenow; end
	self.characterLabel:SetText(table.concat(parts, " · "));
end

function Window:SetContext(context)
	self.context = context or {};
	-- Character, class and race change the display text, so the cache must go.
	self.treeCacheKey = nil;
end
