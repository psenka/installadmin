# InstallAdmin

GUI aplikace pro správu winget balíčků napsaná v Pythonu s CustomTkinter.

## Funkce

- 📦 Výpis nainstalovaných aplikací (`winget list`)
- 🗑️ Odinstalování aplikací
- 🔄 Aktualizace aplikací (pokud je novější verze)
- 🔍 Vyhledávání nových balíčků s autocompletem
- 🌓 Přepínání light/dark tématu
- ⚡ Asynchronní operace (UI nezamrzá)

## Instalace

```bash
pip install -e .
```

## Spuštění

```bash
install-admin
```

nebo

```bash
python -m install_admin
```

## Požadavky

- Windows 10/11 s winget
- Python 3.10+
- Administrátorská práva (pro odinstalování/aktualizaci - řeší se automaticky přes UAC)

## Screenshot

*Aplikace se spustí v systémovém tématu (light/dark). Ikona sluníčka/měsíčku vpravo nahoře přepíná téma.*