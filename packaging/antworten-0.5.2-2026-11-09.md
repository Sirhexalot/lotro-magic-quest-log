# Antworten zur Tatenkorrektur 0.5.2

**Freigabe offen. Erst nach Prüfung des tatsächlich ausgelieferten Archivs einen freigegebenen Download behaupten.**

## Evereus – LOTROInterface

Hi Evereus,

You are right, and thank you for the exact numbers. They made the cause easy to find.

Your import is fine. The catalog contains 100 monster-play deeds per area in Angmar, Eregion and Forochel: "Angmar Champion-slayer -- Tier 1-5", "Eregion Defiler-slayer -- Tier 3" and so on. They are fought as a monster in PvMP and never appear in a normal character's journal. The game flags most of them; a few dozen carry no flag and only their title gives them away. The plugin counted them as attainable deeds, which inflated those three counters.

Fixed in 0.5.2: those deeds are flagged and left out of the counters. They stay visible in the tree, and the details now say why they do not count. The totals drop by 100 each: to 75 in Angmar, 28 in Eregion and 30 in Forochel. Those numbers still include instance deeds, so they are not a promise of pure landscape deeds.

The update is submitted to LOTROInterface and awaits file-admin approval, so the download may still serve the older version for a short while. I will post here once 0.5.2 is available.

Thanks for taking the time to count.

Sirhexalot
