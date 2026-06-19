# RAG EAT Starter Kit

Een open starter kit voor het ontwerpen, testen en beheren van een RAG-assistent met een compact EAT-profiel.

RAG staat voor Retrieval-Augmented Generation. De assistent zoekt eerst relevante bronnen en antwoordt daarna op basis van die bronnen.

EAT wordt hier gebruikt als gedragsprofiel voor de assistent. Het beschrijft rol, stappen, regels, output en toon. EAT is geen kennisbank, geen metadata-model en geen vervanger voor YAML, JSON of Markdown.

## Voor wie is dit?

Deze kit is bedoeld voor mensen die een RAG-assistent willen bouwen voor:

- interne kennisbanken
- productdocumentatie
- beleid en procedures
- handleidingen
- onderwijsdocumentatie
- supportartikelen
- technische documentatie

## Wat zit erin?

| Pad | Doel |
|---|---|
| `docs/RAG_Notes_2026.md` | Praktische gids voor RAG-ontwerp, retrieval, evaluatie en beheer. |
| `docs/RAG_References.md` | Bronnen en aanbevolen leesmateriaal. |
| `docs/EAT_Construct_Explanation.md` | Uitleg van EAT en hoe een LLM EAT moet toelichten. |
| `prompts/rag_assistant.eat` | EAT-profiel voor het gedrag van de assistent. |
| `prompts/rag_system_prompt_template.md` | System-prompttemplate dat EAT koppelt aan RAG-context. |
| `config/rag_pipeline.yaml` | Voorbeeldconfiguratie voor ingestie, retrieval, reranking en output. |
| `eval/rag_eval_set.csv` | Startset voor evaluatievragen. |
| `security/rag_security_checklist.md` | Checklist voor RAG-security. |
| `examples/` | Voorbeelden van vragen, antwoorden en bronverwijzing. |
| `DATA_POLICY.md` | Wat je niet in deze repo moet zetten. |
| `CONTRIBUTING.md` | Regels voor bijdragen. |
| `SECURITY.md` | Hoe kwetsbaarheden gemeld kunnen worden. |

## Snelle start

1. Kopieer deze repo.
2. Pas `config/rag_pipeline.yaml` aan op je eigen omgeving.
3. Vul `eval/rag_eval_set.csv` met echte, maar veilige en geanonimiseerde testvragen.
4. Gebruik `prompts/rag_assistant.eat` als gedragsprofiel.
5. Combineer dit met `prompts/rag_system_prompt_template.md` in je RAG-app.
6. Test eerst retrieval, daarna pas antwoordkwaliteit.
7. Controleer security voordat je live gaat.

## Belangrijke keuze

Deze repo bevat geen echte kennisbank. Dat is bewust.

Zet documenten, klantdata, leerlingdata, personeelsdata, medische data, tokens, API-sleutels en logs niet in deze repo. Gebruik deze repo voor structuur, prompts, configvoorbeelden, evaluatievormen en documentatie.

## Aanbevolen basisopzet

Voor de meeste RAG-projecten is dit een goede eerste versie:

- hybride retrieval: embeddings plus keyword search
- metadata per chunk
- rechtencontrole voor retrieval
- reranking van kandidaatpassages
- antwoorden met bronverwijzing
- fallback bij onvoldoende bronnen
- vaste evaluatieset
- logging van gebruikte bronnen
- securitytest tegen prompt injection in documenten

## Licentie

Deze starter kit gebruikt de MIT License. Dat maakt hergebruik, aanpassen en verspreiden eenvoudig. Controleer zelf of deze licentie past bij je organisatie.

## Status

Versie: 0.1.0

Deze repo is een starter kit. Gebruik hem als basis, niet als vervanging voor eigen securityreview, juridische controle of domeinexpertise.
