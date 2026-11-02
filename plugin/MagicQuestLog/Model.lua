-- Pure logic: no Turbine API, no I/O. Covered by the headless test suite.
MagicQuestLog = MagicQuestLog or {};
local M = {};
MagicQuestLog.Model = M;

local FOLDS = {
	a = { "Ä","ä","À","à","Á","á","Â","â","Ã","ã","Å","å" },
	o = { "Ö","ö","Ô","ô","Ó","ó","Ò","ò" },
	u = { "Ü","ü","Û","û","Ù","ù","Ú","ú" },
	e = { "É","é","È","è","Ê","ê","Ë","ë" },
	i = { "Î","î","Ï","ï","Í","í","Ì","ì" },
	c = { "Ç","ç" }, ss = { "ß","ẞ" }, oe = { "Œ","œ" }, ae = { "Æ","æ" }, n = { "Ñ","ñ" },
};

--- Case- and accent-insensitive form used for search only.
function M.Normalize(text)
	text = tostring(text or "");
	for replacement, characters in pairs(FOLDS) do
		for _, character in ipairs(characters) do text = string.gsub(text, character, replacement); end
	end
	return string.lower(text);
end

--- "@key" is a UI string; anything else is already localized game text.
function M.Caption(name, strings)
	if string.sub(name, 1, 1) ~= "@" then return name; end
	local body = string.sub(name, 2);
	local key, argument = string.match(body, "^(%w+):(.+)$");
	if key == "volume" then return (strings.volume or "Volume") .. " " .. argument; end
	return strings[body] or body;
end

--- Display form of any catalog text: captions resolved, then placeholders from the
--- game text filled in. Some quest and group names carry them literally
--- ("${PLAYERNAME:Runebewahrer[im]|Runebewahrerin[f]}"), and a raw placeholder in a
--- tree row is useless to read.
function M.Display(text, context, strings)
	return (M.Resolve(M.Caption(text, strings), context, strings));
end

--- Context changes are rare but they do change the display text, so cached text is
--- keyed by them rather than simply kept.
function M.ContextKey(context)
	context = context or {};
	return tostring(context.name) .. "|" .. tostring(context.charclass) .. "|" .. tostring(context.race);
end

--- Sort key: accent/case-insensitive, numbers padded so "Kapitel 2" sorts before
--- "Kapitel 10". Computed once per record and per node, never inside a comparator:
--- a comparator must not do string work, the catalog has 15k+ entries.
function M.SortKey(text)
	return (string.gsub(M.Normalize(text), "%d+", function(number)
		return string.format("%09d", tonumber(number) or 0);
	end));
end

--- Build the visible tree. Search matches the name only, as a literal substring.
--- "completed" is an optional set of finished ids; when given, every node also
--- counts how many of its entries are finished, so the tree can show "n/total".
--- Without that set no count is invented: done stays nil.
function M.Build(records, query, strings, completed, context)
	local root = { key = "root", name = "root", children = {}, order = {}, items = {}, total = 0 };
	if completed ~= nil then root.done = 0; end
	local key = M.ContextKey(context);
	local function display(record)
		if record.displayKey ~= key then
			record.displayName = M.Display(record.name, context, strings);
			record.searchText = M.Normalize(record.displayName);
			record.sortKey = M.SortKey(record.displayName);
			record.displayKey = key;
		end
		return record.displayName;
	end
	local needle = M.Normalize(query or "");
	for _, record in ipairs(records or {}) do
		local name = display(record);
		if needle == "" or string.find(record.searchText, needle, 1, true) ~= nil then
			local finished = completed ~= nil and completed[record.id] == true;
			root.total = root.total + 1;
			if finished then root.done = root.done + 1; end
			local node = root;
			for _, part in ipairs(record.p or {}) do
				local child = node.children[part.k];
				if child == nil then
					local caption = M.Display(part.n, context, strings);
					child = { key = part.k, name = caption, sortKey = M.SortKey(caption),
						children = {}, order = {}, items = {}, total = 0 };
					if completed ~= nil then child.done = 0; end
					node.children[part.k] = child;
					table.insert(node.order, child);
				end
				child.total = child.total + 1;
				if finished then child.done = child.done + 1; end
				node = child;
			end
			table.insert(node.items, record);
		end
	end
	local function sort(node)
		table.sort(node.order, function(a, b) return a.sortKey < b.sortKey; end);
		table.sort(node.items, function(a, b) return a.sortKey < b.sortKey; end);
		for _, child in ipairs(node.order) do sort(child); end
	end
	sort(root);
	return root;
end

--- Counter text for a tree node: "n/total" with progress, "total" without.
function M.Counter(node)
	if node.done == nil then return tostring(node.total); end
	return tostring(node.done) .. "/" .. tostring(node.total);
end

--- Human-readable game coordinate, e.g. "75.64S, 24.61W".
function M.Coordinate(target)
	if target == nil or target.lat == nil or target.lon == nil then return ""; end
	return string.format("%.2f%s, %.2f%s", math.abs(target.lat), target.lat < 0 and "S" or "N",
		math.abs(target.lon), target.lon < 0 and "W" or "E");
end

--- MoorMap command for a verified position. Malformed input yields nil, never a guess.
function M.MapCommand(target, questName)
	if target == nil or type(target.map) ~= "number" or type(target.lat) ~= "number" or type(target.lon) ~= "number" then
		return nil;
	end
	local function safe(text) return (string.gsub(tostring(text or ""), "[:\r\n<>]", " ")); end
	return string.format("/moormap ping %d:%.5f:%.5f:%s:%s",
		target.map, target.lat, target.lon, safe(target.n), safe(questName));
