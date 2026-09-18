"""
Fixtures HTML pour les tests unitaires.

Reproduit la structure exacte observée sur le site LONAB
pour permettre des tests sans requêtes réseau.
"""

# Page programmes — structure réelle observée le 2026-09-08
PROGRAMMES_PAGE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head><title>Programmes | LONAB</title></head>
<body class="path-programme-pmub">
<div role="main" class="main-container container">
  <div class="region region-content">
    <div class="views-element-container form-group">
      <div class="view view-programmes view-id-programmes view-display-id-page_1">
        <div class="view-content">
          <table class="table cols-0">
            <tbody>
              <tr>
                <td class="views-field views-field-title">journal hippique PMU&#039;B du 09 septembre 2026</td>
                <td class="views-field views-field-body"></td>
                <td class="views-field views-field-field-ajouter-un-fichier">
                  <a href="/sites/default/files/2026-09/JH_PMU%27B_DU_09-09-2026_0.pdf">Télécharger</a>
                </td>
              </tr>
              <tr>
                <td class="views-field views-field-title">journal hippique PMU&#039;B du 08 septembre 2026</td>
                <td class="views-field views-field-body"></td>
                <td class="views-field views-field-field-ajouter-un-fichier">
                  <a href="/sites/default/files/2026-09/JH_PMUB_DU_08-09-2026.pdf">Télécharger</a>
                </td>
              </tr>
              <tr>
                <td class="views-field views-field-title">journal hippique PMU&#039;B du 31 AOUT 2026</td>
                <td class="views-field views-field-body"></td>
                <td class="views-field views-field-field-ajouter-un-fichier">
                  <a href="/sites/default/files/2026-08/JH_PMUB_DU_31-08-2026.pdf">Télécharger</a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <nav role="navigation">
          <ul class="pager js-pager__items">
            <li class="next">
              <a href="/fr/programme-pmub?page=1" title="Aller à la page suivante" rel="next">
                <span aria-hidden="true">››</span>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

# Page résultats — structure réelle avec la typo Drupal "docuent"
RESULTATS_PAGE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head><title>Résultats/Gains | LONAB</title></head>
<body class="path-resultats-gains-pmub">
<div role="main" class="main-container container">
  <div class="region region-content">
    <div class="views-element-container form-group">
      <div class="view view-resultats-gains view-id-resultats_gains view-display-id-page_1">
        <div class="view-content">
          <table class="table table-striped cols-0">
            <tbody>
              <tr>
                <td class="views-field views-field-title">Télécharger les résultats PMU&#039;B du 07 Septembre 2026</td>
                <td class="views-field views-field-body"></td>
                <td class="views-field views-field-field-ajouter-un-docuent">
                  <a href="/sites/default/files/2026-09/Res_07_09_2026_QUARTE.pdf">Télécharger</a>
                </td>
              </tr>
              <tr>
                <td class="views-field views-field-title">Télécharger les résultats PMU&#039;B du 06 Septembre 2026</td>
                <td class="views-field views-field-body"></td>
                <td class="views-field views-field-field-ajouter-un-docuent">
                  <a href="/sites/default/files/2026-09/Rept41_06_09_2026.pdf">Télécharger</a>
                </td>
              </tr>
              <tr>
                <td class="views-field views-field-title">Télécharger les résultats PMU&#039;B du 06 Septembre 2026</td>
                <td class="views-field views-field-body"></td>
                <td class="views-field views-field-field-ajouter-un-docuent">
                  <a href="/sites/default/files/2026-09/Res41_06_09_2026.pdf">Télécharger</a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <nav role="navigation">
          <ul class="pager js-pager__items">
            <li class="next">
              <a href="/fr/resultats-gains-pmub?page=1" title="Aller à la page suivante" rel="next">
                <span aria-hidden="true">››</span>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

# Page sans pagination (dernière page)
LAST_PAGE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head><title>Programmes | LONAB</title></head>
<body>
<div role="main" class="main-container container">
  <div class="region region-content">
    <div class="views-element-container form-group">
      <div class="view view-programmes view-id-programmes view-display-id-page_1">
        <div class="view-content">
          <table class="table cols-0">
            <tbody>
              <tr>
                <td class="views-field views-field-title">journal hippique PMU&#039;B du 15 janvier 2024</td>
                <td class="views-field views-field-body"></td>
                <td class="views-field views-field-field-ajouter-un-fichier">
                  <a href="/sites/default/files/2024-01/JH_PMUB_DU_15-01-2024.pdf">Télécharger</a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <nav role="navigation">
          <ul class="pager js-pager__items">
            <li class="previous">
              <a href="/fr/programme-pmub?page=41" title="Aller à la page précédente" rel="prev">
                <span aria-hidden="true">‹‹</span>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

# Page vide (pas de tableau)
EMPTY_PAGE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head><title>Programmes | LONAB</title></head>
<body>
<div role="main" class="main-container container">
  <div class="region region-content">
    <div class="views-element-container form-group">
      <div class="view view-programmes view-id-programmes view-display-id-page_1">
        <div class="view-content">
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

# Ligne avec un lien non-PDF
NON_PDF_LINK_HTML = """
<!DOCTYPE html>
<html lang="fr">
<body>
<table class="table cols-0">
  <tbody>
    <tr>
      <td class="views-field views-field-title">Document texte</td>
      <td class="views-field views-field-body"></td>
      <td class="views-field views-field-field-ajouter-un-fichier">
        <a href="/sites/default/files/2026-09/document.html">Télécharger</a>
      </td>
    </tr>
    <tr>
      <td class="views-field views-field-title">journal hippique PMU&#039;B du 01 mars 2026</td>
      <td class="views-field views-field-body"></td>
      <td class="views-field views-field-field-ajouter-un-fichier">
        <a href="/sites/default/files/2026-03/JH_PMUB_DU_01-03-2026.pdf">Télécharger</a>
      </td>
    </tr>
  </tbody>
</table>
</body>
</html>
"""
