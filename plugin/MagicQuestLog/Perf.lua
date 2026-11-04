-- Timing for /mql zeit. Startup samples are kept before the command enables chat output.
-- The game's own clock stands still within one frame (and during the whole login),
-- so the real wall clock is used when the client offers one: os.clock, else
-- Turbine.Engine.GetLocalTime, else GetGameTime (frame granularity only).
MagicQuestLog = MagicQuestLog or {};
local P = { enabled = false, samples = {}, limit = 200 };
MagicQuestLog.Perf = P;

local function pickClock()
	if type(os) == "table" and type(os.clock) == "function" then
		return "os.clock", function() return os.clock(); end;
	end
	local engine = Turbine ~= nil and Turbine.Engine or nil;
	if engine ~= nil and engine.GetLocalTime ~= nil then
		local ok, value = pcall(function() return engine.GetLocalTime(); end);
		if ok and type(value) == "number" then
			return "GetLocalTime", function() return engine.GetLocalTime(); end;
		end
	end
	return "GetGameTime", function() return Turbine.Engine.GetGameTime(); end;
end

local clockName, clockNow = pickClock();
P.clock = clockName;

function P.Now()
	return clockNow();
end

function P.Print(sample)
	Turbine.Shell.WriteLine("Magic Quest Log Zeit: " .. sample.name .. ": "
		.. string.format("%.1f ms", sample.ms) .. (sample.detail or ""));
end

local function add(sample)
	P.samples[#P.samples + 1] = sample;
	if #P.samples > P.limit then table.remove(P.samples, 1); end
	if P.enabled then P.Print(sample); end
end

function P.Record(name, started, detail)
	add({ name = name, ms = (P.Now() - started) * 1000, detail = detail });
end

--- Time until the next frame after this point, reported as its own sample. Uses the
--- game clock, which is what the player feels.
function P.Frame(name)
	if Turbine.UI == nil or Turbine.UI.Control == nil or Turbine.Engine == nil then return; end
	if P.watcher == nil then
		P.watcher = Turbine.UI.Control();
		P.watcher.Update = function(control)
			control:SetWantsUpdates(false);
			local pending = P.pending;
			P.pending = nil;
			if pending ~= nil then
				add({ name = pending.name .. " bis zum nächsten Bild",
					ms = (Turbine.Engine.GetGameTime() - pending.started) * 1000 });
			end
		end;
	end
	if P.pending ~= nil then return; end
	P.pending = { name = name, started = Turbine.Engine.GetGameTime() };
	P.watcher:SetWantsUpdates(true);
end

function P.Toggle()
	P.enabled = not P.enabled;
	if P.enabled then
		Turbine.Shell.WriteLine("Magic Quest Log: Zeitmessung an (Uhr: " .. P.clock .. "; bisherige Messungen folgen).");
		for _, sample in ipairs(P.samples) do P.Print(sample); end
	else
		Turbine.Shell.WriteLine("Magic Quest Log: Zeitmessung aus.");
	end
end
