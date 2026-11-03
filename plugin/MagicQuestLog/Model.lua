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
	local shown = M.Resolve(M.Caption(text, strings), context, strings);
	-- Grammar marks the game leaves on some category names ("Stark-Axt[m]").
	return (string.gsub(shown, "%[%l%l?%l?%]", ""));
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

--- Level as shown: "5", or "~" / "~100" when the level follows the character.
function M.LevelText(record)
	local level = record.l;
	if level == nil or level == "" then return nil; end
	if record.ls == 1 then
		local number = tonumber(level);
		if number ~= nil and number > 1 then return "~" .. tostring(number); end
		return "~";
	end
	return tostring(level);
end

--- Can the character take this quest now, as far as the data says? Open, not ruled
--- out, level reached, every required quest finished (v), one of the alternatives
--- finished (vo), and nothing we cannot check (vb). Without progress: unknown, false.
function M.Available(record, completed, level)
	if completed == nil or completed[record.id] == true then return false; end
	if record.sessionPlay or record.excluded or record.vb == 1 then return false; end
	if level ~= nil and tonumber(record.vl) ~= nil and tonumber(record.vl) > level then return false; end
	for _, id in ipairs(record.v or {}) do
		if completed[id] ~= true then return false; end
	end
	if record.vo ~= nil and #record.vo > 0 then
		local any = false;
		for _, id in ipairs(record.vo) do if completed[id] == true then any = true; end end
		if not any then return false; end
	end
	return true;
end

