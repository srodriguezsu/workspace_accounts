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


def remove_tildes_and_n(text):
    """Removes the accents and 'ñ'.

    :param str text: The text with vowels with accents.

    :return str: The text without the accents.
    """
    result = []
    for char in text:
        # Normalize and remove accents from other characters
        decomposed = unicodedata.normalize('NFD', char)
        filtered = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn')
        result.append(filtered)
    return ''.join(result)


def name_for_email(names):
    """
    Generate a formatted email prefix from a list of names.

    This function takes a list of names (given as a list of strings) and constructs
    an email prefix by concatenating the first name in lowercase and the first
    letter of each subsequent name in lowercase.

    :param tuple names: A list of names to generate the email prefix from.
    :return str: A string representing the generated email prefix.

    :example:
        >>> name_for_email(('Gomez', 'Ruiz'))
        'gomezr'
    """
    output = remove_tildes_and_n(names[0].lower())
    for i in range(1, len(names)):
        output += remove_tildes_and_n(names[i][0].lower())
    return output


def format_name(name):
    """
    Format a name by removing any tildes and capitalizing the first letter.

    This function removes tildes (accent marks) from characters in the name and
    then capitalizes the first letter of the name, returning the formatted version.

    :param str name: The name to be formatted.
    :return str: The formatted name with no tildes and capitalized first letter.

    :example:
        >>> format_name('JOSÉ')
        'Jose'
    """
    return remove_tildes(name).capitalize()


def decompose_fullname(fullname, isReversed, domain):
    """
    Decompose a full name into its components and generate an email address.

    This function splits the full name into first and last name parts, formats
    each name, and creates an email address using the first name and the first
    letter of each last name part. The result is returned as a tuple with
    formatted first name, last name, and email address.

    :param str domain:
    :param bool isReversed:
    :param str fullname: A full name to be decomposed and formatted.
                         The name should be a string with the full name in the format
                         "First Last" or "First Middle Last".
    :return tuple: A tuple containing the formatted first name, last name, and email address.

    :example:
        >>> decompose_fullname('Gomez Ruiz Juan Pablo', True, 'iegerardovalencia.edu.co')
        ('Juan Pablo', 'Gomez Ruiz', 'juan.gomezr@iegerardovalencia.edu.co')
    """
    fullname_parts = fullname.split()
    if isReversed:
        fullname_parts = fullname_parts[::-1]
    half = len(fullname_parts) // 2
    # First name part
    name = fullname_parts[:half]
    name = tuple(map(format_name, name))
    if isReversed:
        name = name[::-1]

    # Last name part
    last_name = fullname_parts[half:]
    last_name = tuple(map(format_name, last_name))
    if isReversed:
        last_name = last_name[::-1]

    email = f"{remove_tildes_and_n(name[0].lower())}.{name_for_email(last_name)}@{domain}"
    return ' '.join(name), ' '.join(last_name), email


def get_initial(full_name):
    full_name_parts = full_name.split()
    full_name_parts = tuple(map(lambda x: remove_tildes_and_n(x)[0], full_name_parts))
    return ''.join(full_name_parts)


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


def process_student_data(connection, domain):
    """
    Fetches student data from the database, decomposes full names into first and last names, generates email addresses,
    and constructs passwords based on the initials and Cod_Matricula.

    :param mySql.Connector connection:
    :param str domain:
    """

    # Create a cursor object to execute the query
    cursor = connection.cursor()

    # Execute the query to fetch Cod_Matricula and Nombre_alumno
    query = "SELECT Cod_Matricula, Nombre_alumno FROM Estudiante2025 WHERE Estado = ''"
    cursor.execute(query)

    # Fetch all rows from the query result
    rows = cursor.fetchall()

    # Get column names from the cursor description
    columns = [i[0] for i in cursor.description]

    # Create a DataFrame from the query result
    df = pd.DataFrame(rows, columns=columns)

    # Close the cursor and connection to the database
    cursor.close()
    connection.close()

    # Apply the decompose_fullname function to the 'Nombre_alumno' column
    df[['First Name [Required]', 'Last Name [Required]', 'Email Address [Required]']] = df['Nombre_alumno'].apply(
        lambda x: pd.Series(decompose_fullname(x, True, domain)))

    # Apply the get_initial function to the 'Nombre_alumno' column to get initials
    df[['initials']] = df['Nombre_alumno'].apply(
        lambda x: pd.Series(get_initial(x)))

    # Construct the password by combining initials and Cod_Matricula
    df['Password [Required]'] = df['initials'] + df['Cod_Matricula'].astype(str).str.replace(r'\D', '', regex=True)

    # Set 'Change Password at Next Sign-In' to True
    df['Change Password at Next Sign-In'] = True

    # Assign default organization unit path
    df['Org Unit Path [Required]'] = '/'

    # Drop unnecessary columns
    df.drop(['Cod_Matricula'], axis=1, inplace=True)
    df.drop(['initials'], axis=1, inplace=True)
    df.drop(['Nombre_alumno'], axis=1, inplace=True)

    # Save the DataFrame to a CSV file
    df.to_csv(f'out/new_students_{domain.split('.')[0]}.csv', index=False)

    return df


def process_teachers_data(connection, domain):
    """
    Fetches student data from the database, decomposes full names into first and last names, generates email addresses,
    and constructs passwords based on the initials and Cod_Matricula.

    :param connection:
    :param domain:
    """

    # Create a cursor object to execute the query
    cursor = connection.cursor()

    # Execute the query to fetch the teachers
    query = "SELECT Cedula, Nombre FROM Docente WHERE Nombre <> ''"
    cursor.execute(query)

    # Fetch all rows from the query result
    rows = cursor.fetchall()

    # Get column names from the cursor description
    columns = [i[0] for i in cursor.description]

    # Create a DataFrame from the query result
    df = pd.DataFrame(rows, columns=columns)

    # Close the cursor and connection to the database
    cursor.close()
    connection.close()

    # Apply the decompose_fullname function to the 'Nombre_alumno' column
    df[['First Name [Required]', 'Last Name [Required]', 'Email Address [Required]']] = df['Nombre'].apply(
        lambda x: pd.Series(decompose_fullname(x, False, domain)))

    # Apply the get_initial function to the 'Nombre_alumno' column to get initials
    df[['initials']] = df['Nombre'].apply(
        lambda x: pd.Series(get_initial(x)))

    # Construct the password by combining initials and Cod_Matricula
    df['Password [Required]'] = df['initials'] + df['Cedula'].astype(str).str.replace(r'\D', '', regex=True)

    # Set 'Change Password at Next Sign-In' to True
    df['Change Password at Next Sign-In'] = True

    # Assign default organization unit path
    df['Org Unit Path [Required]'] = '/'

    # Drop unnecessary columns
    df.drop(['Cedula'], axis=1, inplace=True)
    df.drop(['initials'], axis=1, inplace=True)
    df.drop(['Nombre'], axis=1, inplace=True)

    # Save the DataFrame to a CSV file
    df.to_csv(f'out/new_teachers_{domain.split('.')[0]}.csv', index=False)

    return df


df = process_student_data(db_connection, "lola.edu.co")
