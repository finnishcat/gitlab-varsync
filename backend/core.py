import gitlab
import pandas as pd
import os
import argparse
from dotenv import load_dotenv

# === LOAD .env ===
load_dotenv()

# === Configuration ===
GITLAB_URL = os.getenv('GITLAB_URL')
PRIVATE_TOKEN = os.getenv('GITLAB_PRIVATE_TOKEN')

if not GITLAB_URL or not PRIVATE_TOKEN:
    print("❌ Missing environment variables GITLAB_URL or GITLAB_PRIVATE_TOKEN in the .env file.")
    exit(1)

# Connessione GitLab
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)
gl.auth()


# === FUNZIONI ===

def export_variables_all_groups(keyword=None):
    print(f"📤 Exporting variables from GitLab (Filter: {keyword})...")
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
            print(f"⚠️ Error in group {group.full_path}: {e}")

    df = pd.DataFrame(data)
    df.to_excel("gitlab_variables_all_groups.xlsx", index=False)
    print("✅ Variables exported in gitlab_variables_all_groups.xlsx")


def write_new_variables(keyword=None, file_path=None):
    file_to_use = file_path or "gitlab_variables_all_groups.xlsx"
    if not os.path.exists(file_to_use):
        print(f"❌ File {file_to_use} not found. First run `read` or specify a file with `-f`.")
        return

    print(f"➕ Creating new variables on GitLab with filter {keyword}, file {file_to_use}...")
    df = pd.read_excel(file_to_use)

    for _, row in df.iterrows():
        try:
            project = gl.projects.get(row['project_id'])
        except gitlab.exceptions.GitlabGetError:
            print(f"❌ Project not found with: ID {row['project_id']}")
            continue

        if keyword and keyword.lower() not in project.name.lower():
            continue

        existing_vars = project.variables.list(all=True)
        existing_keys = {(v.key, v.environment_scope or '*') for v in existing_vars}

        key = row['variable_key']
        scope = row['environment_scope'] or '*'

        if (key, scope) in existing_keys:
            print(f"🔁 Already exists: {key} ({scope}) su {project.name}")
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
            print(f"➕ Created: {key} ({scope}) su {project.name}")
        except Exception as e:
            print(f"⚠️ Attention: Variable {key} not defined in {project.name}: {e}")


def update_existing_variables(keyword=None, file_path=None):
    file_to_use = file_path or "gitlab_variables_all_groups.xlsx"
    if not os.path.exists(file_to_use):
        print(f"❌ File {file_to_use} not found. First run `read` or specify a file with `-f`.")
        return

    print(f"🔄 Updating of existing variables in all groups (filter: {keyword}, file: {file_to_use})...")
    df = pd.read_excel(file_to_use)

    for _, row in df.iterrows():
        try:
            project = gl.projects.get(row['project_id'])
        except gitlab.exceptions.GitlabGetError:
            print(f"❌ Project not found with: ID {row['project_id']}")
            continue

        if keyword and keyword.lower() not in project.name.lower():
            continue

        key = row['variable_key']
        scope = row['environment_scope'] or '*'

        # Cerca variabile esistente
        variables = project.variables.list(all=True)
        var = next((v for v in variables if v.key == key and (v.environment_scope or '*') == scope), None)

        if var is None:
            print(f"⚠️ Variabile {key} ({scope}) not found in {project.name}, ignored.")
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
                print(f"📝 Scope changed, recreated: {key} ({scope}) su {project.name}")
            else:
                print(f"✅ No change: {key} ({scope}) on {project.name}")
        except Exception as e:
            print(f"❌ Error while updating variable  {key} in {project.name}: {e}")


def search_variable(key_to_search):
    print(f"🔍 Searching for variable '{key_to_search}' on al GitLab projects...")
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
                    print(f"⚠️ Error reading variables of {project.name}: {e}")
        except Exception as e:
            print(f"⚠️ Error in the group {group.full_path}: {e}")

    df = pd.DataFrame(data)
    filename = f"{key_to_search}.xlsx"
    df.to_excel(filename, index=False)
    print(f"✅ Search result saved in {filename}")


# === ENTRY POINT ===

def main():
    parser = argparse.ArgumentParser(description="GitLab variable management via Excel")
    parser.add_argument("command", choices=["read", "write", "update", "search"], help="Command to run")
    parser.add_argument("filter", nargs='?', default=None, help="(Optional) filter by project name or variable to search")
    parser.add_argument("-f", "--file", help="(Optional) XLSX file for use with write / update")

    args = parser.parse_args()

    if args.command == "read":
        export_variables_all_groups(keyword=args.filter)
    elif args.command == "write":
        write_new_variables(keyword=args.filter, file_path=args.file)
    elif args.command == "update":
        update_existing_variables(keyword=args.filter, file_path=args.file)
    elif args.command == "search":
        if not args.filter:
            print("❌ You must specify a variable to search for, e.g. `search SONAR_TOKEN`")
            return
        search_variable(args.filter)


if __name__ == '__main__':
    main()
