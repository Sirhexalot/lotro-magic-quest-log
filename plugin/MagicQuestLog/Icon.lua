import "Turbine";
import "Turbine.UI";
import "MagicQuestLog.Class";

MagicQuestLog = MagicQuestLog or {};

-- Small always-available starter icon. Uses the mop-sparkles icon from Lucide
-- (see icon-sources/NOTICE), rendered to Resources/start.tga.
MagicQuestLog.Icon = class(Turbine.UI.Window);
local Icon = MagicQuestLog.Icon;

local SIZE = 36;
local SPARKLES = "MagicQuestLog/Resources/start.tga";

function Icon:Constructor(onClick)
	Turbine.UI.Window.Constructor(self);
	self.onClick = onClick;
	self:SetSize(SIZE, SIZE);
	self:SetZOrder(200);
	self:SetMouseVisible(true);
	self:SetBackColor(Turbine.UI.Color(0, 0, 0, 0));

	self.frame = Turbine.UI.Control();
	self.frame:SetParent(self);
	self.frame:SetPosition(0, 0);
	self.frame:SetSize(SIZE, SIZE);
	self.frame:SetBackColor(Turbine.UI.Color(0.10, 0.09, 0.06));
	self.frame:SetMouseVisible(true);
	self:SetFrameColour(false);

	local glyph = Turbine.UI.Control();
	glyph:SetParent(self.frame);
	glyph:SetPosition(6, 6);
	glyph:SetSize(24, 24);
	glyph:SetMouseVisible(false);
	glyph:SetBackground(SPARKLES);

	self.frame.MouseEnter = function() self:SetFrameColour(true); end;
	self.frame.MouseLeave = function() self:SetFrameColour(false); end;
	self.frame.MouseDown = function(sender, args)
		sender.dragStartX, sender.dragStartY = args.X, args.Y;
		sender.dragging, sender.dragged = true, false;
	end;
	self.frame.MouseMove = function(sender, args)
		if not sender.dragging then return; end
		local left, top = self:GetLeft() + (args.X - sender.dragStartX), self:GetTop() + (args.Y - sender.dragStartY);
		self:SetPosition(left, top);
		sender:SetPosition(0, 0);
		sender.dragged = true;
	end;
	self.frame.MouseUp = function(sender, args)
		if not sender.dragging then return; end
		sender.dragging = false;
		if sender.dragged then
			local display = Turbine.UI.Display;
			local left = math.max(0, math.min(self:GetLeft(), display:GetWidth() - SIZE));
			local top = math.max(0, math.min(self:GetTop(), display:GetHeight() - SIZE));
			self:SetPosition(left, top);
			if self.Moved ~= nil then self.Moved(left, top); end
		elseif self.onClick ~= nil then
			self.onClick();
		end
	end;
end

function Icon:SetFrameColour(highlighted)
	self.frame:SetBackColor(highlighted and Turbine.UI.Color(0.18, 0.15, 0.10)
		or Turbine.UI.Color(0.10, 0.09, 0.06));
end
