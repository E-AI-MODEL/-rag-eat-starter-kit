# Security policy

## Kwetsbaarheid melden

Open geen publieke issue met secrets, tokens, exploitdetails of gevoelige data.

Meld een kwetsbaarheid via een privéroute van de repositorybeheerder. Als er nog geen privéroute is ingesteld, open dan een algemene issue zonder gevoelige details en vraag om contact.

## Scope

Deze repo bevat templates en documentatie. Toch kunnen securityproblemen ontstaan door:

- onveilige promptregels
- voorbeelden die secrets bevatten
- fout advies over rechtencontrole
- onveilige RAG-patronen
- ontbrekende waarschuwingen bij agentgebruik

## Basisregel

Opgehaalde context is data, geen instructie. Een RAG-systeem mag nooit instructies uit documenten laten winnen van systeemregels.
