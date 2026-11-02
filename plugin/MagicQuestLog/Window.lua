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

function Window:Constructor(strings, catalogs)
	Turbine.UI.Lotro.Window.Constructor(self);
	self.strings = strings;
	self.catalogs = catalogs;
	self.kind = "quests";
	self.query = "";
	self.expanded = {};
	self.rows = {};
	self.actions = {};
	self.context = {};
	-- Finished ids for the logged-in character. false means "not known", which is
	-- never the same as "nothing done". A real value is used, not nil: a class
	-- whose unknown fields resolve to methods must not be asked about nil.
	self.completed = false;
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
	self.gold = Turbine.UI.Color(1, 0.9, 0.5);
	self.selectedBack = Turbine.UI.Color(0.16, 0.15, 0.10);

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
	-- One shared status mark for the shown record (the tree uses tiny dots).
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
	self.countLabel:SetPosition(MARGIN, ROW + 28);
	self.countLabel:SetSize(math.max(200, width - MARGIN * 2), 18);

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
	self.mapInfo:SetPosition(detailLeft + 174, self.detailButtonTop + 5);
	self.mapInfo:SetSize(math.max(60, detailWidth - 182), 18);
	for _, row in ipairs(self.rows) do self:Sizes(row.control, row.depth); end
end

function Window:SetKind(kind)
	if self.kind == kind then return; end
	self.kind = kind;
	self.expanded = {};
	self:Rebuild();
end

function Window:Catalog()
	return (self.catalogs or {})[self.kind] or {};
end

function Window:Rebuild(force)
	-- Only kind, query or progress change the tree. Expanding is a display
	-- change, so it must not rebuild and re-sort the whole catalog.
	local key = self.kind .. "\1" .. tostring(self.query) .. "\1" .. (self.completed and "known" or "?")
		.. "\1" .. Model.ContextKey(self.context);
	if force or self.treeCacheKey ~= key or self.root == nil then
		self.root = Model.Build(self:Catalog(), self.query, self.strings, self.completed or nil, self.context);
		self.treeCacheKey = key;
	end
	self.tree:SetSelectedIndex(0);
	self.tree:ClearItems();
	self.rows = {};
	self.actions = {};
	self.countLabel:SetText(self:CountText());
	for _, child in ipairs(self.root.order) do self:AddNode(child, 0, "|"); end
end

--- Headline count. With progress it reports finished of total, and says so.
function Window:CountText()
	local finished = self.completed and self.root.done or nil;
	if finished == nil then
		return self.strings.results .. ": " .. tostring(self.root.total);
	end
	return self.strings.finished .. ": " .. tostring(finished) .. " / " .. tostring(self.root.total)
		.. " " .. self.strings.results;
end

--- Finished ids of the logged-in character. false means unknown, never "none done".
function Window:SetProgress(completed)
	self.completed = completed or false;
	self.treeCacheKey = nil;
	if self.root ~= nil then self:Rebuild(); end
end

function Window:Sizes(control, depth)
	local width = math.max(80, self.tree:GetWidth() - 16);
	control:SetSize(width, control:GetHeight());
	local indent = depth * 14;
	if control.marker then
		control.marker:SetPosition(3 + indent, 5);
	end
	if control.label then
		local left = (control.marker and 18 or 6) + indent;
		control.label:SetPosition(left, 0);
		control.label:SetSize(math.max(20, width - left - 6), control:GetHeight());
	end
	if control.status then
		control.status:SetPosition(3 + indent, 3);
	end
	if control.text then
		local left = 20 + indent;
		control.text:SetPosition(left, 0);
		control.text:SetSize(math.max(20, width - left - 6), 18);
	end
end

function Window:AddRow(control, depth, action)
	self.rows[#self.rows + 1] = { control = control, depth = depth };
	self.tree:AddItem(control);
	self.actions[self.tree:GetItemCount()] = action;
	self:Sizes(control, depth);
end

function Window:AddNode(node, depth, parentPath)
	local path = parentPath .. depth .. "/" .. tostring(node.key);
	local hasChildren = (#node.order > 0) or (#node.items > 0);
	local open = self.expanded[path] == true;
	local row = Turbine.UI.Control();
	row:SetSize(1, 20);
	row:SetBackColor(self.back);
	row:SetMouseVisible(true);
	-- The expander is a chevron texture instead of "[+]"/"[-]" text.
	if hasChildren then
		row.marker = makeImage(row, open and "open" or "closed");
	else
		row.marker = false;
	end
	local label = makeLabel(row, self.body, depth == 0 and self.gold or self.trim);
	label:SetText(node.name .. "   (" .. Model.Counter(node) .. ")");
	label:SetSize(1, 20);
	row.label = label;
	row.status, row.text = false, false;
	self:AddRow(row, depth, function()
		if not hasChildren then return; end
		self.expanded[path] = not open;
		self:Rebuild();
	end);
	if not open then return; end
	for _, child in ipairs(node.order) do self:AddNode(child, depth + 1, path); end
	for _, record in ipairs(node.items) do
		local item = Turbine.UI.Control();
		item:SetSize(1, 18);
		item:SetBackColor(self.back);
		item:SetMouseVisible(true);
		-- A status mark only exists when progress is known: without it every row
		-- would carry a grey circle that says nothing.
		if self.completed then
			local mark = makeImage(item, self.completed[record.id] == true and "done" or "todo");
			mark:SetPosition(3, 1);
			item.status = mark;
		else
			item.status = false;
		end
		item.label = false;
		item.marker = false;
		local text = makeLabel(item, self.body, self.trim);
		text:SetText(record.displayName or record.name);
		text:SetSize(1, 18);
		item.text = text;
		self:AddRow(item, depth + 1, function()
			if self.selectedRow ~= nil then self.selectedRow:SetBackColor(self.back); end
			item:SetBackColor(self.selectedBack);
			self.selectedRow = item;
			self:ShowDetails(record);
		end);
	end
end

function Window:ShowDetails(record)
	-- Every field gets a real value: leaving a key unset would fall through to the
	-- object's own lookup and could look like a set value.
	self.record = record or false;
	if record == nil then
		self.detailTitle:SetText(self.strings.choose);
		self.detailStatus:SetVisible(false);
		self.detailText:SetText("");
		self.mapSlot:SetVisible(false);
		self.mapCover:SetVisible(false);
		self.mapLabel:SetVisible(false);
		self.mapInfo:SetText("");
		self.command = false;
		return;
	end
	self.detailTitle:SetText(record.displayName or record.name);
	if self.completed then
		self.detailStatus:SetVisible(true);
		self.detailStatus:SetDone(self.completed[record.id] == true);
	else
		self.detailStatus:SetVisible(false);
	end
	self.detailText:SetText(Model.Detail(record, self.strings, self.context));
	local target = (record.t or {})[1];
	local command = Model.MapCommand(target, record.displayName or record.name);
	self.command = command or false;
	if command ~= nil then
		self.mapShortcut:SetData(command);
		self.mapSlot:SetShortcut(self.mapShortcut);
		self.mapSlot:SetVisible(true);
		self.mapCover:SetVisible(true);
		self.mapLabel:SetVisible(true);
		self.mapInfo:SetText(Model.Coordinate(target) .. " (" .. self.strings.maphint .. ")");
	else
		self.mapSlot:SetVisible(false);
		self.mapCover:SetVisible(false);
		self.mapLabel:SetVisible(false);
		self.mapInfo:SetText(self.strings.nomap);
	end
end

function Window:SetContext(context)
	self.context = context or {};
	-- Character, class and race change the display text, so the cache must go.
	self.treeCacheKey = nil;
end
