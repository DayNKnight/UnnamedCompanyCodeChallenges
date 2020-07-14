import pandas
import re

# Phone regex from https://www.regextester.com/17
phoneFormat = re.compile("^(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$")

def addUser(name,age,phone,cur):
    if phone == None or phone == '':
        cur.execute(
            """
            INSERT INTO people(person_name, person_age)
            VALUES (%s,%s)
            """,(name,age))
    else:
        cur.execute(
            """
            INSERT INTO people(person_name, person_age,person_phone)
            VALUES (%s,%s,%s)
            """,(name,age,phone))

def removeUser(name,age,cur,conn):
    cur.execute("SELECT COUNT(*) FROM people WHERE person_name = %s AND person_age = %s;", (name, age))
    num = cur.fetchone()[0]

    # If there is more than one person with the same name and age, we need to get the person_id from the user
    if num > 1:
        print("There seems to be more than one person by that name and age. Here is the list: ")
        data_frame = pandas.read_sql("SELECT * FROM people WHERE person_name = \'{s0}\' AND person_age = \'{s1}\';".format(s0=name,s1=age), conn)
        print(data_frame.to_string(index=False))
        _id = int(input("\n\nPlease input the person_id that you would like to remove (Does not support multiple people): ").strip())
        cur.execute(
            """
            DELETE FROM people WHERE person_id = %s;
            """,(_id,)
        )
    else:
        cur.execute(
            """
            DELETE FROM people
            WHERE person_name = %s AND person_age = %s;
            """,(name,age))

# These two edit functions allow dynamic psql queries and updates to be made
def editWithID(n,a,cur,cn,ca,cp,id):
    prefix = "UPDATE people SET"
    postfix = f"WHERE person_id = {id};"
    columns = []
    # Create the variables for the SET command
    if cn != None:
        columns.append(f"person_name = '{cn}'")
    if ca != None:
        columns.append(f"person_age = '{ca}'")
    if cp != None:
        columns.append(f"person_phone = '{cp}'")
    
    query = " ".join([prefix,f"{', '.join(columns)}", postfix])
    cur.execute(query)

def editWithoutID(n,a,cur,cn,ca,cp):

    prefix = "UPDATE people SET"
    middle = f"WHERE"
    columns = []
    whereSet = [f"person_name = '{n}'",f"person_age = '{a}'"]

    if cn != None:
        columns.append(f"person_name = '{cn}'")
    if ca != None:
        columns.append(f"person_age = '{ca}'")
    if cp != None:
        columns.append(f"person_phone = '{cp}'")  

    query = " ".join([prefix,f"{', '.join(columns)}",middle,f"{' AND '.join(whereSet)}",";"]) 
    print(query)
    input()
    cur.execute(query)

def editUser(name,age,cur,conn):
    # Make sure that the user exists that we are trying to edit
    cur.execute("SELECT COUNT(*) FROM people WHERE person_name = %s AND person_age = %s;", (name, age))
    num = cur.fetchone()[0]
    # If there are no people in the database that match, tell the user and then wait for them to acknowledge
    if (num == 0):
        print(f"User {name} with age {age} not found. Press enter to continue.")
        input()
    # If there is more than one person with the same name and age, we need to get the person_id from the user
    elif num > 1:
        print("There seems to be more than one person by that name and age. Here is the list: ")
        # Print the list of people that match the name and age of the person
        data_frame = pandas.read_sql("SELECT * FROM people WHERE person_name = \'{s0}\' AND person_age = \'{s1}\';".format(s0=name,s1=age), conn)
        print(data_frame.to_string(index=False))
        # Use the person_id as the identifier, as it is easier for the user to type and it is a PRIMARY KEY in the database, so it is unique
        # Get the new inputs from the user
        _id = input("\n\nPlease input the person_id that you would like to edit: ").strip()
        changed_name = input("What is the new name? (Leave blank for no change) : ")
        changed_age = input("What would you like to change the age to? (Leave blank for no change): ")
        changed_number = input("What would you like to change the phone number to? (Leave blank for no change): ")

        # Change all empty strings to None types, as I find it easier to type for later on
        if changed_name == '':
            changed_name = None
        if changed_age == '':
            changed_age = None
        if changed_number == '':
            changed_number = None

        # If there are no changes, then we dont have to execute a command, so return without doing anything
        if (changed_name == None and changed_age == None and changed_number == None):
            print("No changes detected, returning.")
            return
        
        editWithID(name,age,cur,changed_name,changed_age,changed_number,_id)

    else:  
        # Get the new inputs from the user     
        changed_name = input("What is the new name? (Leave blank for no change) : ")
        changed_age = input("What would you like to change the age to? (Leave blank for no change): ")
        changed_number = input("What would you like to change the phone number to? (Leave blank for no change): ")
        # Change all the strings to None types
        if changed_name == '':
            changed_name = None
        if changed_age == '':
            changed_age = None
        if changed_number == '':
            changed_number = None

        # If there are no changes, then we dont have to execute a command, so return without doing anything
        if (changed_name == None and changed_age == None and changed_number == None):
            print("No changes detected, returning.")

        editWithoutID(name,age,cur,changed_name,changed_age,changed_number)

