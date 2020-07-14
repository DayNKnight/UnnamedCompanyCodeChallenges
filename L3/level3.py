"""
Author: Zack Knight
Date: 5/5/2020

Raytheon Coding Challenges
Level 3
    1.Create a command-line based user interface program that:
        a.Accepts 3 command line parameters
            i. Required: name and age
            ii.Optional: phone number
        b.Stores the data in a database
        c.Supports the following commands:
            i.User:
                1.Add
                2.Remove
                3.Edit
            ii.Database:
                1.Export
                2.Clear
            iii.Print all users(in table format, sorted by 
                name, with all attributes) to stdout or a file
"""
import psycopg2
import argparse
import os
from configparser import ConfigParser
from os import system, name 
import pandas

from UserCommands import userCommand

# clear function is from https://www.geeksforgeeks.org/clear-screen-python/
def clear(): 
  
    # for windows 
    if os.name == 'nt': 
        os.system('cls') 
    # for mac and linux(here, os.name is 'posix') 
    else: 
        os.system('clear') 
  
def redraw():
    clear()
    print(
        """
______      _        _                      _____ _    _____ 
|  _  \    | |      | |                    /  __ \ |  |_   _|
| | | |__ _| |_ __ _| |__   __ _ ___  ___  | /  \/ |    | |  
| | | / _` | __/ _` | '_ \ / _` / __|/ _ \ | |   | |    | |  
| |/ / (_| | || (_| | |_) | (_| \__ \  __/ | \__/\ |____| |_ 
|___/ \__,_|\__\__,_|_.__/ \__,_|___/\___|  \____|_____|___/ 
        \n\n""")

# Config and connect gotten from https://www.postgresqltutorial.com/postgresql-python/connect/
def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db

# This function will either export or clear the database.
# Export just exports all of the data to a file.
# Clear truncates the table
def databaseCommand(cur,conn):
    ans = input("Would you like to export or clear the database? [e,c]  \n (enter 'back' to go back to the main selection screen) \n >>> ").strip()
    if ans == 'e':
        print("Exporting database to 'export' file in current directory. This overwrites the file if there is one already there.")
        fp = open("export",'w')
        cur.copy_to(fp,'people')
        fp.close()
    elif ans == 'c':
        conf = input("Are you sure you want to clear? This will DELETE **ALL** of the data in the table. [y/n]").strip()
        if conf == 'y':
            cur.execute("TRUNCATE TABLE people;")
            conn.commit()
    elif ans == 'back':
        return
    else:
        badRedraw(ans)
        databaseCommand(cur,conn)

def printDatabase(conn):
    # Parse the user input
    ans = input("Would you like to print to STDOUT, a text file, or a CSV file? [s,f,c]  \n (enter 'back' to go back to the main selection screen) \n >>> ").strip()
    # Default answer.
    # The dataframe is returned from panda's read_sql function. This is the easy way to print the tables instead of trying to parse the data myself.
        # Idea for using pandas came from this: https://stackoverflow.com/questions/43382230/print-a-postgresql-table-to-standard-output-in-python
    if ans == None or ans == '':
        data_frame = pandas.read_sql('SELECT * FROM people ORDER BY person_name', conn)
        print(data_frame.to_string(index=False))
        print("\n")
    # The file and csv are basically the same, but just have different defaults and different pandas calls
    elif ans == 'f' or ans == 'F':
        data_frame = pandas.read_sql('SELECT * FROM people ORDER BY person_name', conn)
        outF = input("What is the file you would like to output to? (out.txt is default)(This will overwrite an existing file): ").strip()
        if outF == None or outF == '':
            outF = 'out.txt'
        with open(outF,'w') as f:
            data_frame.to_string(f,index=False)
        redraw()
    elif ans == 'c' or ans == 'C':
        data_frame = pandas.read_sql('SELECT * FROM people ORDER BY person_name', conn)
        outF = input("What is the file you would like to output to? (out.csv is default)(This will overwrite an existing file): ").strip()
        if outF == None or outF == '':
            outF = 'out.csv'
        with open(outF,'w') as f:
            data_frame.to_csv(f,index=False)
        redraw()
    elif ans == 'back':
        # This is just here so that the badRedraw is not called for 'back'
        return
    else:
        badRedraw(ans)
        printDatabase(conn)
    
def badRedraw(answer):
    redraw()
    print(f"\n\n***ERROR*** '{answer}' is not a valid command, please try again \n")

def connect(name,age,phone):
    """ Connect to the PostgreSQL database server """
    redraw()
    conn = None
    table_name = "people"
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
		
        # create a cursor
        cur = conn.cursor()

        # check to see if table exists
        cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s);", (table_name,))
        # if it doesn't exist, create it
        if not cur.fetchone()[0]:
            print("Table '{s}' not found. Creating it.\n".format(s=table_name))
            # For some reason, sql does not like supplied format from psycopg parser, as it puts single quotes around
            #  the inserted strings
            cur.execute(
                """
                CREATE TABLE people ( 
                    person_id SERIAL PRIMARY KEY,
                    person_name VARCHAR(255) NOT NULL,
                    person_age INTEGER NOT NULL,
                    person_phone VARCHAR(50),
                    time_created TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() at time zone 'utc')
                );
                """)
            conn.commit()
        firstUse = True
        while True:
            answer = input("Would you like to perform user, database, or print commands? [u,d,p] ('q' to quit) \n >>> ")
            if answer.strip() == "u":
                # In an attmept to keep the code from being too long in one file, the user commands are in UserCommands.py
                returned = userCommand(name,age,phone,firstUse,cur,conn)
                # If the return was True, it means that the operation was a success, so we can make firstUse = false and 
                    # Continue to run the program to insert more people
                #If the return was false, that means that the user exited before running a command, so we can re-use the command
                    # line values for later in the run.
                if returned:
                    firstUse = False
                    conn.commit()
                redraw()
            elif answer.strip() == "d":
                databaseCommand(cur,conn)
            elif answer.strip() == "p":
                printDatabase(conn)
            elif answer.strip() == "q":
                print("Now exiting program")
                exit()
            else:
                badRedraw(answer)     
          
	    # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reads in ELF files and outputs the strings")
    parser.add_argument('-n',"--name",dest='name',help="The name of the person", required=True)
    parser.add_argument('-a',"--age",dest='age',help="The age of the person",required=True)
    parser.add_argument('-p',"--phone",dest='phone',default=None)

    args = parser.parse_args()
    connect(args.name,args.age,args.phone)
