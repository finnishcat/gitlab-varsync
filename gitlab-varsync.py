import gitlab
import pandas as pd
import os
import argparse
from dotenv import load_dotenv

# === CARICA .env ===
load_dotenv()

# === CONFIGURAZIONE ===
GITLAB_URL = os.getenv('GITLAB_URL')
PRIVATE_TOKEN = os.getenv('GITLAB_PRIVATE_TOKEN')

if not GITLAB_URL or not PRIVATE_TOKEN:
    print("❌ Variabili d'ambiente GITLAB_URL o GITLAB_PRIVATE_TOKEN mancanti nel file .env.")
    exit(1)

# Connessione GitLab
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)
gl.auth()


# === FUNZIONI ===

def export_variables_all_groups(keyword=None):
    print(f"📤 Esportazione variabili da GitLab (filtro: {keyword})...")
    data = []
    groups = gl.groups.list(all=True)

    for group in groups:
        try:
            projects = group.projects.list(include_subgroups=True, all=True)
            for proj in projects:
                project = gl.projects.get(proj.id)
                if keyword and keyword.lower() not in project.name.lower():
                    continue
                variables = project.variables.list()
                for var in variables:
                    data.append({
                        'project_id': project.id,
                        'project_name': project.name,
                        'project_url': project.web_url,
                        'group': group.full_path,
                        'variable_key': var.key,
                        'variable_value': var.value,
                        'protected': var.protected,
                        'masked': var.masked,
                        'environment_scope': var.environment_scope
                    })
        except Exception as e:
            print(f"⚠️ Errore nel gruppo {group.full_path}: {e}")

    df = pd.DataFrame(data)
    df.to_csv("gitlab_variables_all_groups.csv", index=False)
    df.to_excel("gitlab_variables_all_groups.xlsx", index=False)
    print("✅ Variabili esportate in gitlab_variables_all_groups.csv e gitlab_variables_all_groups.xlsx")


def write_new_variables(keyword=None, file_path=None):
    file_to_use = file_path or "gitlab_variables_all_groups.xlsx"
    if not os.path.exists(file_to_use):
        print(f"❌ File {file_to_use} non trovato. Avvia prima `read` o specifica un file con `-f`.")
        return

    print(f"➕ Creazione nuove variabili su GitLab (filtro: {keyword}, file: {file_to_use})...")
    df = pd.read_excel(file_to_use)

    for _, row in df.iterrows():
        try:
            project = gl.projects.get(row['project_id'])
        except gitlab.exceptions.GitlabGetError:
            print(f"❌ Progetto non trovato: ID {row['project_id']}")
            continue

        if keyword and keyword.lower() not in project.name.lower():
            continue

        existing_vars = project.variables.list(all=True)
        existing_keys = {(v.key, v.environment_scope or '*') for v in existing_vars}

        key = row['variable_key']
        scope = row['environment_scope'] or '*'

        if (key, scope) in existing_keys:
            print(f"🔁 Già presente: {key} ({scope}) su {project.name}")
            continue

        try:
            value = str(row['variable_value']) if pd.notna(row['variable_value']) else ""
            project.variables.create({
                'key': key,
                'value': value,
                'protected': bool(row['protected']),
                'masked': bool(row['masked']),
                'environment_scope': scope
            })
            print(f"➕ Creato: {key} ({scope}) su {project.name}")
        except Exception as e:
            print(f"⚠️ Attenzione: variabile {key} non definita in {project.name}: {e}")


