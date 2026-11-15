# Antworten zur Importkorrektur 0.5.1

**Spieltest bestanden; 0.5.1 am 7. November eingereicht, Freigabe offen. Antworten werden anschließend versendet; Versandstand unten dokumentieren.** Ein hochgeladenes, noch nicht freigegebenes Archiv ist noch kein verfügbarer Download.

## peskycritter – LOTROInterface

Hi peskycritter,

Thanks for reporting this. No, a disappearing Character button is not how it should behave. Sorry for the confusing start.

I reproduced a loading bug in-game: LOTRO returns saved data directly while a plugin starts, but uses a callback for later reads. My code wasn't handling that callback, so reopening the window or switching characters could make an existing import look missing and lose the character list. That's my bug, not something you did wrong.

I also found that the exporter and plugin rejected character names with accents. The website fix is already live; those names need a fresh export. The plugin fix keeps the Character button visible but disabled when only one character is known, and adds a message with the expected path if an import really is missing.

I've now tested the corrected 0.5.1 in-game, including closing and reopening the window, and submitted it to LOTROInterface. It is awaiting approval, so the download may still serve 0.5.0 for now. Once 0.5.1 is available, please let me know whether it resolves the problem for your characters too.

One other thing worth checking: after extraction, the path should be `PluginData\[account]\[server]\AllCharacters\MagicQuestLog_Import_[name].plugindata`, without an extra `MagicQuestLog-PluginData` folder in between. Please don't post your account folder name or the full ZIP publicly.

Thanks for taking the time to report both symptoms.

Sirhexalot

## LabNo8051 – Reddit, Antwort unter dem Fehlerbericht

Thanks for reporting it here too, and no need to feel dumb about the ZIP. The instructions should make that clearer.

I reproduced a bug in-game that explains why reopening the plugin or switching characters could lose the imported data: LOTRO delivers runtime file reads through a callback, and my loader wasn't handling it. That's my mistake, not yours.

There was a second bug with accented character names: the exporter silently skipped them. The website fix for that is live. The plugin update handles the runtime callback, keeps the Character button from disappearing and explains genuinely missing imports. I've tested 0.5.1 in-game, including reopening the window, and submitted it to LOTROInterface. It is awaiting approval, so the download may still serve 0.5.0 for now.

If any of your character names contain accents, please make a fresh export from the website as well as installing the plugin update, because the old ZIP may not contain their files at all. I'd appreciate hearing whether the update fixes it for you.

Thanks for sticking with it and adding the extra detail.

## SturmoviK88 – Reddit, „Awesome!“

Thank you! Glad you like it. If you spot something that doesn't line up with the game, let me know.

## Real_Cauliflower_956 – Reddit, „Looks good, I will check it out.“

Thanks for giving it a try! I'd love to hear how it works for your character, especially if you run into anything confusing.

## iAkrobat – Reddit, „That is crazy.“

Thanks! It started with wanting to know which quests I'd missed. It got a little out of hand from there.

## Hyoss – LOTROInterface

Bereits beantwortet: Die bestehende Antwort erklärt den Browser-Konverter und bedankt sich für den Deed-Tracker-Hinweis. Nicht noch einmal dieselbe Antwort veröffentlichen. Nur bei einer neuen Rückfrage antworten.

## Nach erfolgreicher Einreichung anzupassender Statussatz

Bei Freigabe offen:

> I've tested 0.5.1 in-game and submitted it to LOTROInterface. It's awaiting approval, so the download may still serve 0.5.0 for now. The website fix is already live.

Erst nach Prüfung des tatsächlich ausgelieferten Archivs:

> Version 0.5.1 is available now. Please update the plugin and export your Companion data again from https://llb.sirhexalot.de/spielstand.html?lang=en, then extract the ZIP into PluginData.