def userCommand(name,age,phone,firstUse,cur,conn):
    # The firstUse command is so that, if the command line inputs were used in the same run of the program, 
        # we assume that the user will want to use new inputs, so we need to get those new inputs.
    ans = input("Would you like to add, remove, or edit the user? [a,r,e] \n (enter 'back' to go back to the main selection screen) \n >>> ")
    while True:
        if ans.strip() == "a":
            # Check if the command line inputs were used
            if firstUse:
                # Check the phone number to make sure that it is a valid phone number format
                if phone != None:
                    try:
                        phone = phoneFormat.search(phone).group(0)
                    except Exception as e:
                        print(f"Error {e}")
                        print(f"'{phone}' is not a valid phone number. Please check and make sure it has the regular delimiters like '()-'.\n Press enter to acknowledge and exit")
                        input()
                        exit()
                addUser(name,age,phone,cur)
                firstUse = False
            else:
                #If they were used, then get the new inputs
                print("It seems like this may be a repetitive call, so updated information must be obtained.")
                name = input("Please input the individuals name: ").strip()
                age = input("Please input the individuals age: ").strip()
                phone = input("Please input the individuals phone number (hit enter for blank): ").strip()
                if phone != '':
                    try:
                        phone = phoneFormat.search(phone).group(0)
                    except Exception as e:
                        print(f"Error {e}")
                        print(f"'{phone}' is not a valid phone number. Please check and make sure it is and try again.\n Press enter to continue")
                        input()
                        exit()

                addUser(name,age,phone,cur)
            return True
        elif ans.strip() == "r":
            if firstUse:
                # Not passing in phone number, as phone number should not be a deciding factor for removal because it is optional
                removeUser(name,age,cur,conn)
                firstUse = False
            else:
                print("It seems like this may be a repetitive call, so updated information must be obtained.")
                name = input("Please input the individuals name: ").strip()
                age = input("Please input the individuals age: ").strip()
                removeUser(name,age,cur,conn)
            
            return True
        elif ans.strip() == "e":
            if firstUse:
                # Not passing in phone number, as phone number should not be a deciding factor for removal because it is optional
                editUser(name,age,cur,conn)
                firstUse = False
            else:
                print("It seems like this may be a repetitive call, so updated information must be obtained.")
                name = input("Please input the individuals current name in the database: ").strip()
                age = input("Please input the individuals current age in the database: ").strip()
                editUser(name,age,cur,conn)
            return True
        elif ans.strip() == 'back':
            # If this is the first user command supplied in the program run, then assume that the person
            # person running the CLI wanted to do a different command, so we can re-use the supplied name
            # age, and phone for a future add, remove, or edit. This assumes that the supplied arguments 
            # are new and not re-used when running the program
            if firstUse:
                return False
            else:
                return True
        else:
            print("Not a valid command, please try again")
            ans = input("Would you like to add, remove, or edit the user? [a,r,e] \n (enter 'back' to go back to the main selection screen) \n >>> ")