def update_existing_variables(keyword=None, file_path=None):
    file_to_use = file_path or "gitlab_variables_all_groups.xlsx"
    if not os.path.exists(file_to_use):
        print(f"❌ File {file_to_use} non trovato. Avvia prima `read` o specifica un file con `-f`.")
        return

    print(f"🔄 Aggiornamento variabili esistenti (filtro: {keyword}, file: {file_to_use})...")
    df = pd.read_excel(file_to_use)

    for _, row in df.iterrows():
        try:
            project = gl.projects.get(row['project_id'])
        except gitlab.exceptions.GitlabGetError:
            print(f"❌ Progetto non trovato: ID {row['project_id']}")
            continue

        if keyword and keyword.lower() not in project.name.lower():
            continue

        key = row['variable_key']
        scope = row['environment_scope'] or '*'

        # Cerca variabile esistente
        variables = project.variables.list(all=True)
        var = next((v for v in variables if v.key == key and (v.environment_scope or '*') == scope), None)

        if var is None:
            print(f"⚠️ Variabile {key} ({scope}) non trovata in {project.name}, ignorata.")
            continue

        needs_update = (
            var.value != str(row['variable_value']) or
            var.protected != bool(row['protected']) or
            var.masked != bool(row['masked'])
        )
        scope_changed = (var.environment_scope or '*') != scope

        try:
            if needs_update and not scope_changed:
                var.value = str(row['variable_value'])
                var.protected = bool(row['protected'])
                var.masked = bool(row['masked'])
                var.save()
                print(f"📝 Aggiornato: {key} ({scope}) su {project.name}")
            elif scope_changed:
                var.delete()
                project.variables.create({
                    'key': key,
                    'value': str(row['variable_value']),
                    'protected': bool(row['protected']),
                    'masked': bool(row['masked']),
                    'environment_scope': row['environment_scope']
                })
                print(f"📝 Scope cambiato, ricreata: {key} ({scope}) su {project.name}")
            else:
                print(f"✅ Nessuna modifica: {key} ({scope}) su {project.name}")
        except Exception as e:
            print(f"❌ Errore durante aggiornamento {key} in {project.name}: {e}")


def search_variable(key_to_search):
    print(f"🔍 Ricerca variabile '{key_to_search}' in tutti i progetti GitLab...")
    data = []
    groups = gl.groups.list(all=True)

    for group in groups:
        try:
            projects = group.projects.list(include_subgroups=True, all=True)
            for proj in projects:
                project = gl.projects.get(proj.id)
                try:
                    variables = project.variables.list()
                    match = next((v for v in variables if v.key == key_to_search), None)
                    if match:
                        data.append({
                            'project_id': project.id,
                            'project_name': project.name,
                            'project_url': project.web_url,
                            'group': group.full_path,
                            'variable_key': match.key,
                            'variable_value': match.value,
                            'protected': match.protected,
                            'masked': match.masked,
                            'environment_scope': match.environment_scope
                        })
                    else:
                        data.append({
                            'project_id': project.id,
                            'project_name': project.name,
                            'project_url': project.web_url,
                            'group': group.full_path,
                            'variable_key': key_to_search,
                            'variable_value': "MISSING",
                            'protected': "",
                            'masked': "",
                            'environment_scope': ""
                        })
                except Exception as e:
                    print(f"⚠️ Errore nella lettura variabili di {project.name}: {e}")
        except Exception as e:
            print(f"⚠️ Errore nel gruppo {group.full_path}: {e}")

    df = pd.DataFrame(data)
    filename = f"{key_to_search}.xlsx"
    df.to_excel(filename, index=False)
    print(f"✅ Risultato ricerca salvato in {filename}")


# === ENTRY POINT ===

def main():
    parser = argparse.ArgumentParser(description="Gestione variabili GitLab via Excel")
    parser.add_argument("command", choices=["read", "write", "update", "search"], help="Comando da eseguire")
    parser.add_argument("filter", nargs='?', default=None, help="(Opzionale) filtro per nome progetto o variabile da cercare")
    parser.add_argument("-f", "--file", help="(Opzionale) file XLSX da usare con write/update")

    args = parser.parse_args()

    if args.command == "read":
        export_variables_all_groups(keyword=args.filter)
    elif args.command == "write":
        write_new_variables(keyword=args.filter, file_path=args.file)
    elif args.command == "update":
        update_existing_variables(keyword=args.filter, file_path=args.file)
    elif args.command == "search":
        if not args.filter:
            print("❌ Devi specificare una variabile da cercare, es: `search SONAR_TOKEN`")
            return
        search_variable(args.filter)


if __name__ == '__main__':
    main()
