# Antworten zur Dublettenkorrektur 0.5.3

**Status: 0.5.3 gebaut, Upload und Freigabe stehen aus. Erst nach der Freigabe einen verfügbaren Download behaupten.**

## Evereus – LOTROInterface

Hi Evereus,

thank you for the detailed list. The duplicate class books were real: the catalog carried 65 exact duplicate groups as two separate entries, 67 older ids in total. 0.5.3 now shows each of them once. The older id stays in the catalog, so a progress file that still names it does not lose the completion; it is carried over to the current deed.

What 0.5.3 does not change: the class list still contains the books of every class, not just yours. The 30 under Trollshaws are 10 classes x 3 books; the 6 under Bree are Brawler and Mariner. A class filter and the separation of class, instance, race/social and landscape deeds are the next data step, not part of this release.

The rest of your list:

- **Tracking an Old Goat:** I found the duplicate, but the two entries differ in their prerequisite and reward, and I have not yet confirmed which one the live game uses. I left both visible for now rather than guessing. If you still have a character who has not done it, the deed log will show which version is current; that would settle it.
- **Explore the Dreadwood:** it is not in our current deed export at all, in any language. It may be a removed deed that no longer exists in the data. If you can give me the German name or the deed id, I can check it.
- **Lhaid Ogo:** it is in the catalog as an Epic deed with a location in Enedwaith, so it appears under Enedwaith with an Epic section. The next step separates Epic deeds from landscape areas.
- **Cardolan and Swanfleet:** 9 and 4 are the deeds that currently have a zone. Most deeds in the "Swanfleet & Cardolan" category have no zone and fall into Other Content; the next data step maps those pack categories to Eriador.
- **Bree 127:** there is no cap. 127 is the sum of landscape and non-landscape deeds in Bree-land (53 skirmish instances, 6 class deeds and others). The category separation will remove them from the landscape number.
- **Monster play:** already fixed in 0.5.2; the totals are 75 in Angmar, 28 in Eregion and 30 in Forochel.

0.5.3 is on its way to LOTROInterface and has to pass file-admin approval, so the download may still serve 0.5.2 for a while. I will post here once 0.5.3 is available.

Thanks again for counting and for the exact names and ids. That is what makes these fixes possible.

Sirhexalot

## Kurzfassung für Adrian

- 0.5.3 behebt die 65 exakten Klassendubletten; 67 alte IDs werden ausgeblendet, ihr Fortschritt zählt weiter.
- Klassenfilter und die Trennung von Klasse/Instanz/Volk/Landschaft sind **nicht** in 0.5.3; sie bleiben der nächste Datenschritt.
- Tracking und Enmity bleiben sichtbar; für Tracking braucht es den Blick ins Spiel.
- Dreadwood fehlt in unseren Daten; nach dem deutschen Namen oder der ID fragen.
- Lhaid Ogo, Cardolan/Swanfleet und Bree 127 werden erklärt, nicht als erledigt behauptet.
- 0.5.2 (Monsterplay) bleibt bestätigt: 75/28/30.