end

--- Which character properties the plugin may use. The public API has no sex getter,
--- so gender-dependent wording is never inferred from a name.
function M.Context(player, classEnum, raceEnum)
	local context = {};
	if player == nil then return context; end
	local function take(method)
		local ok, value = pcall(function() return player[method](player); end);
		if ok then return value; end
		return nil;
	end
	local name = take("GetName");
	if type(name) == "string" and name ~= "" then context.name = name; end
	local classValue, raceValue = take("GetClass"), take("GetRace");
	local classes = { Burglar="Schurke", Captain="Hauptmann", Champion="Waffenmeister", Guardian="Wächter",
		Hunter="Jäger", LoreMaster="Kundiger", Minstrel="Barde", RuneKeeper="Runenbewahrer", Warden="Hüter",
		Beorning="Beorninger", Brawler="Schläger", Mariner="Seefahrer" };
	local races = { Hobbit="Hobbit", Man="Mensch", Elf="Elb", Dwarf="Zwerg", HighElf="Hochelb",
		StoutAxe="Robustaxt-Zwerg", Beorning="Beorninger", RiverHobbit="Flusshobbit" };
	for key, label in pairs(classes) do
		if classEnum ~= nil and classEnum[key] ~= nil and classEnum[key] == classValue then context.charclass = label; end
	end
	for key, label in pairs(races) do
		if raceEnum ~= nil and raceEnum[key] ~= nil and raceEnum[key] == raceValue then context.race = label; end
	end
	return context;
end

--- LOTRO marks up some game text: "<rgb=#FF0000>…</rgb>", "<b>", "<u>". A label
--- cannot render that, so the tags are removed and the words stay. Only these tags
--- are touched: the data also contains single stray "<" inside real words
--- ("<Armund sighs"), and removing those would lose text.
local MARKUP = {
	"<%s*/?%s*rgb[^>]*>",   -- colour tag, with or without value, opening or closing
	"<%s*/?%s*[bui]%s*>",   -- bold, underline, italics
	"</%s*[a-zA-Z]+%s*>",   -- a stray closing tag; the text carries "</sit>"
};

function M.CleanMarkup(text)
	text = tostring(text or "");
	for _, pattern in ipairs(MARKUP) do text = string.gsub(text, pattern, ""); end
	return text;
end

--- Replace game text placeholders. Current counters are never invented.
function M.Resolve(text, context, strings, total)
	text = M.CleanMarkup(text);
	text = string.gsub(text, "\\n", "\n");
	text = string.gsub(text, "\\q", "\"");
	local needsCounter = false;
	text = string.gsub(text, "%(%s*%${NUMBER}%s*/%s*%${TOTAL}%s*%)", function()
		needsCounter = true;
		if total ~= nil then return "(" .. strings.needed .. ": " .. tostring(total) .. ")"; end
		return "(" .. strings.counter .. ")";
	end);
	local function replace(token)
		local key, choices = string.match(token, "^([%w_]+):(.*)$");
		if choices ~= nil then
			local alternatives, seen = {}, {};
			for choice in string.gmatch(choices, "[^|]+") do
				local clean = (string.gsub(choice, "%[[^%]]*%]", ""));
				clean = (string.gsub(string.gsub(clean, "^%s+", ""), "%s+$", ""));
				if clean ~= "" and not seen[clean] then alternatives[#alternatives + 1] = clean; seen[clean] = true; end
			end
			return table.concat(alternatives, " / ");
		end
		if token == "PLAYER" or token == "PLAYERNAME" then return context.name or strings.you; end
		if token == "CLASS" then return context.charclass or strings.charclass; end
		if token == "RACE" then return context.race or strings.race; end
		if token == "TOTAL" then
			if total ~= nil then return tostring(total); end
			needsCounter = true;
			return strings.counter;
		end
		if token == "NUMBER" then needsCounter = true; return strings.counter; end
		return strings.value;
	end
	for _ = 1, 4 do
		-- The replacement result must be kept: discarding it left every
		-- placeholder to the fallback below, which turns them all into "[value]".
		local count;
		text, count = string.gsub(text, "%${([^{}]+)}", replace);
		if count == 0 then break; end
	end
	if string.find(text, "${", 1, true) ~= nil then
		text = string.gsub(text, "%${[^}\n]*}?", strings.value);
	end
	return text, needsCounter;
end

--- Right-hand pane text for one record: description, then numbered steps.
function M.Detail(record, strings, context)
	local parts = {};
	if record.l ~= nil and record.l ~= "" then
		table.insert(parts, strings.level .. ": " .. (record.l == "Scaling" and strings.scaled or tostring(record.l)));
	end
	local description = M.Resolve(record.d, context, strings);
	if (string.gsub(description, "%s", "")) ~= "" then
		table.insert(parts, strings.description .. "\n\n" .. description);
	end
	local blocks, current, currentStep = {}, {}, nil;
	local function flush()
		if #current > 0 then
			table.insert(blocks, strings.step .. " " .. tostring(currentStep) .. "\n\n" .. table.concat(current, "\n"));
		end
		current = {};
	end
	for _, step in ipairs(record.s or {}) do
		local number = step.i;
		if #current > 0 then flush(); end
		currentStep = number;
		for _, line in ipairs(step.n or {}) do
			current[#current + 1] = M.Resolve(line, context, strings);
		end
		for _, goal in ipairs(step.g or {}) do
			current[#current + 1] = "\n- " .. M.Resolve(goal.t, context, strings, goal.c);
		end
	end
	flush();
	for _, block in ipairs(blocks) do table.insert(parts, block); end
	return table.concat(parts, "\n\n\n");
end
