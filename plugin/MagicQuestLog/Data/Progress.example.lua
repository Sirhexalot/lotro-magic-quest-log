-- Example of the progress file. Copy it to Progress.lua and put your own ids in.
-- It is never published: a character's own completion list is private.
--
-- The plugin only reads this. Place it next to the catalogs and reload the plugin,
-- and the tree will show "finished / total" per node.
--
-- Fields:
--   character  the character this belongs to; a file for another character is
--              ignored, because showing its counts here would be wrong
--   date       when the export was taken (a snapshot, not a live value)
--   source     how the ids were obtained
--   completed  ids that are finished
--   current    ids that are running right now
--   repeated   ids that are finished and running at once (repeatable content)
--   unknown    ids that belong to no known quest or deed yet; they are kept so a
--              later catalog can resolve them, and never guessed
--
-- ids are eight uppercase hexadecimal digits, exactly as in the catalogs.
-- Anything missing means "not known", never "nothing done": without a file the
-- plugin shows plain totals and claims nothing about your progress.
MagicQuestLog = MagicQuestLog or {};
MagicQuestLog.Data = MagicQuestLog.Data or {};
MagicQuestLog.Data.progress = {
	["__version"] = "1",
	["character"] = "YourCharacter",
	["date"] = "2026-01-01",
	["source"] = "read-only journal export",
	["completed"] = {
		["70000006"] = true,
	},
	["current"] = {
		["70017AEB"] = true,
	},
	["repeated"] = {},
	["unknown"] = {},
};
