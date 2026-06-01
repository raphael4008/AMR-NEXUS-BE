import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w') as f:
        f.write(content)

base_dir = '/home/bantu/Documents/amr-nexus-backend/backend/tests/'

replace_in_file(os.path.join(base_dir, 'test_models.py'), [
    ('"result_value": "Resistant"', '"result_value": "R"'),
    ('sector="animal"', 'sector="ANIMAL"'),
])

replace_in_file(os.path.join(base_dir, 'test_api.py'), [
    ('"result_value": "Resistant"', '"result_value": "R"'),
])

replace_in_file(os.path.join(base_dir, 'conftest.py'), [
    ('"result_value": "Resistant"', '"result_value": "R"'),
    ('"result_value": "Sensitive"', '"result_value": "S"'),
    ('"result_value": "Intermediate"', '"result_value": "I"'),
    ('"sector": "environment"', '"sector": "ENVIRONMENT"'),
    ('"sector": "human"', '"sector": "HUMAN"'),
    ('"sector": "animal"', '"sector": "ANIMAL"'),
])

print("Tests updated.")
