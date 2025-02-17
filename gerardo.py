import pandas as pd
import os
import mysql.connector
import unicodedata
import re


def remove_tildes(text):
    """Removes the accents of each vowel in a text but preserves the 'ñ'.

    :param str text: The text with vowels with accents.

    :return str: The text without the accents.
    """
    result = []
    for char in text:
        # Preserve 'ñ' and 'Ñ'
        if char in {'ñ', 'Ñ'}:
            result.append(char)
        else:
            # Normalize and remove accents from other characters
            decomposed = unicodedata.normalize('NFD', char)
            filtered = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn')
            result.append(filtered)
    return ''.join(result)


def name_for_email(names):
    output = names[0].lower()
    for i in range(1, len(names)):
        output += names[i][0].lower()
    return output


def format_name(name):
    return remove_tildes(name).capitalize()

def decompose_fullname(fullname):
    fullname_parts = fullname.split()[::-1]
    half = len(fullname_parts) // 2
    # First name part
    name = fullname_parts[:half][::-1]
    name = tuple(map(format_name, name))

    # Last name part
    last_name = fullname_parts[half:][::-1]
    last_name = tuple(map(format_name, last_name))

    email = f"{name[0].lower()}.{name_for_email(last_name)}@iegerardovalencia.edu.co"
    return ' '.join(name), ' '.join(last_name), email


df = pd.read_csv('users.csv')
# df.dropna(axis=1, inplace=True, how='all')
print(df.columns)

# Access environment variables
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# Connect to MySQL
db_connection = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)
# Create a cursor object to execute the query
cursor = db_connection.cursor()

# Execute the query
cursor.execute("SELECT Cod_Matricula, Nombre_alumno  FROM Estudiante2025")

# Fetch all rows from the query result
rows = cursor.fetchall()

# Get column names from the cursor description
columns = [i[0] for i in cursor.description]

# Create a DataFrame
df = pd.DataFrame(rows, columns=columns)

# Close the cursor and connection
cursor.close()
db_connection.close()
# Apply the decompose_fullname function to the 'Nombre_alumno' column
df[['Name', 'Last_Name', 'Email']] = df['Nombre_alumno'].apply(lambda x: pd.Series(decompose_fullname(x)))

print(df[['Last_Name', 'Email']])
