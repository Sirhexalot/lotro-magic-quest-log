-- Minimal class helper, Lua 5.1 compatible. Defined only when the client does not
-- already provide one, so the plugin never shadows a host implementation.
if _G.class == nil then
	_G.class = function(base)
		local c = {};
		c.base = base;
		local mt = { __index = base };
		mt.__call = function(classTable, ...)
			local instance = setmetatable({}, { __index = c });
			if instance.Constructor ~= nil then
				instance:Constructor(...);
			end
			return instance;
		end;
		setmetatable(c, mt);
		return c;
	end;
end
