import streamlit as st
import pandas as pd
from io import BytesIO

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Préparation Certification HAS",
    page_icon="✓",
    layout="wide",
)

STATUTS = [
    "À vérifier",
    "Conforme",
    "Partiellement conforme",
    "Non conforme",
    "Non applicable",
]

PRIORITES = [
    "Faible",
    "Moyenne",
    "Élevée",
    "Critique",
]

# ============================================================
# DONNÉES DE DÉMONSTRATION
# ============================================================
# Remplacer ces données par le référentiel HAS officiel.
# Une ligne = une exigence / un contrôle.

REFERENTIEL_DEMO = [
    {
        "ID": "E-001",
        "Domaine": "Organisation",
        "Critère": "Exemple de critère",
        "Exigence": "Libellé exact de l'exigence E à intégrer",
        "Référence_HAS": "Volet 1 - E-001",
        "Référence_Charte": "",
        "Preuves_attendues": "Procédure ; organisation ; responsabilités",
        "Responsable": "",
        "Statut": "À vérifier",
        "Priorité": "Élevée",
        "Commentaires": "",
        "Référence_preuve": "",
        "Action": "",
    },
    {
        "ID": "E-002",
        "Domaine": "Formation",
        "Critère": "Exemple de critère",
        "Exigence": "Libellé exact de l'exigence E à intégrer",
        "Référence_HAS": "Volet 1 - E-002",
        "Référence_Charte": "",
        "Preuves_attendues": "Programme de formation ; évaluations ; traçabilité",
        "Responsable": "",
        "Statut": "À vérifier",
        "Priorité": "Élevée",
        "Commentaires": "",
        "Référence_preuve": "",
        "Action": "",
    },
]

# ============================================================
# INITIALISATION SESSION
# ============================================================

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(REFERENTIEL_DEMO)

df = st.session_state.df

# ============================================================
# FONCTIONS
# ============================================================

def export_excel(dataframe):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(
            writer,
            index=False,
            sheet_name="Checklist"
        )

        # Tableau de synthèse
        synthese = (
            dataframe["Statut"]
            .value_counts()
            .rename_axis("Statut")
            .reset_index(name="Nombre")
        )

        synthese.to_excel(
            writer,
            index=False,
            sheet_name="Synthèse"
        )

    return output.getvalue()


def calculer_kpi(dataframe):
    total = len(dataframe)

    if total == 0:
        return {
            "total": 0,
            "conforme": 0,
            "partiel": 0,
            "non_conforme": 0,
            "a_verifier": 0,
            "taux": 0,
        }

    conforme = (dataframe["Statut"] == "Conforme").sum()
    partiel = (dataframe["Statut"] == "Partiellement conforme").sum()
    non_conforme = (dataframe["Statut"] == "Non conforme").sum()
    a_verifier = (dataframe["Statut"] == "À vérifier").sum()

    return {
        "total": total,
        "conforme": conforme,
        "partiel": partiel,
        "non_conforme": non_conforme,
        "a_verifier": a_verifier,
        "taux": round(conforme / total * 100, 1),
    }


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Certification HAS")

st.sidebar.markdown(
    """
### Navigation

- Tableau de bord
- Checklist
- Preuves
- Actions
- Référentiel
- Exports
"""
)

page = st.sidebar.radio(
    "Accéder à",
    [
        "Tableau de bord",
        "Checklist",
        "Preuves",
        "Actions",
        "Référentiel",
        "Exports",
    ],
)

st.sidebar.divider()

st.sidebar.caption(
    "Outil de préparation interne — "
    "à adapter et qualifier selon les exigences de votre système qualité."
)

# ============================================================
# TABLEAU DE BORD
# ============================================================

