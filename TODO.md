# Teendők

## Elkészült

- [x] A kézirat címének átírása: *rapidsim: A Python toolkit for RAPID simulations and visualization*.
- [x] A többértékű listás paraméterek automatikus gridfuttatása a Python API-ban és a CLI-ben; az egyelemű listák skalárként kezelése.

## Szoftver, csomagolás és kiadás

- [x] A grid runner csomagba foglalásának ellenőrzése: a `run_grid()` a telepített `rapidsim` API része, és a buildelt wheelből importálható.
- [ ] Az ellenőrzött grid runnerrel új kiadás készítése és PyPI-ra publikálása, hogy a nyilvános `pip install rapidsim` is ezt a verziót telepítse.
- [ ] A szimulációs kimenetek plotolásának hozzáadása; a támogatott formátumok, API és dokumentáció meghatározásával.
- [ ] A telepített csomagból ellenőrizni és dokumentálni a `run()`, `run_grid()` és utófeldolgozási API működését, futtatható példákkal.
- [ ] A `rapidsim.__version__` attribútum biztosítása és tesztelése.
- [ ] Automatizált tesztek futtatása CI-ben, és annak ellenőrzése, hogy a PyPI-kiadás csak sikeres tesztelés után történik; a tesztlefedettség ismertetése a cikkben.
- [ ] Friss, teljes RAPID-forrást tartalmazó sdist készítésének és PyPI-ra feltöltésének ellenőrzése; tesztelni a forrásból fordítást és az egyedi fordítási kapcsolókat.
- [ ] Ellenőrizni, hogy fordított RAPID-bináris ne legyen verziókezelve; a kiadási folyamat állítsa elő és csomagolja.
- [ ] A PyPI projektmetaadatok `[project.urls]` mezőinek beállítása a hibajegykezelő, dokumentáció és forráskód helyes URL-jeivel.
- [ ] A kiadási folyamat és verziókezelés felülvizsgálata: Dependabot/submodule-frissítési PR, összevonás utáni kiadás, a `COMMIT RELEASE` lépés és a `setuptools-scm` lehetőségének mérlegelése.
- [ ] A Python-verziók és platformok támogatásának ellenőrzése, majd egységesítése a kódban, a wheelökben, a PyPI-metaadatokban és a kéziratban.
- [ ] A `CITATION.cff` és a README idézési útmutatójának ellenőrzése; a BibTeX-bejegyzések nem szabványos mezőinek eltávolítása.

## A kézirat tartalma és következetessége

- [ ] A `rapidsim` tényleges hatókörének és hozzáadott értékének világos bemutatása a bináris terjesztésen túl; a wrapper méretének és szerepének pontos, túlzásmentes leírása.
- [ ] A Python-választás indoklása az apt/Homebrew és más nyelvek lehetőségeihez képest; kitérni a MATLAB Python-interfészére és a felhőben futó Jupyter/Colab környezetekre.
- [ ] A `subprocess`-alapú megoldás indoklása, előnyeinek és korlátainak ismertetése, valamint a pybind11/nanobind alternatívák rövid tárgyalása.
- [ ] A Python API, a grid-futtatás és az utófeldolgozás konkrét bemutatása; elmagyarázni, mely munkafolyamatokat teszik egyszerűbbé a YAML-os futtatáshoz képest.
- [ ] Konfigurációs táblázat készítése a YAML-kulcsokkal, jelentéssel, elfogadott értékekkel/mértékegységekkel és a kapcsolódó RAPID-paraméterekkel.
- [ ] Rövid asztrofizikai bevezető írása a gázról, porról, protoplanetáris korongokról, fotoevaporációról és holtzónákról.
- [ ] A HDF5-, AEC- és SZIP-függőségek, valamint a csomagolt `libaec`, `libgomp`, `libhdf5`, `libhdf5_hl` és `libsz-0` könyvtárak betöltési viselkedésének ismertetése.
- [ ] A kiadási automatizmus leírásának összehangolása: különválasztani az automatikus frissítési, tesztelési és publikálási lépéseket a karbantartói kompatibilitási munkától.
- [ ] A dokumentáció hatókörének pontosítása: jelezni, hogy a RAPID-ot és a `rapidsim`-et is lefedi.
- [ ] A „heterogeneous systems” kifejezés megmagyarázása vagy törlése, illetve a macOS/Linux wheel- és Intel-platformállítások aktualizálása a tényleges támogatás szerint.
- [ ] A MESA-példák mellett változatosabb szoftverpéldák mérlegelése, például DustPy, rubble és astro-frap.
- [ ] A SoftwareX-hez készült C1–C9 metadata táblázat eltávolítása vagy A&C-hez illő átalakítása; a szükséges kód- és verzióadatok megfelelő helyen való megadása.
- [ ] A 2.3. szakasz és az 1. ábra frissítése a végleges kiadási folyamat szerint.

## Ábrák, hivatkozások és szerkesztési javítások

- [ ] Az architektúra/folyamatábra raszteres változatának lecserélése publikációra alkalmas vektoros ábrára.
- [ ] A 3. és A.4. ábra bemeneti konfigurációjának és megjelenített kimenetének egyeztetése, majd az ábrák újragenerálása.
- [ ] A C3 DOI javítása a ténylegesen hivatkozott kódverzióhoz.
- [ ] A hivatkozás [2] weboldalának lecserélése a `10.3847/0067-0049/223/1/11` DOI-ra, és a `FARGO3D` írásmód egységesítése.
- [ ] A [11] hivatkozásban a `PyYAML` írásmód és az archivált URL javítása; a [13] hivatkozásban a `DisksSubmitted` elírás javítása.
- [ ] A konkrét szövegjavítások elvégzése: az absztrakt első mondatának bontása; a „to run to” és az „Although” javítása; az ismétlődő szöveg átírása; a 64-es szám alsó indexének megszüntetése; a külön publikáció hiányáról szóló mondat törlése; „responsibility of the first author” cseréje „responsibility of the author”-ra.
