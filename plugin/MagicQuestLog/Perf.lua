-- Timing for /mql zeit. Startup samples are kept before the command enables chat output.
-- GetGameTime stands still within one frame, so the CPU clock is used when the client
-- offers it. Each rebuild also reports the time until the next frame is drawn: that
-- is the stall a player actually notices.
MagicQuestLog = MagicQuestLog or {};
local P = { enabled = false, samples = {}, limit = 200 };
MagicQuestLog.Perf = P;

local hasClock = type(os) == "table" and type(os.clock) == "function";
P.clock = hasClock and "os.clock" or "GetGameTime";

function P.Now()
	if hasClock then return os.clock(); end
	return Turbine.Engine.GetGameTime();
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

--- Game time until the next frame after this point, reported as its own sample.
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