if page == "Tableau de bord":

    st.title("Préparation à la certification HAS")
    st.subheader("Information promotionnelle — Volet 1")

    kpi = calculer_kpi(df)

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Exigences", kpi["total"])
    col2.metric("Conformes", kpi["conforme"])
    col3.metric("Partiellement conformes", kpi["partiel"])
    col4.metric("Non conformes", kpi["non_conforme"])
    col5.metric("Taux de conformité", f"{kpi['taux']} %")

    st.divider()

    # Barre de progression
    st.subheader("Progression globale")

    st.progress(kpi["taux"] / 100)

    st.write(
        f"{kpi['conforme']} exigence(s) conforme(s) "
        f"sur {kpi['total']}."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Répartition par statut")

        statut_counts = (
            df["Statut"]
            .value_counts()
            .rename_axis("Statut")
            .reset_index(name="Nombre")
        )

        st.bar_chart(
            statut_counts.set_index("Statut")
        )

    with col2:
        st.subheader("Répartition par domaine")

        domaine_counts = (
            df.groupby(["Domaine", "Statut"])
            .size()
            .unstack(fill_value=0)
        )

        st.bar_chart(domaine_counts)

    st.divider()

    st.subheader("Points nécessitant une attention")

    risques = df[
        df["Statut"].isin(
            [
                "Non conforme",
                "Partiellement conforme",
                "À vérifier",
            ]
        )
    ]

    if risques.empty:
        st.success("Aucun point en attente.")
    else:
        st.dataframe(
            risques[
                [
                    "ID",
                    "Domaine",
                    "Critère",
                    "Statut",
                    "Priorité",
                    "Responsable",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# CHECKLIST
# ============================================================

elif page == "Checklist":

    st.title("Checklist des exigences")

    # -------------------------
    # FILTRES
    # -------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        domaines = ["Tous"] + sorted(
            df["Domaine"].dropna().unique().tolist()
        )

        domaine = st.selectbox(
            "Domaine",
            domaines,
        )

    with col2:
        statuts = ["Tous"] + STATUTS

        statut = st.selectbox(
            "Statut",
            statuts,
        )

    with col3:
        priorites = ["Toutes"] + PRIORITES

        priorite = st.selectbox(
            "Priorité",
            priorites,
        )

    recherche = st.text_input(
        "Rechercher",
        placeholder="ID, exigence, critère, preuve..."
    )

    # -------------------------
    # FILTRAGE
    # -------------------------

    filtered = df.copy()

    if domaine != "Tous":
        filtered = filtered[
            filtered["Domaine"] == domaine
        ]

    if statut != "Tous":
        filtered = filtered[
            filtered["Statut"] == statut
        ]

    if priorite != "Toutes":
        filtered = filtered[
            filtered["Priorité"] == priorite
        ]

    if recherche:
        mask = (
            filtered.astype(str)
            .apply(
                lambda col: col.str.contains(
                    recherche,
                    case=False,
                    na=False
                )
            )
            .any(axis=1)
        )

        filtered = filtered[mask]

    st.caption(
        f"{len(filtered)} exigence(s) affichée(s)"
    )

    # -------------------------
    # AFFICHAGE DES EXIGENCES
    # -------------------------

    for index, row in filtered.iterrows():

        with st.expander(
            f"{row['ID']} — {row['Domaine']} — "
            f"{row['Statut']}"
        ):

            st.markdown(
                f"### {row['Exigence']}"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    "**Référence HAS :**",
                    row["Référence_HAS"]
                )

                st.write(
                    "**Référence Charte :**",
                    row["Référence_Charte"]
                )

                st.write(
                    "**Critère :**",
                    row["Critère"]
                )

            with col2:
                st.write(
                    "**Preuves attendues :**",
                    row["Preuves_attendues"]
                )

                st.write(
                    "**Priorité :**",
                    row["Priorité"]
                )

            st.divider()

            new_status = st.selectbox(
                "Statut",
                STATUTS,
                index=STATUTS.index(row["Statut"])
                if row["Statut"] in STATUTS
                else 0,
                key=f"status_{row['ID']}",
            )

            new_owner = st.text_input(
                "Responsable",
                value=row["Responsable"],
                key=f"owner_{row['ID']}",
            )

            new_evidence = st.text_input(
                "Référence de la preuve",
                value=row["Référence_preuve"],
                placeholder="Ex. SOP-QA-001 v05 / dossier formation...",
                key=f"evidence_{row['ID']}",
            )

            new_comment = st.text_area(
                "Commentaires / constats d'audit",
                value=row["Commentaires"],
                key=f"comment_{row['ID']}",
            )

            new_action = st.text_area(
                "Action à réaliser",
                value=row["Action"],
                key=f"action_{row['ID']}",
            )

            if st.button(
                "Enregistrer",
                key=f"save_{row['ID']}"
            ):

                st.session_state.df.loc[
                    index, "Statut"
                ] = new_status

                st.session_state.df.loc[
                    index, "Responsable"
                ] = new_owner

                st.session_state.df.loc[
                    index, "Référence_preuve"
                ] = new_evidence

                st.session_state.df.loc[
                    index, "Commentaires"
                ] = new_comment

                st.session_state.df.loc[
                    index, "Action"
                ] = new_action

                st.success(
                    f"{row['ID']} enregistré."
                )

# ============================================================
# PREUVES
# ============================================================

elif page == "Preuves":

    st.title("Gestion des preuves")

    st.info(
        "Cette version référence les documents. "
        "La gestion documentaire physique/électronique "
        "peut être intégrée ultérieurement."
    )

    preuves = df[
        df["Référence_preuve"].fillna("").astype(str).str.strip() != ""
    ].copy()

    if preuves.empty:
        st.warning(
            "Aucune référence de preuve renseignée."
        )
    else:
        st.dataframe(
            preuves[
                [
                    "ID",
                    "Domaine",
                    "Exigence",
                    "Référence_preuve",
                    "Responsable",
                    "Statut",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Exigences sans preuve référencée")

    sans_preuve = df[
        df["Référence_preuve"].fillna("").astype(str).str.strip() == ""
    ]

    st.dataframe(
        sans_preuve[
            [
                "ID",
                "Domaine",
                "Critère",
                "Statut",
                "Responsable",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# ACTIONS
# ============================================================

elif page == "Actions":

    st.title("Plan d'actions")

    actions = df[
        df["Action"].fillna("").astype(str).str.strip() != ""
    ].copy()

    if actions.empty:
        st.info(
            "Aucune action enregistrée."
        )
    else:

        st.dataframe(
            actions[
                [
                    "ID",
                    "Domaine",
                    "Priorité",
                    "Responsable",
                    "Statut",
                    "Action",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Actions prioritaires")

    prioritaires = df[
        (
            df["Priorité"].isin(
                ["Élevée", "Critique"]
            )
        )
        &
        (
            df["Statut"].isin(
                [
                    "Non conforme",
                    "Partiellement conforme",
                    "À vérifier",
                ]
            )
        )
    ]

    st.dataframe(
        prioritaires[
            [
                "ID",
                "Domaine",
                "Priorité",
                "Responsable",
                "Statut",
                "Action",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# REFERENTIEL
# ============================================================

elif page == "Référentiel":

    st.title("Gestion du référentiel")

    st.write(
        "Importez ici le fichier Excel contenant "
        "le référentiel HAS structuré."
    )

    fichier = st.file_uploader(
        "Importer le référentiel Excel",
        type=["xlsx", "xls"],
    )

    if fichier:

        try:
            imported = pd.read_excel(fichier)

            colonnes_requises = [
                "ID",
                "Domaine",
                "Critère",
                "Exigence",
                "Référence_HAS",
                "Référence_Charte",
                "Preuves_attendues",
            ]

            missing = [
                c for c in colonnes_requises
                if c not in imported.columns
            ]

            if missing:

                st.error(
                    "Colonnes manquantes : "
                    + ", ".join(missing)
                )

            else:

                # Ajouter les colonnes de suivi si absentes
                valeurs_defaut = {
                    "Responsable": "",
                    "Statut": "À vérifier",
                    "Priorité": "Moyenne",
                    "Commentaires": "",
                    "Référence_preuve": "",
                    "Action": "",
                }

                for column, value in valeurs_defaut.items():

                    if column not in imported.columns:
                        imported[column] = value

                st.session_state.df = imported

                st.success(
                    f"{len(imported)} exigences importées."
                )

                st.dataframe(
                    imported,
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as e:

            st.error(
                f"Erreur lors de l'import : {e}"
            )

# ============================================================
# EXPORTS
# ============================================================

elif page == "Exports":

    st.title("Exports")

    st.subheader("Export Excel")

    st.write(
        "Le fichier contient la checklist complète "
        "et une feuille de synthèse."
    )

    excel_data = export_excel(
        st.session_state.df
    )

    st.download_button(
        label="Télécharger la checklist Excel",
        data=excel_data,
        file_name="checklist_certification_HAS.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

    st.divider()

    st.subheader("Résumé")

    kpi = calculer_kpi(
        st.session_state.df
    )

    resume = pd.DataFrame(
        {
            "Indicateur": [
                "Nombre total d'exigences",
                "Conformes",
                "Partiellement conformes",
                "Non conformes",
                "À vérifier",
                "Taux de conformité",
            ],
            "Valeur": [
                kpi["total"],
                kpi["conforme"],
                kpi["partiel"],
                kpi["non_conforme"],
                kpi["a_verifier"],
                f"{kpi['taux']} %",
            ],
        }
    )

    st.table(resume)
