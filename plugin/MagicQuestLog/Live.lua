-- Live completion detection from the quest chat channel.
-- Pure logic plus one chat hook: no storage, no UI. Covered by the headless tests.
--
-- The client prints a completion as a header line and the name on the next line:
--   "Abgeschlossen:" / "Completed:" / "Terminé :"  +  name
-- Depending on the client version both lines arrive either as two chat events or
-- as one message containing a line break, so both forms are handled.
--
-- Deeds use the same header, which is why one name index spans both catalogs.
-- A name is only a hint: 639 quest names and 237 deed names in the German catalog
-- belong to more than one entry (race/class variants, repeatable lines). Such a
-- name is never assigned to a guess; the caller is told it was ambiguous.
MagicQuestLog = MagicQuestLog or {};
local L = {};
MagicQuestLog.Live = L;

-- Matched by pattern, not by catalog language: a client can print English server
-- text on a German client, and the three forms cost nothing.
local HEADER = {
	"^Abgeschlossen%s*:%s*(.*)$",
	"^Completed%s*:%s*(.*)$",
	"^Terminé%s*:%s*(.*)$",
};

--- Trim, and fold the narrow no-break space the French client uses before ":".
local function clean(text)
	text = tostring(text or "");
	text = string.gsub(text, "\194\160", " ");   -- UTF-8 no-break space
	return (string.gsub(text, "^%s*(.-)%s*$", "%1"));
end

--- name -> { ids... } over both catalogs. Rebuilt whenever the catalogs change.
function L.Index(quests, deeds)
	local index = {};
	local function add(records)
		for _, record in ipairs(records or {}) do
			local name = record.name;
			if name ~= nil then
				local list = index[name];
				if list == nil then list = {}; index[name] = list; end
				list[#list + 1] = record.id;
			end
		end
	end
	add(quests);
	add(deeds);
	return index;
end

--- Parser state. Kept on the object so a header and its name may arrive apart.
function L.New(options)
	options = options or {};
	return {
		index = options.index or {},
		completed = options.completed or {},
		unresolved = options.unresolved or {},
		pending = false,
		onChange = options.onChange,
		onAmbiguous = options.onAmbiguous,
	};
end

--- Which ids a completed name stands for: exactly one, or none when ambiguous.
function L.Resolve(self, name)
	local ids = self.index[name];
	if ids == nil or #ids ~= 1 then return nil, ids and #ids or 0; end
	return ids[1], 1;
end

function L.Mark(self, id)
	if id == nil or self.completed[id] == true then return false; end
	self.completed[id] = true;
	if self.onChange ~= nil then self.onChange(id); end
	return true;
end

--- One completion by name. Returns the id when it was assigned.
function L.Completion(self, name)
	name = clean(name);
	if name == "" then return nil; end
	local id, candidates = L.Resolve(self, name);
	if id ~= nil then
		L.Mark(self, id);
		return id;
	end
	-- Never guess between entries that share a name; keep it findable instead.
	if candidates > 1 then
		-- Stored as text: the client writes numbers with a decimal comma, which
		-- would make the whole saved file unreadable on the next load.
		self.unresolved[name] = tostring(candidates);
		if self.onAmbiguous ~= nil then self.onAmbiguous(name, candidates); end
	end
	return nil;
end

--- Feed one raw chat message, whatever the client delivered as one event.
function L.Message(self, text)
	local body = string.gsub(tostring(text or ""), "\r\n", "\n");
	body = string.gsub(body, "\r", "\n");
	for line in string.gmatch(body, "([^\n]*)") do
		local trimmed = clean(line);
		if trimmed ~= "" then
			if self.pending then
				self.pending = false;
				L.Completion(self, trimmed);
			else
				local rest = nil;
				for _, pattern in ipairs(HEADER) do
					rest = string.match(trimmed, pattern);
					if rest ~= nil then break; end
				end
				if rest ~= nil then
					-- Name on the same line, or the next non-empty line carries it.
					if rest == "" then self.pending = true; else L.Completion(self, rest); end
				end
			end
		end
	end
end

--- Hook the chat. Idempotent: reloading the plugin replaces the handler instead of
--- stacking another one, which would mark every completion several times.
function L.Attach(self)
	if Turbine == nil or Turbine.Chat == nil then return false; end
	L.detached = self;
	Turbine.Chat.Received = function(_, args)
		if L.detached ~= self then return; end     -- a newer instance owns the hook
		if args == nil then return; end
		if args.ChatType ~= nil and Turbine.ChatType ~= nil
			and args.ChatType ~= Turbine.ChatType.Quest then
			return;
		end
		L.Message(self, args.Message);
	end;
	return true;
end

function L.Detach()
	L.detached = nil;
	if Turbine ~= nil and Turbine.Chat ~= nil then Turbine.Chat.Received = nil; end
end