--- List section of an entry below its area: the names of path parts three and
--- deeper, a part that only repeats the area ("Imlad Morgul: Cirith Ungol") cut
--- to its own name. Returns the name ("" for the area itself) and its kind:
--- "area" for a sub-area, "group" for a quest group.
function M.Section(parts, context, strings)
	local names, kind = {}, "group";
	local above = {};
	for index, part in ipairs(parts or {}) do
		local name = M.Display(part.n, context, strings);
		if index <= 2 then
			above[#above + 1] = name;
		else
			if index == 3 and string.sub(tostring(part.k), 1, 5) == "area:" then kind = "area"; end
			for _, upper in ipairs(above) do
				local prefix = upper .. ":";
				if string.lower(string.sub(name, 1, #prefix)) == string.lower(prefix) then
					name = (string.gsub(string.sub(name, #prefix + 1), "^%s+", ""));
				end
			end
			if name ~= "" and (#names == 0 or string.lower(names[#names]) ~= string.lower(name)) then
				names[#names + 1] = name;
			end
			above[#above + 1] = name;
		end
	end
	return table.concat(names, " > "), kind;
end

--- Middle half of the levels below a node ("Stufe 9-25"), scaling entries left out.
--- Only with at least five levels; a node made mostly of scaling content says "~".
local function levelRange(levels, scaling)
	if scaling >= 5 and scaling >= #levels then return "~"; end
	if #levels < 5 then return nil; end
	table.sort(levels);
	local low = levels[math.floor((#levels - 1) * 0.25) + 1];
	local high = levels[math.ceil((#levels - 1) * 0.75) + 1];
	if low == high then return tostring(low); end
	return tostring(low) .. "-" .. tostring(high);
end

--- Build the visible tree. Search matches the name and the names of the areas it
--- lies in, so "Breeland" finds the area with all its entries.
--- "completed" is an optional set of finished ids; when given, every node also
--- counts how many of its entries are finished, so the tree can show "n/total".
--- Without that set no count is invented: done stays nil.
--- options.filter: "all", "open", "done" or "available"; options.level: the
--- character's level for "available".
function M.Build(records, query, strings, completed, context, options)
	options = options or {};
	local filter = options.filter or "all";
	local root = { key = "root", name = "root", children = {}, order = {}, items = {}, total = 0 };
	if completed ~= nil then root.done = 0; end
	local key = M.ContextKey(context);
	local function display(record)
		if record.displayKey ~= key then
			record.displayName = M.Display(record.name, context, strings);
			record.searchText = M.Normalize(record.displayName);
			local captions = {};
			for _, part in ipairs(record.p or {}) do captions[#captions + 1] = M.Display(part.n, context, strings); end
			record.pathText = M.Normalize(table.concat(captions, "\1"));
			-- List section below the area, cached like the name.
			record.section, record.sectionKind = M.Section(record.p, context, strings);
			record.sectionKey = M.SortKey(record.section);
			record.sortKey = M.SortKey(record.displayName);
			record.displayKey = key;
		end
		return record.displayName;
	end
	-- What a character can still do, not what exists. A session play is never
	-- written to the journal (the game plays someone else), and of two quests that
	-- rule each other out only one can be taken. Neither belongs in a counter.
	-- A finished entry always counts: the game data has a few pairs that a
	-- character has evidently done both of.
	local function attainable(record, finished)
		record.sessionPlay = record.x == 1;
		record.excluded = false;
		record.excludedBy = false;
		if finished then return true; end
		if record.sessionPlay then return false; end
		if completed ~= nil then
			for _, other in ipairs(record.ex or {}) do
				if completed[other] == true then
					record.excluded, record.excludedBy = true, other;
					return false;
				end
			end
		end
		return true;
	end
	local byId = {};
	for _, record in ipairs(records or {}) do byId[record.id] = record; end
	local needle = M.Normalize(query or "");
	for _, record in ipairs(records or {}) do
		local name = display(record);
		-- The state is worked out for every record, not only for the ones the
		-- search keeps: a stale flag would otherwise be shown later.
		local finished = completed ~= nil and completed[record.id] == true;
		local counts = attainable(record, finished);
		local shown = needle == "" or string.find(record.searchText, needle, 1, true) ~= nil
			or string.find(record.pathText, needle, 1, true) ~= nil;
		if shown and filter ~= "all" and completed ~= nil then
			if filter == "done" then shown = finished;
			elseif filter == "open" then shown = counts and not finished;
			elseif filter == "available" then shown = M.Available(record, completed, options.level); end
		end
		if shown then
			if counts then
				root.total = root.total + 1;
				if finished then root.done = root.done + 1; end
			end
			-- Two tree levels only (region or section, then area or book); what lies
			-- deeper becomes the entry's list section within its area.
			local node = root;
			local parts, depth = record.p or {}, 0;
			for _, part in ipairs(parts) do
				depth = depth + 1;
				if depth > 2 then break; end
				local child = node.children[part.k];
				if child == nil then
					local caption = M.Display(part.n, context, strings);
					child = { key = part.k, name = caption, sortKey = M.SortKey(caption),
						children = {}, order = {}, items = {}, total = 0, levels = {}, scaling = 0 };
					if completed ~= nil then child.done = 0; end
					node.children[part.k] = child;
					table.insert(node.order, child);
				end
				if counts then
					child.total = child.total + 1;
					if finished then child.done = child.done + 1; end
				end
				if record.ls == 1 then child.scaling = child.scaling + 1;
				elseif tonumber(record.l) ~= nil and tonumber(record.l) > 0 then
					child.levels[#child.levels + 1] = tonumber(record.l);
				end
				node = child;
			end
			table.insert(node.items, record);
		end
	end
	-- Name the alternative that blocks an entry. It may itself be filtered out by
	-- the search, so the record is looked up in the whole catalog.
	for _, record in ipairs(records or {}) do
		if record.excluded then
			local other = byId[record.excludedBy];
			record.excludedByName = other ~= nil and display(other) or record.excludedBy;
		end
	end
	-- Names that occur more than once in one list get their quest giver beside them.
	-- Items are ordered by section: the area itself first, then sub-areas, then
	-- quest groups, each alphabetically, and by name inside a section.
	local function sort(node)
		table.sort(node.order, function(a, b) return a.sortKey < b.sortKey; end);
		local function rank(record)
			if record.section == "" then return 0; end
			return record.sectionKind == "area" and 1 or 2;
		end
		table.sort(node.items, function(a, b)
			local ra, rb = rank(a), rank(b);
			if ra ~= rb then return ra < rb; end
			if a.sectionKey ~= b.sectionKey then return a.sectionKey < b.sectionKey; end
			return a.sortKey < b.sortKey;
		end);
		local seen = {};
		for _, record in ipairs(node.items) do seen[record.displayName] = (seen[record.displayName] or 0) + 1; end
		for _, record in ipairs(node.items) do record.twin = seen[record.displayName] > 1; end
		if node.levels ~= nil then
			node.range = levelRange(node.levels, node.scaling);
			node.levels = nil;
		end
		for _, child in ipairs(node.order) do sort(child); end
	end
	sort(root);
	root.byId = byId;
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

--- Right-hand pane text for one record. opts: completed (set or nil), level,
--- byId (all records), running (counters from the import for this id), showSteps
--- (objectives and steps; off by default so the solution is not in view), deed.
function M.Detail(record, strings, context, opts)
	opts = opts or {};
	local completed = opts.completed;
	local parts = {};
	local head = {};
	local level = M.LevelText(record);
	if level ~= nil then
		head[#head + 1] = strings.level .. " " .. level .. (record.ls == 1 and (" (" .. strings.scaling .. ")") or "");
	end
	if record.g ~= nil and record.g ~= "" then head[#head + 1] = string.format(strings.from, record.g); end
	if #head > 0 then table.insert(parts, table.concat(head, "  ·  ")); end
	-- Facts from the game data in one line.
	local facts = {};
	if tonumber(record.lp) then facts[#facts + 1] = string.format(strings.lp, tonumber(record.lp)); end
	if record.dy == 1 then facts[#facts + 1] = strings.daily; end
	if record.rp == -1 then facts[#facts + 1] = strings.repeatable;
	elseif tonumber(record.rp) and tonumber(record.rp) > 1 then facts[#facts + 1] = string.format(strings.upto, tonumber(record.rp)); end
	if record.gr == 2 then facts[#facts + 1] = strings.fellowship;
	elseif record.gr == 1 then facts[#facts + 1] = strings.smallfellowship; end
	if record.ix == 1 then facts[#facts + 1] = strings.instance; end
	if tonumber(record.tl) then
		local seconds = tonumber(record.tl);
		facts[#facts + 1] = string.format(strings.timelimit, seconds >= 120 and (tostring(math.floor(seconds / 60 + 0.5)) .. " min") or (tostring(seconds) .. " s"));
	end
	if #facts > 0 then table.insert(parts, table.concat(facts, "  ·  ")); end
	-- Why an entry is not counted. The row is dimmed in the tree; this says why.
	if record.sessionPlay then
		table.insert(parts, strings.sessionnote);
	end
	if record.excluded then
		-- Resolve returns two values; the second would become table.insert's position.
		local note = M.Resolve(string.format(strings.alternativenote,
			tostring(record.excludedByName or record.excludedBy or "")), context, strings);
		table.insert(parts, note);
	end
	-- Requirements, each with its state for the shown character.
	local function state(id)
		if completed == nil then return ""; end
		return "  (" .. (completed[id] == true and strings.reqdone or strings.reqopen) .. ")";
	end
	local function nameOf(id)
		local other = (opts.byId or {})[id];
		if other == nil then return id; end
		return other.displayName or M.Display(other.name, context, strings);
	end
	local requirements = {};
	if tonumber(record.vl) ~= nil then
		local line = "- " .. string.format(strings.reqlevel, tostring(record.vl));
		if opts.level ~= nil then
			line = line .. "  (" .. (opts.level >= tonumber(record.vl) and strings.reqdone or strings.reqopen) .. ")";
		end
		requirements[#requirements + 1] = line;
	end
	-- Requirements outside the catalogue say nothing useful and are left out.
	local known = opts.byId or {};
	for _, id in ipairs(record.v or {}) do
		if known[id] ~= nil then requirements[#requirements + 1] = "- " .. nameOf(id) .. state(id); end
	end
	local alternatives = {};
	for _, id in ipairs(record.vo or {}) do
		if known[id] ~= nil then alternatives[#alternatives + 1] = "    " .. nameOf(id) .. state(id); end
	end
	if #alternatives > 0 then
		requirements[#requirements + 1] = "- " .. strings.reqoneof;
		for _, line in ipairs(alternatives) do requirements[#requirements + 1] = line; end
	end
	if record.vb == 1 then requirements[#requirements + 1] = "- " .. strings.reqother; end
	if #requirements > 0 then
		table.insert(parts, strings.requirements .. "\n" .. table.concat(requirements, "\n"));
	end
	-- Quest chain: what leads here, what comes next.
	local chain = {};
	for _, id in ipairs(record.pq or {}) do chain[#chain + 1] = "- " .. strings.before .. ": " .. nameOf(id) .. state(id); end
	if record.nq ~= nil then chain[#chain + 1] = "- " .. strings.after .. ": " .. nameOf(record.nq) .. state(record.nq); end
	if #chain > 0 then
		table.insert(parts, strings.chain .. "\n" .. table.concat(chain, "\n"));
	end
	local description = M.Resolve(record.d, context, strings);
	if (string.gsub(description, "%s", "")) ~= "" then
		table.insert(parts, strings.description .. "\n\n" .. description);
	end
	if not opts.showSteps and not opts.deed then
		if record.s ~= nil and #record.s > 0 then table.insert(parts, strings.stepshidden); end
		return table.concat(parts, "\n\n\n");
	end
	local running = opts.running;
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
			local line = "\n- " .. M.Resolve(goal.t, context, strings, goal.c);
			-- Counter from the Companion import, matched by objective and condition
			-- number; never by text, never invented.
			local row = running ~= nil and goal.k ~= nil and running[tostring(step.i) .. ":" .. tostring(goal.k)] or nil;
			if row ~= nil then
				if row.done then
					line = line .. "  (" .. strings.reqdone .. ")";
				elseif row.count ~= nil and tonumber(goal.c) ~= nil and tonumber(goal.c) > 1 then
					line = line .. "  [" .. tostring(math.min(row.count, tonumber(goal.c))) .. "/" .. tostring(goal.c)
						.. ", " .. strings.imported .. "]";
				end
			end
			current[#current + 1] = line;
		end
	end
	flush();
	for _, block in ipairs(blocks) do table.insert(parts, block); end
	return table.concat(parts, "\n\n\n");
end

--- Right-hand pane for an area: its level range and counts.
function M.NodeSummary(node, strings, completed, level, running)
	local lines = {};
	if node.range ~= nil then lines[#lines + 1] = strings.level .. " " .. node.range; end
	lines[#lines + 1] = "";
	lines[#lines + 1] = strings.total .. ": " .. tostring(node.total);
	if completed ~= nil then
		local open, inprogress, available = 0, 0, 0;
		local function walk(current)
			for _, record in ipairs(current.items) do
				if completed[record.id] ~= true and not record.sessionPlay and not record.excluded then
					open = open + 1;
					if running ~= nil and running[record.id] ~= nil then inprogress = inprogress + 1; end
					if M.Available(record, completed, level) then available = available + 1; end
				end
			end
			for _, child in ipairs(current.order) do walk(child); end
		end
		walk(node);
		lines[#lines + 1] = strings.finished .. ": " .. tostring(node.done or 0);
		lines[#lines + 1] = strings.filteropen .. ": " .. tostring(open);
		lines[#lines + 1] = strings.inprogress .. ": " .. tostring(inprogress);
		lines[#lines + 1] = strings.available .. ": " .. tostring(available);
	end
	lines[#lines + 1] = "";
	lines[#lines + 1] = strings.choosehint;
	return table.concat(lines, "\n");
end
